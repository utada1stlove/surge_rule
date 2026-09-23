#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

readonly VERSION="1.0.0"
readonly BACKUP_ROOT="/var/backups/snell-users"
readonly USER_CONFIG_DIR="/etc/snell-users"
readonly SNELL_ROOT="/usr/local/libexec/snell"
readonly SYSTEMD_DIR="/etc/systemd/system"

readonly SNELL_V5_VERSION="5.0.1"
readonly SNELL_V5_URL="https://dl.nssurge.com/snell/snell-server-v5.0.1-linux-amd64.zip"
readonly SNELL_V5_SHA256="5b2e221f2c6e29b1db8e47053e1221be29d5627da807cb932b089f514a3609f0"

readonly SNELL_V6_VERSION="6.0.0-rc2"
readonly SNELL_V6_URL="https://dl.nssurge.com/snell/snell-server-v6.0.0rc2-linux-amd64.zip"
readonly SNELL_V6_SHA256="27d8bead8dd7a33f2207b58c7bb6b4c274f67f537b621dcbee7112ffd22e23e6"

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
    COLOR_RESET=$'\033[0m'
    COLOR_BOLD=$'\033[1m'
    COLOR_GREEN=$'\033[32m'
    COLOR_YELLOW=$'\033[33m'
    COLOR_RED=$'\033[31m'
    COLOR_CYAN=$'\033[36m'
else
    COLOR_RESET=""
    COLOR_BOLD=""
    COLOR_GREEN=""
    COLOR_YELLOW=""
    COLOR_RED=""
    COLOR_CYAN=""
fi

log() {
    printf '%s[snell-userctl]%s %s\n' "$COLOR_GREEN" "$COLOR_RESET" "$*"
}

warn() {
    printf '%s[snell-userctl] WARN:%s %s\n' "$COLOR_YELLOW" "$COLOR_RESET" "$*" >&2
}

die() {
    printf '%s[snell-userctl] ERROR:%s %s\n' "$COLOR_RED" "$COLOR_RESET" "$*" >&2
    exit 1
}

refresh_screen() {
    [[ -t 1 ]] || return 0
    if command -v clear >/dev/null 2>&1; then
        clear
    else
        printf '\033[2J\033[H'
    fi
}

pause_menu() {
    [[ -t 0 ]] || return 0
    printf '\n'
    read -r -p "Press Enter to return to the menu..." _
}

run_menu_action() {
    local status=0
    ("$@") || status=$?
    if (( status != 0 )); then
        warn "operation failed"
    fi
    pause_menu
}

prompt_value() {
    local prompt="$1" default_value="${2:-}" value
    if [[ -n "$default_value" ]]; then
        read -r -p "${prompt} [${default_value}]: " value
        printf '%s\n' "${value:-$default_value}"
    else
        read -r -p "${prompt}: " value
        printf '%s\n' "$value"
    fi
}

confirm_action() {
    local prompt="$1" answer
    read -r -p "${prompt} [y/N]: " answer
    [[ "$answer" == "y" || "$answer" == "Y" || "$answer" == "yes" || "$answer" == "YES" ]]
}

need_root() {
    [[ "${EUID:-$(id -u)}" -eq 0 ]] || die "run this script as root"
}

need_command() {
    command -v "$1" >/dev/null 2>&1 || die "missing command: $1"
}

require_amd64() {
    local arch
    arch="$(uname -m)"
    [[ "$arch" == "x86_64" ]] || die "only x86_64/amd64 is validated; found: $arch"
}

random_hex() {
    local bytes="${1:-32}"
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -hex "$bytes"
    else
        od -An -N "$bytes" -tx1 /dev/urandom | tr -d ' \n'
    fi
}

validate_user() {
    [[ "$1" =~ ^[A-Za-z0-9_-]+$ ]] || die "user name must contain only letters, digits, underscore, or hyphen"
}

validate_version() {
    [[ "$1" == "5" || "$1" == "6" ]] || die "version must be 5 or 6"
}

validate_port() {
    [[ "$1" =~ ^[0-9]+$ ]] || die "invalid port: $1"
    (( "$1" >= 1 && "$1" <= 65535 )) || die "port out of range: $1"
}

config_path() {
    printf '%s/%s.conf\n' "$USER_CONFIG_DIR" "$1"
}

unit_name() {
    printf 'snell-v%s@%s.service\n' "$1" "$2"
}

backup_paths() {
    local label="$1"
    shift
    local timestamp destination path
    local -a existing=()

    install -d -m 0700 "$BACKUP_ROOT"
    timestamp="$(date +%Y%m%d-%H%M%S)"
    destination="${BACKUP_ROOT}/${label}-${timestamp}.tar.gz"

    for path in "$@"; do
        if [[ -e "$path" || -L "$path" ]]; then
            existing+=("${path#/}")
        fi
    done

    if [[ "${#existing[@]}" -eq 0 ]]; then
        return 0
    fi

    tar -C / -czf "$destination" "${existing[@]}"
    gzip -t "$destination"
    printf '%s\n' "$destination"
}

binary_path() {
    case "$1" in
        5) printf '%s/v5/%s/snell-server\n' "$SNELL_ROOT" "$SNELL_V5_VERSION" ;;
        6) printf '%s/v6/%s/snell-server\n' "$SNELL_ROOT" "$SNELL_V6_VERSION" ;;
        *) die "unsupported version: $1" ;;
    esac
}

ensure_binary() {
    local version="$1"
    local url expected directory temporary download source actual
    case "$version" in
        5) url="$SNELL_V5_URL"; expected="$SNELL_V5_SHA256" ;;
        6) url="$SNELL_V6_URL"; expected="$SNELL_V6_SHA256" ;;
        *) die "unsupported version: $version" ;;
    esac

    directory="$(dirname "$(binary_path "$version")")"
    if [[ -x "$(binary_path "$version")" ]]; then
        actual="$(sha256sum "$(binary_path "$version")")"
        actual="${actual%% *}"
        if [[ "$actual" == "$expected" ]]; then
            return 0
        fi
    fi

    need_command curl
    need_command unzip
    need_command sha256sum
    install -d -m 0755 "$directory"
    temporary="$(mktemp -d)"
    download="${temporary}/snell-server-v${version}.zip"

    log "downloading Snell version ${version}"
    curl -fL --retry 3 --connect-timeout 10 --max-time 120 -o "$download" "$url"
    unzip -tqq "$download"
    unzip -q "$download" -d "$temporary"
    source="${temporary}/snell-server"
    [[ -f "$source" ]] || die "snell-server missing from archive"
    actual="$(sha256sum "$source")"
    actual="${actual%% *}"
    [[ "$actual" == "$expected" ]] || die "binary checksum mismatch"
    install -m 0755 "$source" "$(binary_path "$version")"
    rm -rf "$temporary"
}

write_templates() {
    local v5_bin v6_bin
    v5_bin="$(binary_path 5)"
    v6_bin="$(binary_path 6)"
    install -d -m 0755 "$SYSTEMD_DIR"

    cat > "${SYSTEMD_DIR}/snell-v5@.service" <<'UNIT_V5'
[Unit]
Description=Snell v5 user %i
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/libexec/snell/v5/5.0.1/snell-server -c /etc/snell-users/%i.conf
Restart=on-failure
RestartSec=3
LimitNOFILE=65536
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
UNIT_V5

    cat > "${SYSTEMD_DIR}/snell-v6@.service" <<'UNIT_V6'
[Unit]
Description=Snell v6 user %i
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/libexec/snell/v6/6.0.0-rc2/snell-server -c /etc/snell-users/%i.conf
Restart=on-failure
RestartSec=3
LimitNOFILE=65536
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
UNIT_V6

    chmod 0644 "${SYSTEMD_DIR}/snell-v5@.service" "${SYSTEMD_DIR}/snell-v6@.service"
    systemctl daemon-reload
}

config_value() {
    local path="$1"
    local key="$2"
    sed -n "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*//p" "$path" | head -n 1
}

active_version() {
    local user="$1" version
    for version in 5 6; do
        if systemctl is-active --quiet "$(unit_name "$version" "$user")"; then
            printf '%s\n' "$version"
            return 0
        fi
    done
    return 1
}

print_node() {
    local user="$1" version="$2" show_secrets="${3:-}" path port psk host display_psk
    path="$(config_path "$user")"
    port="$(config_value "$path" listen | sed -n 's/.*:\([0-9][0-9]*\).*/\1/p')"
    psk="$(config_value "$path" psk)"
    host="${PUBLIC_HOST:-$(hostname -f 2>/dev/null || hostname)}"
    display_psk="<redacted>"
    [[ "$show_secrets" == "--show-secrets" ]] && display_psk="$psk"
    printf '%s = snell, %s, %s, psk=%s, version=%s\n' "$user" "$host" "$port" "$display_psk" "$version"
}

add_user() {
    local user="$1" port="$2" version="$3" psk="${4:-}"
    local path backup=""
    validate_user "$user"
    validate_port "$port"
    validate_version "$version"
    need_root
    require_amd64
    need_command systemctl

    path="$(config_path "$user")"
    [[ ! -e "$path" ]] || die "user already exists: $user"

    ensure_binary "$version"
    write_templates
    install -d -m 0750 "$USER_CONFIG_DIR"

    if [[ -z "$psk" ]]; then
        psk="$(random_hex 32)"
    fi

    umask 077
    cat > "$path" <<CONFIG_TEXT
# managed-version = ${version}
[snell-server]
listen = [::]:${port}
ipv6 = true
psk = ${psk}
CONFIG_TEXT
    chmod 0600 "$path"

    systemctl enable --now "$(unit_name "$version" "$user")"
    log "added ${user}: port ${port}, version ${version}"
    print_node "$user" "$version" --show-secrets
}

remove_user() {
    local user="$1" version path backup=""
    validate_user "$user"
    need_root
    need_command systemctl
    path="$(config_path "$user")"
    [[ -f "$path" ]] || die "user not found: $user"

    for version in 5 6; do
        systemctl disable --now "$(unit_name "$version" "$user")" >/dev/null 2>&1 || true
    done

    backup="$(backup_paths "remove-${user}" "$path" | head -n 1 || true)"
    [[ -n "$backup" ]] && log "backup: $backup"
    rm -f "$path"
    systemctl daemon-reload
    log "removed user: $user"
}

list_users() {
    local path user port version active psk_len
    need_root
    install -d -m 0750 "$USER_CONFIG_DIR"
    for path in "$USER_CONFIG_DIR"/*.conf; do
        [[ -e "$path" ]] || continue
        user="$(basename "$path" .conf)"
        port="$(config_value "$path" listen | sed -n 's/.*:\([0-9][0-9]*\).*/\1/p')"
        version="$(sed -n 's/^# managed-version = //p' "$path" | head -n 1)"
        active="$(active_version "$user" 2>/dev/null || true)"
        psk_len="$(config_value "$path" psk | wc -c)"
        printf '%s\tport=%s\tversion=%s\tactive=%s\tpsk_length=%s\n' "$user" "$port" "${version:-unknown}" "${active:-inactive}" "$((psk_len - 1))"
    done
}

show_user() {
    local user="$1" show_secrets="${2:-}" path version active
    validate_user "$user"
    path="$(config_path "$user")"
    [[ -f "$path" ]] || die "user not found: $user"
    version="$(sed -n 's/^# managed-version = //p' "$path" | head -n 1)"
    active="$(active_version "$user" 2>/dev/null || true)"
    print_node "$user" "${active:-${version:-5}}" "$show_secrets"
}

switch_user() {
    local user="$1" version="$2" path old
    validate_user "$user"
    validate_version "$version"
    need_root
    require_amd64
    path="$(config_path "$user")"
    [[ -f "$path" ]] || die "user not found: $user"
    old="$(active_version "$user" 2>/dev/null || true)"

    if [[ "$old" == "$version" ]]; then
        systemctl restart "$(unit_name "$version" "$user")"
        log "restarted ${user} on version ${version}"
        return 0
    fi

    ensure_binary "$version"
    write_templates
    if [[ -n "$old" ]]; then
        systemctl disable --now "$(unit_name "$old" "$user")"
    fi
    sed -i "s/^# managed-version = .*/# managed-version = ${version}/" "$path"
    systemctl enable --now "$(unit_name "$version" "$user")"
    log "switched ${user} to version ${version}"
}

usage() {
    cat <<'USAGE_TEXT'
Usage:
  snell-userctl.sh list
  snell-userctl.sh add NAME --port PORT [--version 5|6] [--psk PSK] [--host HOST]
  snell-userctl.sh remove NAME
  snell-userctl.sh show NAME [--show-secrets] [--host HOST]
  snell-userctl.sh switch NAME --version 5|6

Examples:
  snell-userctl.sh add alice --port 32003 --version 5
  snell-userctl.sh add bob   --port 32004 --version 5
  snell-userctl.sh switch alice --version 6
  snell-userctl.sh show alice --show-secrets
  snell-userctl.sh remove bob

Notes:
  - Each user gets an independent config, port, PSK, and systemd instance.
  - Config files are stored under /etc/snell-users.
  - v5 and v6 can run at the same time for different users.
  - Do not paste real PSKs into public logs if --psk is used.
USAGE_TEXT
}

menu_add_user() {
    local user port version psk_choice psk="" host
    user="$(prompt_value "User name")"
    [[ -n "$user" ]] || { warn "user name cannot be empty"; return 1; }
    port="$(prompt_value "Port")"
    [[ -n "$port" ]] || { warn "port cannot be empty"; return 1; }
    version="$(prompt_value "Snell version (5 or 6)" "5")"
    host="$(prompt_value "Public host shown in the Surge node (leave blank for hostname)")"
    read -r -p "Custom PSK (leave blank to generate one): " psk_choice
    psk="$psk_choice"
    [[ -n "$host" ]] && PUBLIC_HOST="$host"
    add_user "$user" "$port" "$version" "$psk"
}

menu_show_user() {
    local user
    user="$(prompt_value "User name")"
    [[ -n "$user" ]] || { warn "user name cannot be empty"; return 1; }
    show_user "$user" --show-secrets
}

menu_remove_user() {
    local user
    user="$(prompt_value "User name")"
    [[ -n "$user" ]] || { warn "user name cannot be empty"; return 1; }
    confirm_action "Remove user ${user}?" || return 0
    remove_user "$user"
}

menu_switch_user() {
    local user version
    user="$(prompt_value "User name")"
    [[ -n "$user" ]] || { warn "user name cannot be empty"; return 1; }
    version="$(prompt_value "Switch to Snell version (5 or 6)")"
    [[ -n "$version" ]] || { warn "version cannot be empty"; return 1; }
    switch_user "$user" "$version"
}

menu() {
    local choice
    while true; do
        refresh_screen
        [[ -t 0 ]] || return 0
        printf '%s%sSnell User Manager%s\n\n' "$COLOR_BOLD" "$COLOR_CYAN" "$COLOR_RESET"
        cat <<'MENU_TEXT'
1) list users
2) add user
3) show user and Surge node
4) switch user version
5) remove user
6) return
MENU_TEXT
        read -r -p "choice: " choice
        [[ -n "$choice" ]] || return 0
        case "$choice" in
            1) run_menu_action list_users ;;
            2) run_menu_action menu_add_user ;;
            3) run_menu_action menu_show_user ;;
            4) run_menu_action menu_switch_user ;;
            5) run_menu_action menu_remove_user ;;
            6) return 0 ;;
            *) warn "invalid choice"; pause_menu ;;
        esac
    done
}

main() {
    local command="${1:-menu}"
    [[ "$#" -gt 0 ]] && shift
    local user="" port="" version="5" psk="" host="" show_secrets="" arg

    while [[ "$#" -gt 0 ]]; do
        arg="$1"
        case "$arg" in
            --port) port="${2:-}"; shift 2 ;;
            --version) version="${2:-}"; shift 2 ;;
            --psk) psk="${2:-}"; shift 2 ;;
            --host) host="${2:-}"; shift 2 ;;
            --show-secrets) show_secrets="--show-secrets"; shift ;;
            *)
                if [[ -z "$user" ]]; then
                    user="$arg"
                    shift
                else
                    die "unknown argument: $arg"
                fi
                ;;
        esac
    done

    [[ -n "$host" ]] && PUBLIC_HOST="$host"

    case "$command" in
        add)
            [[ -n "$user" ]] || die "add needs NAME"
            [[ -n "$port" ]] || die "add needs --port"
            add_user "$user" "$port" "$version" "$psk"
            ;;
        remove)
            [[ -n "$user" ]] || die "remove needs NAME"
            remove_user "$user"
            ;;
        list) list_users ;;
        show)
            [[ -n "$user" ]] || die "show needs NAME"
            show_user "$user" "$show_secrets"
            ;;
        switch)
            [[ -n "$user" ]] || die "switch needs NAME"
            switch_user "$user" "$version"
            ;;
        menu) menu ;;
        -h|--help|help) usage ;;
        *) die "unknown command: $command" ;;
    esac
}

main "$@"
