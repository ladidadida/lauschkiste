#!/usr/bin/env bash
# Installs the jukebox and runs `jukebox setup`.
#
#   curl -fsSL https://raw.githubusercontent.com/ladidadida/RPi-Jukebox-RFID/main/install.sh | bash
#   curl -fsSL .../install.sh | bash -s -- --source
#
# Options:
#   --source [DIR]     install from a git checkout (default DIR: ~/RPi-Jukebox-RFID) instead of
#                      the release wheels
#   --branch NAME      branch to check out with --source (default: main)
#   --version TAG      release to install (default: the latest release)
#   --wheels DIR       install the wheels in DIR instead of downloading a release
#   --repo OWNER/NAME  GitHub repository (default: ladidadida/RPi-Jukebox-RFID)
#   --home DIR         JUKEBOX_HOME (default: ~/jukebox on a Raspberry Pi, ~/.local/share/jukebox
#                      elsewhere, DIR/shared with --source)
#   --yes              don't ask, use defaults (also passed to `jukebox setup`)
#   --no-setup         only install, don't run `jukebox setup`

set -euo pipefail

REPO="ladidadida/RPi-Jukebox-RFID"
MODE=package
SOURCE_DIR="${HOME}/RPi-Jukebox-RFID"
BRANCH=main
VERSION=latest
WHEELS=""
JUKEBOX_HOME_DIR=""
ASSUME_YES=false
RUN_SETUP=true
MARKER="# jukebox (added by install.sh)"

log() { printf '\033[1m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[33mWarning: %s\033[0m\n' "$*" >&2; }
die() { printf '\033[31mError: %s\033[0m\n' "$*" >&2; exit 1; }

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --source)
                MODE=source
                if [[ $# -gt 1 && "$2" != --* ]]; then SOURCE_DIR="$2"; shift; fi ;;
            --branch) BRANCH="$2"; shift ;;
            --version) VERSION="$2"; shift ;;
            --wheels) WHEELS="$(cd "$2" && pwd)"; shift ;;
            --repo) REPO="$2"; shift ;;
            --home) JUKEBOX_HOME_DIR="$2"; shift ;;
            --yes|-y) ASSUME_YES=true ;;
            --no-setup) RUN_SETUP=false ;;
            -h|--help) echo "See the comment at the top of install.sh for the options."; exit 0 ;;
            *) die "unknown option $1 (see --help)" ;;
        esac
        shift
    done
}

is_debian() { [[ -r /etc/os-release ]] && grep -qiE '^(ID|ID_LIKE)=.*(debian|raspbian)' /etc/os-release; }
is_raspberry_pi() { grep -qs 'Raspberry Pi' /proc/device-tree/model; }

add_to_shell_profile() {
    local line="$1" file
    for file in "${HOME}/.profile" "${HOME}/.bashrc"; do
        touch "$file"
        grep -qxF "$line" "$file" || printf '\n%s\n%s\n' "$MARKER" "$line" >> "$file"
    done
}

install_system_packages() {
    if ! is_debian; then
        warn "not a Debian based system: install python3 (with headers), a C compiler and curl yourself"
        return
    fi
    log "Installing base packages"
    local packages=(ca-certificates curl python3 python3-dev python3-venv build-essential libffi-dev)
    [[ "$MODE" == source ]] && packages+=(git)
    $SUDO env DEBIAN_FRONTEND=noninteractive apt-get -qq update
    $SUDO env DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends "${packages[@]}"
}

# 32-bit Raspberry Pi OS: PyPI has no armv6/armv7 wheels for several dependencies (pydantic-core,
# av, ...), piwheels has. uv doesn't read /etc/pip.conf, so it gets its own configuration.
configure_piwheels() {
    case "$(uname -m)" in armv6l|armv7l) ;; *) return 0 ;; esac
    is_raspberry_pi || return 0
    local config="${XDG_CONFIG_HOME:-${HOME}/.config}/uv/uv.toml"
    grep -qs piwheels "$config" && return 0
    log "Using piwheels for prebuilt ARM packages (${config})"
    mkdir -p "$(dirname "$config")"
    printf '\n[[index]]\nname = "piwheels"\nurl = "https://www.piwheels.org/simple"\n' >> "$config"
}

install_uv() {
    export PATH="${HOME}/.local/bin:${PATH}"
    if command -v uv >/dev/null; then return; fi
    log "Installing uv"
    curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh
    command -v uv >/dev/null || die "uv was installed but is not on PATH"
}

download_release_wheels() {
    local target="$1" api="https://api.github.com/repos/${REPO}/releases"
    [[ "$VERSION" == latest ]] && api="${api}/latest" || api="${api}/tags/${VERSION}"
    log "Downloading the wheels of release ${VERSION} from ${REPO}"
    local release
    release="$(curl -fsSL "$api")" || die "no release ${VERSION} found in ${REPO}"
    python3 -c '
import json, sys
for asset in json.load(sys.stdin).get("assets", []):
    if asset["name"].endswith(".whl"):
        print(asset["browser_download_url"])
' <<< "$release" > "${target}/urls"
    [[ -s "${target}/urls" ]] || die "release ${VERSION} of ${REPO} has no wheels"
    (cd "$target" && xargs -n1 curl -fsSLO < urls)
}

install_package() {
    local wheels="$WHEELS"
    if [[ -z "$wheels" ]]; then
        wheels="$(mktemp -d)"
        download_release_wheels "$wheels"
    fi
    local cli with=()
    cli="$(ls "$wheels"/jukebox_cli-*.whl 2>/dev/null | head -n1)"
    [[ -n "$cli" ]] || die "no jukebox_cli wheel in ${wheels}"
    for wheel in "$wheels"/*.whl; do
        [[ "$wheel" == "$cli" ]] || with+=(--with "$wheel")
    done
    log "Installing the jukebox package"
    uv tool install --force --python python3 "$cli" "${with[@]}"
    JUKEBOX_BIN="$(uv tool dir --bin)/jukebox"
}

install_source() {
    if [[ -d "${SOURCE_DIR}/.git" ]]; then
        log "Using the existing checkout ${SOURCE_DIR}"
    else
        log "Cloning ${REPO} (${BRANCH}) into ${SOURCE_DIR}"
        git clone --branch "$BRANCH" "https://github.com/${REPO}.git" "$SOURCE_DIR"
    fi
    log "Installing the Python environment"
    (cd "$SOURCE_DIR" && uv sync --no-dev --frozen --python python3)
    if [[ ! -f "${SOURCE_DIR}/packages/webapp/build/index.html" ]]; then
        if command -v npm >/dev/null; then
            log "Building the web app"
            (cd "${SOURCE_DIR}/packages/webapp" && npm ci && npm run build)
        else
            log "Taking the web app from the latest release (no npm to build it)"
            local tmp
            tmp="$(mktemp -d)"
            VERSION=latest download_release_wheels "$tmp"
            python3 - "$tmp" "${SOURCE_DIR}/packages/webapp/build" <<'PYTHON'
import glob, pathlib, sys, zipfile
wheel = glob.glob(f"{sys.argv[1]}/jukebox-*.whl")[0]
with zipfile.ZipFile(wheel) as archive:
    for name in archive.namelist():
        if name.startswith("jukebox/webapp/") and not name.endswith("/"):
            target = pathlib.Path(sys.argv[2], name[len("jukebox/webapp/"):])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
PYTHON
        fi
    fi
    mkdir -p "${HOME}/.local/bin"
    ln -sf "${SOURCE_DIR}/.venv/bin/jukebox" "${HOME}/.local/bin/jukebox"
    JUKEBOX_BIN="${SOURCE_DIR}/.venv/bin/jukebox"
}

choose_home() {
    if [[ -z "$JUKEBOX_HOME_DIR" ]]; then
        if [[ "$MODE" == source ]]; then
            JUKEBOX_HOME_DIR="${SOURCE_DIR}/shared"
        elif is_raspberry_pi; then
            JUKEBOX_HOME_DIR="${HOME}/jukebox"
        else
            return 0
        fi
    fi
    JUKEBOX_HOME_DIR="$(mkdir -p "$JUKEBOX_HOME_DIR" && cd "$JUKEBOX_HOME_DIR" && pwd)"
    export JUKEBOX_HOME="$JUKEBOX_HOME_DIR"
    add_to_shell_profile "export JUKEBOX_HOME=\"${JUKEBOX_HOME_DIR}\""
}

# Everything runs from main, so a partially downloaded script does nothing
main() {
    parse_args "$@"
    SUDO=""
    if [[ "$(id -u)" -ne 0 ]]; then
        SUDO=sudo
    else
        warn "running as root; the jukebox will run as root too"
    fi

    install_system_packages
    install_uv
    configure_piwheels
    if [[ "$MODE" == source ]]; then install_source; else install_package; fi
    add_to_shell_profile 'export PATH="$HOME/.local/bin:$PATH"'
    choose_home

    "$JUKEBOX_BIN" home

    if [[ "$RUN_SETUP" == true ]]; then
        log "Setting up this machine"
        if [[ "$ASSUME_YES" == true ]]; then
            "$JUKEBOX_BIN" setup --yes
        elif [[ -t 0 ]]; then
            "$JUKEBOX_BIN" setup
        elif (: < /dev/tty) 2>/dev/null; then
            "$JUKEBOX_BIN" setup < /dev/tty
        else
            "$JUKEBOX_BIN" setup --yes
        fi
    fi

    log "Done. Open a new shell (or 'source ~/.profile') to use the 'jukebox' command."
}

main "$@"
