#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

readonly SCRIPT_VERSION="1.0.0"
readonly BACKUP_ROOT="/var/backups/proxy-protocols"

readonly SNELL_ROOT="/usr/local/libexec/snell"
readonly SNELL_USER_CONFIG_DIR="/etc/snell-users"
readonly SYSTEMD_DIR="/etc/systemd/system"
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly SNELL_USERCTL="${SCRIPT_DIR}/snell-userctl.sh"

readonly ANYTLS_USER="anytls"
readonly ANYTLS_BIN="/usr/local/bin/anytls-server"
readonly ANYTLS_CONFIG_DIR="/etc/anytls-native"
readonly ANYTLS_ENV="${ANYTLS_CONFIG_DIR}/env"
readonly ANYTLS_UNIT="/etc/systemd/system/anytls-native.service"

readonly SNELL_V5_VERSION="5.0.1"
readonly SNELL_V5_URL="https://dl.nssurge.com/snell/snell-server-v5.0.1-linux-amd64.zip"
readonly SNELL_V5_BIN_SHA256="5b2e221f2c6e29b1db8e47053e1221be29d5627da807cb932b089f514a3609f0"

readonly SNELL_V6_VERSION="6.0.0-rc2"
readonly SNELL_V6_URL="https://dl.nssurge.com/snell/snell-server-v6.0.0rc2-linux-amd64.zip"
readonly SNELL_V6_BIN_SHA256="27d8bead8dd7a33f2207b58c7bb6b4c274f67f537b621dcbee7112ffd22e23e6"

readonly ANYTLS_VERSION="0.0.13"
readonly ANYTLS_ZIP_URL="https://github.com/anytls/anytls-go/releases/download/v${ANYTLS_VERSION}/anytls_${ANYTLS_VERSION}_linux_amd64.zip"
readonly ANYTLS_ZIP_SHA256="7e80fc099ea54a71110d256dd60648c47c63c70a3c499eb1f6d7aaa4edb7016f"
readonly ANYTLS_SERVER_SHA256="c1a3a52cf3246a51b2cbf427283cde2482fe99b6868588a57786c24324ac44fa"

LOG_PREFIX="proxy-protocol"

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
    printf '%s[%s]%s %s\n' "$COLOR_GREEN" "$LOG_PREFIX" "$COLOR_RESET" "$*"
}

warn() {
    printf '%s[%s] WARN:%s %s\n' "$COLOR_YELLOW" "$LOG_PREFIX" "$COLOR_RESET" "$*" >&2
}

die() {
    printf '%s[%s] ERROR:%s %s\n' "$COLOR_RED" "$LOG_PREFIX" "$COLOR_RESET" "$*" >&2
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

require_systemd() {
    command -v systemctl >/dev/null 2>&1 || die "systemd is required"
}

random_hex() {
    local bytes="${1:-32}"
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -hex "$bytes"
    else
        od -An -N "$bytes" -tx1 /dev/urandom | tr -d ' \n'
    fi
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

download_and_verify() {
    local url="$1"
    local output="$2"
    local expected_sha="$3"

    curl -fL --retry 3 --connect-timeout 10 --max-time 120 -o "$output" "$url"
    printf '%s  %s\n' "$expected_sha" "$output" | sha256sum -c -
}

atomic_install() {
    local source="$1"
    local destination="$2"
    local mode="$3"
    local temporary="${destination}.new.$$"

    install -m "$mode" "$source" "$temporary"
    mv -f "$temporary" "$destination"
}

write_snell_template() {
    local major="$1" version_dir unit
    version_dir="$(snell_version_dir "$major")"
    unit="${SYSTEMD_DIR}/snell-v${major}@.service"
    install -d -m 0755 "$SYSTEMD_DIR"
    cat > "$unit" <<UNIT_SNELL
[Unit]
Description=Snell v${major} user %i
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=${version_dir}/snell-server -c ${SNELL_USER_CONFIG_DIR}/%i.conf
Restart=on-failure
RestartSec=3
LimitNOFILE=65536
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
UNIT_SNELL
    chmod 0644 "$unit"
}

snell_version_dir() {
    case "$1" in
        5) printf '%s/v5/%s\n' "$SNELL_ROOT" "$SNELL_V5_VERSION" ;;
        6) printf '%s/v6/%s\n' "$SNELL_ROOT" "$SNELL_V6_VERSION" ;;
        *) die "unknown Snell major version: $1" ;;
    esac
}

install_snell() {
    local major="$1"
    local url version expected version_dir temporary download binary
    local backup=""

    case "$major" in
        5)
            version="$SNELL_V5_VERSION"
            url="$SNELL_V5_URL"
            expected="$SNELL_V5_BIN_SHA256"
            ;;
        6)
            version="$SNELL_V6_VERSION"
            url="$SNELL_V6_URL"
            expected="$SNELL_V6_BIN_SHA256"
            warn "Snell v6 currently uses the official RC2 package"
            ;;
        *) die "only snell-v5 or snell-v6 are supported" ;;
    esac

    need_root
    require_amd64
    require_systemd
    need_command curl
    need_command unzip
    need_command sha256sum

    version_dir="$(snell_version_dir "$major")"
    install -d -m 0755 "$version_dir"
    temporary="$(mktemp -d)"
    download="${temporary}/snell-server-v${version}.zip"

    log "downloading Snell ${version}"
    curl -fL --retry 3 --connect-timeout 10 --max-time 120 -o "$download" "$url"
    unzip -tqq "$download"
    unzip -q "$download" -d "$temporary"
    binary="${temporary}/snell-server"
    [[ -f "$binary" ]] || die "snell-server is missing from the archive"

    if [[ "$(sha256sum "$binary" | awk '{print $1}')" != "$expected" ]]; then
        die "Snell binary checksum mismatch"
    fi

    if [[ -e "$version_dir" || -e "${SYSTEMD_DIR}/snell-v${major}@.service" ]]; then
        backup="$(backup_paths "snell-before-v${major}" "$version_dir" "${SYSTEMD_DIR}/snell-v${major}@.service" | head -n 1)"
        [[ -n "$backup" ]] && log "backup: $backup"
    fi

    atomic_install "$binary" "${version_dir}/snell-server" 0755
    write_snell_template "$major"
    systemctl daemon-reload

    log "installed Snell ${version} binary and snell-v${major}@.service template"
    log "no default config or service instance was created"
    log "next: use snell-userctl.sh add NAME --port PORT --version ${major}"
    snell_status
    rm -rf "$temporary"
}

snell_binary_state() {
    local major="$1" binary expected actual
    binary="$(snell_version_dir "$major")/snell-server"
    case "$major" in
        5) expected="$SNELL_V5_BIN_SHA256" ;;
        6) expected="$SNELL_V6_BIN_SHA256" ;;
    esac
    if [[ ! -x "$binary" ]]; then
        printf 'not-installed\n'
        return 0
    fi
    actual="$(sha256sum "$binary" | awk '{print $1}')"
    if [[ "$actual" == "$expected" ]]; then
        printf 'installed\n'
    else
        printf 'checksum-mismatch\n'
    fi
}

snell_status() {
    local user_count=0 active_count=0
    if [[ -d "$SNELL_USER_CONFIG_DIR" && -r "$SNELL_USER_CONFIG_DIR" && -x "$SNELL_USER_CONFIG_DIR" ]]; then
        user_count="$(find "$SNELL_USER_CONFIG_DIR" -maxdepth 1 -type f -name '*.conf' 2>/dev/null | wc -l || true)"
    fi
    active_count="$(systemctl list-units 'snell-v[56]@*.service' --state=active --no-legend --no-pager 2>/dev/null | wc -l)"
    printf '%sSnell v5 binary:%s %s\n' "$COLOR_CYAN" "$COLOR_RESET" "$(snell_binary_state 5)"
    printf '%sSnell v6 binary:%s %s\n' "$COLOR_CYAN" "$COLOR_RESET" "$(snell_binary_state 6)"
    printf '%sSnell users:%s %s configured, %s active\n' "$COLOR_CYAN" "$COLOR_RESET" "$user_count" "$active_count"
}

uninstall_snell() {
    local major="$1" purge_config="${2:-false}" version_dir backup unit config

    need_root
    require_systemd
    [[ "$purge_config" == "false" ]] || die "Snell user configs are owned by snell-userctl.sh; remove users there"
    version_dir="$(snell_version_dir "$major")"
    unit="${SYSTEMD_DIR}/snell-v${major}@.service"

    if systemctl list-units "snell-v${major}@*.service" --all --no-legend --no-pager 2>/dev/null | grep -q .; then
        die "Snell v${major} still has systemd instances; remove or switch them with snell-userctl.sh"
    fi
    if [[ -d "$SNELL_USER_CONFIG_DIR" ]]; then
        for config in "$SNELL_USER_CONFIG_DIR"/*.conf; do
            [[ -e "$config" ]] || continue
            if grep -q "^# managed-version = ${major}$" "$config"; then
                die "Snell v${major} is still assigned to user config: $config"
            fi
        done
    fi

    backup="$(backup_paths "snell-uninstall-v${major}" "$unit" "$version_dir" | head -n 1)"
    [[ -n "$backup" ]] && log "backup: $backup"
    rm -f "$unit"
    rm -rf "$version_dir"

    systemctl daemon-reload
    log "uninstalled unused Snell v${major} binary and template"
}

write_anytls_unit() {
    local port="$1"
    cat > "$ANYTLS_UNIT" <<'UNIT_ANYTLS'
[Unit]
Description=Native AnyTLS Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=anytls
Group=anytls
EnvironmentFile=/etc/anytls-native/env
ExecStart=/usr/local/bin/anytls-server -l 0.0.0.0:PORT_PLACEHOLDER -p ${ANYTLS_PASSWORD}
Restart=on-failure
RestartSec=3
LimitNOFILE=65536
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
CapabilityBoundingSet=
AmbientCapabilities=
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

[Install]
WantedBy=multi-user.target
UNIT_ANYTLS
    sed -i "s/PORT_PLACEHOLDER/${port}/" "$ANYTLS_UNIT"
    chmod 0644 "$ANYTLS_UNIT"
}

ensure_anytls_user() {
    if ! getent passwd "$ANYTLS_USER" >/dev/null 2>&1; then
        useradd --system --user-group --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin "$ANYTLS_USER"
    fi
}

ensure_anytls_env() {
    local password="${ANYTLS_PASSWORD:-}"
    install -d -m 0711 -o root -g root "$ANYTLS_CONFIG_DIR"
    if [[ -f "$ANYTLS_ENV" ]]; then
        chmod 0600 "$ANYTLS_ENV"
        return 0
    fi
    if [[ -z "$password" ]]; then
        password="$(random_hex 32)"
    fi
    umask 077
    printf 'ANYTLS_PASSWORD="%s"\n' "$password" > "$ANYTLS_ENV"
    chmod 0600 "$ANYTLS_ENV"
    log "created /etc/anytls-native/env"
}

anytls_password() {
    local value
    value="$(sed -n 's/^ANYTLS_PASSWORD=//p' "$ANYTLS_ENV" | head -n 1)"
    value="${value%\"}"
    value="${value#\"}"
    printf '%s\n' "$value"
}

install_anytls() {
    local port="${1:-${ANYTLS_PORT:-50014}}"
    local temporary download binary actual backup=""

    need_root
    require_amd64
    require_systemd
    need_command curl
    need_command unzip
    need_command sha256sum
    [[ "$port" =~ ^[0-9]+$ ]] || die "invalid AnyTLS port: $port"
    (( port >= 1 && port <= 65535 )) || die "AnyTLS port out of range: $port"

    if [[ -e "$ANYTLS_BIN" || -e "$ANYTLS_UNIT" || -e "$ANYTLS_ENV" ]]; then
        backup="$(backup_paths "anytls-before-install" "$ANYTLS_BIN" "$ANYTLS_UNIT" "$ANYTLS_ENV" | head -n 1 || true)"
        [[ -n "$backup" ]] && log "backup: $backup"
    fi

    temporary="$(mktemp -d)"
    download="${temporary}/anytls.zip"
    log "downloading AnyTLS ${ANYTLS_VERSION}"
    download_and_verify "$ANYTLS_ZIP_URL" "$download" "$ANYTLS_ZIP_SHA256"
    unzip -q "$download" -d "$temporary"
    binary="${temporary}/anytls-server"
    [[ -f "$binary" ]] || die "anytls-server is missing from the archive"
    actual="$(sha256sum "$binary" | awk '{print $1}')"
    [[ "$actual" == "$ANYTLS_SERVER_SHA256" ]] || die "AnyTLS server checksum mismatch"

    ensure_anytls_user
    ensure_anytls_env
    atomic_install "$binary" "$ANYTLS_BIN" 0755
    write_anytls_unit "$port"
    systemctl daemon-reload
    systemctl enable --now anytls-native.service
    systemctl restart anytls-native.service

    log "installed native AnyTLS ${ANYTLS_VERSION} on port ${port}"
    anytls_status "$port"
    anytls_node_line "$port" --show-secrets
    rm -rf "$temporary"
}

anytls_status() {
    local port="${1:-50014}"
    printf 'AnyTLS service: %s\n' "$(systemctl is-active anytls-native.service 2>/dev/null || true)"
    printf 'AnyTLS version: %s\n' "$ANYTLS_VERSION"
    printf 'AnyTLS port: %s\n' "$port"
    printf 'AnyTLS env: %s\n' "$([[ -f "$ANYTLS_ENV" ]] && printf present || printf missing)"
}

uninstall_anytls() {
    local purge="${1:-false}" backup
    backup="$(backup_paths "anytls-uninstall" "$ANYTLS_BIN" "$ANYTLS_UNIT" "$ANYTLS_ENV" | head -n 1 || true)"
    [[ -n "$backup" ]] && log "backup: $backup"

    systemctl disable --now anytls-native.service >/dev/null 2>&1 || true
    rm -f "$ANYTLS_BIN" "$ANYTLS_UNIT"

    if [[ "$purge" == "true" ]]; then
        rm -rf "$ANYTLS_CONFIG_DIR"
        if getent passwd "$ANYTLS_USER" >/dev/null 2>&1; then
            userdel "$ANYTLS_USER" >/dev/null 2>&1 || warn "could not remove user $ANYTLS_USER"
        fi
    fi

    systemctl daemon-reload
    log "uninstalled native AnyTLS"
}

default_host() {
    if [[ -n "${PUBLIC_HOST:-}" ]]; then
        printf '%s\n' "$PUBLIC_HOST"
        return 0
    fi
    hostname -f 2>/dev/null || hostname
}

anytls_node_line() {
    local port="${1:-50014}" show_secrets="${2:-}" host password display_password
    host="$(default_host)"
    password="$(anytls_password)"
    display_password="<redacted>"
    [[ "$show_secrets" == "--show-secrets" ]] && display_password="$password"
    printf 'Surge node: AnyTLS-%s = anytls, %s, %s, password=%s, sni=%s, skip-cert-verify=true, reuse=false\n' "$ANYTLS_VERSION" "$host" "$port" "$display_password" "$host"
}

status_all() {
    local show_secrets="${1:-}"
    require_amd64
    if command -v systemctl >/dev/null 2>&1; then
        printf 'systemd: %s\n' "$(systemctl --version | head -n 1)"
    fi
    snell_status
    anytls_status "${ANYTLS_PORT:-50014}"
    if [[ "$show_secrets" == "--show-secrets" ]]; then
        [[ -f "$ANYTLS_ENV" ]] && anytls_node_line "${ANYTLS_PORT:-50014}" --show-secrets
        [[ -d "$SNELL_USER_CONFIG_DIR" ]] && warn "use snell-userctl.sh show NAME --show-secrets for Snell users"
    fi
}

parse_common_options() {
    ARG_PORT=""
    ARG_PURGE="false"
    ARG_SHOW_SECRETS=""
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            --port)
                [[ "$#" -ge 2 ]] || die "--port needs a value"
                ARG_PORT="$2"
                shift 2
                ;;
            --host)
                [[ "$#" -ge 2 ]] || die "--host needs a value"
                PUBLIC_HOST="$2"
                shift 2
                ;;
            --purge)
                ARG_PURGE="true"
                shift
                ;;
            --show-secrets)
                ARG_SHOW_SECRETS="--show-secrets"
                shift
                ;;
            *)
                die "unknown option: $1"
                ;;
        esac
    done
}

usage() {
    cat <<'USAGE_TEXT'
Usage:
  manage-proxy-protocols.sh status [--show-secrets]
  manage-proxy-protocols.sh install snell-v5
  manage-proxy-protocols.sh install snell-v6
  manage-proxy-protocols.sh install anytls  [--port 50014] [--host HOST]
  manage-proxy-protocols.sh uninstall snell-v5|snell-v6
  manage-proxy-protocols.sh uninstall anytls [--purge]
  manage-proxy-protocols.sh menu

Environment:
  ANYTLS_PORT      New AnyTLS port, default 50014
  ANYTLS_PASSWORD  New AnyTLS password, generated when absent
  PUBLIC_HOST      Host shown in generated Surge node lines

Notes:
  - Only Snell v5, Snell v6, and native AnyTLS are managed.
  - sing-box, Nginx, and other proxy services are not modified.
  - Snell installation only deploys the versioned binary and systemd template.
  - Snell users, configs, ports, PSKs, and version switches are managed by snell-userctl.sh.
  - Snell uninstall refuses to remove a version still assigned to a user.
  - AnyTLS uninstall keeps configuration unless --purge is used.
  - Native AnyTLS uses a dynamic self-signed certificate, so Surge nodes need skip-cert-verify=true.
USAGE_TEXT
}

menu() {
    local choice port purge
    while true; do
        refresh_screen
        [[ -t 0 ]] || return 0
        printf '%s%sProxy Protocol Manager%s\n\n' "$COLOR_BOLD" "$COLOR_CYAN" "$COLOR_RESET"
        cat <<'MENU_TEXT'
1) status
2) install Snell v5 binary
3) install Snell v6 binary
4) manage Snell users
5) install native AnyTLS
6) uninstall unused Snell v5 binary
7) uninstall unused Snell v6 binary
8) uninstall native AnyTLS
9) exit
MENU_TEXT
        read -r -p "choice: " choice
        [[ -n "$choice" ]] || return 0
        case "$choice" in
            1) run_menu_action status_all ;;
            2) run_menu_action install_snell 5 ;;
            3) run_menu_action install_snell 6 ;;
            4)
                if [[ -f "$SNELL_USERCTL" ]]; then
                    bash "$SNELL_USERCTL"
                else
                    warn "missing companion script: $SNELL_USERCTL"
                    pause_menu
                fi
                ;;
            5)
                port="$(prompt_value "AnyTLS port" "${ANYTLS_PORT:-50014}")"
                run_menu_action install_anytls "$port"
                ;;
            6)
                if confirm_action "Uninstall the unused Snell v5 binary?"; then
                    run_menu_action uninstall_snell 5
                fi
                ;;
            7)
                if confirm_action "Uninstall the unused Snell v6 binary?"; then
                    run_menu_action uninstall_snell 6
                fi
                ;;
            8)
                purge="false"
                confirm_action "Also delete the AnyTLS password and system user?" && purge="true"
                if confirm_action "Uninstall native AnyTLS?"; then
                    run_menu_action uninstall_anytls "$purge"
                fi
                ;;
            9) return 0 ;;
            *) warn "invalid choice"; pause_menu ;;
        esac
    done
}

main() {
    local command="${1:-menu}"
    [[ "$#" -gt 0 ]] && shift
    local protocol

    case "$command" in
        status)
            parse_common_options "$@"
            status_all "$ARG_SHOW_SECRETS"
            ;;
        install)
            protocol="${1:-}"
            [[ "$#" -gt 0 ]] && shift
            parse_common_options "$@"
            case "$protocol" in
                snell-v5) install_snell 5 ;;
                snell-v6) install_snell 6 ;;
                anytls) install_anytls "${ARG_PORT:-${ANYTLS_PORT:-50014}}" ;;
                *) die "install supports snell-v5, snell-v6, anytls" ;;
            esac
            ;;
        switch) die "switch individual Snell users with snell-userctl.sh switch NAME --version 5|6" ;;
        uninstall)
            protocol="${1:-}"
            [[ "$#" -gt 0 ]] && shift
            parse_common_options "$@"
            case "$protocol" in
                snell-v5) uninstall_snell 5 "$ARG_PURGE" ;;
                snell-v6) uninstall_snell 6 "$ARG_PURGE" ;;
                anytls) uninstall_anytls "$ARG_PURGE" ;;
                *) die "uninstall supports snell-v5, snell-v6, anytls" ;;
            esac
            ;;
        menu) menu ;;
        -h|--help|help) usage ;;
        *) die "unknown command: $command" ;;
    esac
}

main "$@"
