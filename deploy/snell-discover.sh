#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

readonly BACKUP_ROOT="/var/backups/snell-discover"
readonly SYSTEMD_DIR="/etc/systemd/system"
readonly MULTI_USER_WANTS="${SYSTEMD_DIR}/multi-user.target.wants"
readonly USER_CONFIG_DIR="/etc/snell-users"

declare -A UNIT_NAMES=()
declare -A UNIT_PATHS=()
declare -A BIN_PATHS=()
declare -A CONFIG_PATHS=()

log() {
    printf '[snell-discover] %s\n' "$*"
}

warn() {
    printf '[snell-discover] WARN: %s\n' "$*" >&2
}

die() {
    printf '[snell-discover] ERROR: %s\n' "$*" >&2
    exit 1
}

need_root() {
    [[ "${EUID:-$(id -u)}" -eq 0 ]] || die "run this script as root"
}

need_command() {
    command -v "$1" >/dev/null 2>&1 || die "missing command: $1"
}

add_bin() {
    local path="$1"
    [[ -n "$path" && ( -e "$path" || -L "$path" ) ]] || return 0
    BIN_PATHS["$path"]=1
}

add_config() {
    local path="$1"
    [[ -n "$path" && -f "$path" ]] || return 0
    CONFIG_PATHS["$path"]=1
}

unit_is_snell() {
    local unit="$1" text="$2" fragment="$3"
    case "$unit" in
        snell-server.service|snell-v5@*.service|snell-v6@*.service)
            return 0
            ;;
    esac
    local -a lines=()
    mapfile -t lines < <(systemctl show --property=ExecStart --value "$unit" 2>/dev/null || true)
    local line
    for line in "${lines[@]}"; do
        [[ "$line" == *snell-server* ]] && return 0
        case "$unit" in
            snell-v5@*.service|snell-v6@*.service)
                [[ "$line" == *"/etc/snell-users/"* ]] && return 0
                ;;
        esac
    done
    return 1
}

parse_unit_references() {
    local unit="$1" text="$2" fragment="${3:-}" line executable="" argument
    local -a parts=()

    if [[ -n "$fragment" && "$fragment" != /dev/null ]]; then
        add_unit_path "$unit" "$fragment"
    fi
    while IFS= read -r line; do
        [[ "$line" == ExecStart=* ]] || continue
        line="${line#ExecStart=}"
        # systemctl show emits systemd's parsed ExecStart form. This basic
        # parser only collects literal paths; it never executes them.
        read -r -a parts <<< "$line"
        ((${#parts[@]} > 0)) || continue
        executable="${parts[0]}"
        while [[ "$executable" == [-@+!]* ]]; do executable="${executable:1}"; done
        if [[ "$executable" == *snell-server* || "$unit" == snell-* ]]; then
            add_bin "$executable"
        fi
        for argument in "${parts[@]:1}"; do
            case "$argument" in
                /etc/snell-server*.conf|/etc/snell-users/*.conf)
                    [[ "$argument" == *'%i'* ]] || add_config "$argument"
                    ;;
            esac
        done
    done < <(systemctl show --property=ExecStart --value "$unit" 2>/dev/null || true)

    if [[ "$unit" == snell-v5@*.service || "$unit" == snell-v6@*.service ]]; then
        local instance="${unit#*@}"
        instance="${instance%.service}"
        if [[ "$instance" != *'@'* && "$instance" != *'%'* ]]; then
            add_config "${USER_CONFIG_DIR}/${instance}.conf"
        fi
    fi
}

add_unit_path() {
    local unit="$1" path="$2"
    [[ -e "$path" || -L "$path" ]] || return 0
    UNIT_PATHS["$path"]=1
}

discover_units() {
    local unit text fragment dropins dropin resolved_unit
    local -a units=() dropin_paths=()
    mapfile -t units < <(
        {
            systemctl list-unit-files --type=service --all --no-legend --no-pager 2>/dev/null | awk '{print $1}'
            systemctl list-units --type=service --all --no-legend --no-pager 2>/dev/null | awk '{print $1}'
        } | sort -u
    )

    for unit in "${units[@]}"; do
        [[ "$unit" == *.service ]] || continue
        fragment="$(systemctl show --property=FragmentPath --value "$unit" 2>/dev/null || true)"
        text="$(systemctl cat "$unit" 2>/dev/null || true)"
        [[ -n "$text" || -n "$fragment" ]] || continue
        if ! unit_is_snell "$unit" "$text" "$fragment"; then
            continue
        fi

        resolved_unit="$unit"
        if [[ "$unit" == *@*.service && "$unit" != *@.service ]]; then
            resolved_unit="${unit%%@*}@.service"
            fragment="$(systemctl show --property=FragmentPath --value "$resolved_unit" 2>/dev/null || true)"
        fi
        if [[ -n "$fragment" && "$fragment" != /dev/null ]]; then
            case "$unit" in
                *@.service)
                    # A template is a shared unit file, not a running instance.
                    case "$unit" in
                        snell-v5@.service|snell-v6@.service) UNIT_PATHS["$fragment"]=1 ;;
                    esac
                    ;;
                *)
                    UNIT_NAMES["$unit"]=1
                    add_unit_path "$resolved_unit" "$fragment"
                    ;;
            esac
        fi
        case "$unit" in *@.service) ;; *) parse_unit_references "$resolved_unit" "$text" "$fragment" ;; esac
        dropins="$(systemctl show --property=DropInPaths --value "$unit" 2>/dev/null || true)"
        if [[ -n "$dropins" ]]; then
            read -r -a dropin_paths <<< "$dropins"
            for dropin in "${dropin_paths[@]}"; do
                if [[ "$dropin" == *snell* || "$unit" == snell-* ]]; then
                    add_unit_path "$unit" "$dropin"
                fi
            done
        fi
        case "$unit" in *@.service) ;; *)
            while IFS= read -r -d '' dropin; do
                UNIT_PATHS["$dropin"]=1
            done < <(find /etc/systemd/system -type l -name "$unit" -print0 2>/dev/null)
            ;;
        esac
    done
}

discover_bins() {
    local path
    for path in \
        /usr/local/bin/snell-server \
        /usr/bin/snell-server \
        /usr/local/sbin/snell-server \
        /usr/local/libexec/snell/*/*/snell-server; do
        if [[ -L "$path" && -e "$path" ]]; then
            path="$(readlink -f -- "$path")"
        fi
        add_bin "$path"
    done
}

discover_configs() {
    local path
    add_config /etc/snell-server.conf
    if [[ -d "$USER_CONFIG_DIR" ]]; then
        while IFS= read -r -d '' path; do
            add_config "$path"
        done < <(find "$USER_CONFIG_DIR" -maxdepth 1 \( -type f -o -type l \) -name '*.conf' -print0 2>/dev/null)
    fi
    while IFS= read -r -d '' path; do
        add_config "$path"
    done < <(find /etc -maxdepth 3 -type f -name 'snell-server*.conf' -print0 2>/dev/null)
}

binary_version() {
    printf '%s\n' "not-executed"
}

discover_all() {
    need_command systemctl
    UNIT_NAMES=()
    UNIT_PATHS=()
    BIN_PATHS=()
    CONFIG_PATHS=()
    discover_units
    discover_bins
    discover_configs
}

show_discovery() {
    local index=1 unit bin config path active version
    discover_all
    if [[ "${#UNIT_NAMES[@]}" -eq 0 && "${#BIN_PATHS[@]}" -eq 0 && "${#CONFIG_PATHS[@]}" -eq 0 ]]; then
        log "no Snell installation detected"
        return 1
    fi

    printf '\nSnell systemd units:\n'
    for unit in "${!UNIT_NAMES[@]}"; do
        active="$(systemctl is-active "$unit" 2>/dev/null || true)"
        printf '  [%s] unit=%s active=%s\n' "$index" "$unit" "${active:-inactive}"
        index=$((index + 1))
    done
    printf '\nSnell unit files and links:\n'
    for path in "${!UNIT_PATHS[@]}"; do printf '  %s\n' "$path"; done
    printf '\nSnell binaries (not executed):\n'
    for bin in "${!BIN_PATHS[@]}"; do
        version="$(binary_version "$bin")"
        printf '  %s type=%s\n' "$bin" "$version"
    done
    printf '\nSnell config files:\n'
    for config in "${!CONFIG_PATHS[@]}"; do printf '  %s\n' "$config"; done
    printf '\n'
}

backup_selected() {
    local timestamp destination path
    local -a existing=()
    install -d -m 0700 "$BACKUP_ROOT"
    timestamp="$(date +%Y%m%d-%H%M%S)-$$"
    destination="${BACKUP_ROOT}/snell-uninstall-${timestamp}.tar.gz"
    for path in "${!UNIT_PATHS[@]}" "${!BIN_PATHS[@]}" "${!CONFIG_PATHS[@]}"; do
        [[ -e "$path" || -L "$path" ]] && existing+=("${path#/}")
    done
    ((${#existing[@]} > 0)) || die "nothing was selected for backup"
    tar -C / -czf "$destination" "${existing[@]}" || die "failed to create backup archive"
    gzip -t "$destination" || die "backup archive verification failed"
    local entry
    for entry in "${existing[@]}"; do
        tar -tzf "$destination" -- "$entry" >/dev/null || die "backup is missing selected path: /${entry}"
    done
    printf '%s\n' "$destination"
}

remove_selected_path() {
    local path="$1"
    [[ "$path" == /* ]] || die "refusing to remove non-absolute path: $path"
    case "$path" in
        /etc/systemd/system/*|/etc/snell-users/*|/etc/snell-server*.conf|/usr/local/libexec/snell/*/*/snell-server|/usr/local/bin/snell-server|/usr/bin/snell-server|/usr/local/sbin/snell-server|/opt/*/snell-server)
            ;;
        *) die "refusing to remove path outside the Snell allowlist: $path" ;;
    esac
        [[ -L "$path" || -f "$path" ]] || { warn "skipping unexpected file type: $path"; return 0; }
        rm -f -- "$path"
}

show_selected() {
    local unit path
    warn "the following Snell components will be uninstalled:"
    for unit in "${!UNIT_NAMES[@]}"; do printf '  unit: %s\n' "$unit"; done
    for path in "${!UNIT_PATHS[@]}"; do printf '  unit path: %s\n' "$path"; done
    for path in "${!BIN_PATHS[@]}"; do printf '  binary: %s\n' "$path"; done
    for path in "${!CONFIG_PATHS[@]}"; do printf '  config: %s\n' "$path"; done
}

confirm_uninstall() {
    local assume_yes="$1" answer
    if [[ "$assume_yes" == true ]]; then return 0; fi
    [[ -t 0 ]] || die "interactive confirmation requires a terminal; use --yes to confirm explicitly"
    read -r -p "continue? [y/N] " answer
    [[ "$answer" == "y" || "$answer" == "Y" || "$answer" == "yes" || "$answer" == "YES" ]] || die "cancelled"
}

uninstall_all() {
    local purge_config="$1" assume_yes="$2" backup unit path config
    need_root
    discover_all
    if [[ "${#UNIT_NAMES[@]}" -eq 0 && "${#BIN_PATHS[@]}" -eq 0 ]]; then
        die "no Snell systemd unit or binary detected"
    fi

    show_selected
    if [[ "$purge_config" != true ]]; then
        log "configuration files will be preserved"
    fi
    confirm_uninstall "$assume_yes"

    backup="$(backup_selected)"
    log "verified backup: $backup"

    for unit in "${!UNIT_NAMES[@]}"; do
        case "$unit" in
            *@*.service)
                systemctl stop "$unit" || die "failed to stop $unit; no files were removed"
                systemctl disable "$unit" || die "failed to disable $unit; no files were removed"
                ;;
            *)
                systemctl disable --now "$unit" || die "failed to stop/disable $unit; no files were removed"
                ;;
        esac
        if systemctl is-active --quiet "$unit"; then
            die "$unit is still active; no files were removed"
        fi
    done

    for path in "${!UNIT_PATHS[@]}" "${!BIN_PATHS[@]}"; do
        [[ -e "$path" || -L "$path" ]] || continue
        remove_selected_path "$path"
    done
    if [[ "$purge_config" == true ]]; then
        for config in "${!CONFIG_PATHS[@]}"; do
            [[ -e "$config" || -L "$config" ]] || continue
            remove_selected_path "$config"
        done
    fi

    systemctl daemon-reload || die "files removed, but systemd daemon-reload failed; backup: $backup"
    systemctl reset-failed >/dev/null 2>&1 || true
    log "Snell uninstall completed; backup: $backup"
}

usage() {
    cat <<'USAGE_TEXT'
Usage:
  snell-discover.sh discover
  snell-discover.sh uninstall [--yes] [--purge-config]

Commands:
  discover          list likely Snell units, binaries, and configs without executing binaries
  uninstall         display the exact selection, back it up, then remove it
                    --yes           explicitly skip interactive confirmation
                    --purge-config  delete discovered config files after verified backup

Safety:
  - Discovery does not execute binaries found on disk.
  - Only known Snell unit names or units whose ExecStart references snell-server are selected.
  - Every selected unit path, binary, and config is archived and verified before deletion.
  - Config files are preserved unless --purge-config is explicitly used.
USAGE_TEXT
}

main() {
    local command="${1:-}" purge="false" assume_yes="false" arg
    [[ "$#" -gt 0 ]] && shift
    while [[ "$#" -gt 0 ]]; do
        arg="$1"
        case "$arg" in
            --yes) assume_yes="true"; shift ;;
            --purge-config) purge="true"; shift ;;
            *) die "unknown option: $arg" ;;
        esac
    done

    case "$command" in
        discover) show_discovery ;;
        uninstall) uninstall_all "$purge" "$assume_yes" ;;
        -h|--help|help|"") usage ;;
        *) die "unknown command: $command" ;;
    esac
}

main "$@"
