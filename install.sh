#!/usr/bin/env bash
# Installs Lauschkiste and runs `lauschctl setup`.
#
#   curl -fsSL https://raw.githubusercontent.com/ladidadida/lauschkiste/main/install.sh | bash
#   curl -fsSL .../install.sh | bash -s -- --from source
#
# Where Lauschkiste comes from (--from):
#   pypi     the packages on PyPI (default); --version 0.1.0a4 picks a version
#   github   the wheels attached to a release; --version TAG picks a release
#   source   a git checkout (default ~/lauschkiste, --source DIR for another one) that runs from its
#            own folder; --branch NAME picks the branch
#   testpypi, or the URL of a package index, for testing; --wheels DIR installs wheels from a folder
#
# Options:
#   --from SOURCE      see above
#   --source [DIR]     the same as --from source
#   --branch NAME      branch to check out with --from source (default: main)
#   --version V        release to install (default: the latest)
#   --wheels DIR       install the wheels in DIR instead of downloading a release
#   --repo OWNER/NAME  GitHub repository (default: ladidadida/lauschkiste)
#   --home DIR         LAUSCHKISTE_HOME (default: ~/lauschkiste on a Raspberry Pi,
#                      ~/.local/share/lauschkiste elsewhere, DIR/shared with --source)
#   --library DIR      the library (music, audiobooks) in DIR instead of <home>/library
#   --yes              don't ask, use defaults (also passed to `lauschctl setup`)
#   --no-setup         only install, don't run `lauschctl setup`

set -euo pipefail

REPO="ladidadida/lauschkiste"
MODE=package
SOURCE_DIR="${HOME}/lauschkiste"
BRANCH=main
VERSION=latest
FROM=
WHEELS=""
BUNDLED_PLUGINS=(lauschkiste-plugin-board-raspberry-pi lauschkiste-plugin-devices lauschkiste-plugin-mpd
                 lauschkiste-plugin-rfid-readers lauschkiste-plugin-samba lauschkiste-plugin-audiobookshelf
                 lauschkiste-plugin-directories)
HOME_DIR=""
LIBRARY_DIR=""
ASSUME_YES=false
RUN_SETUP=true
MARKER="# lauschkiste (added by install.sh)"

log() { printf '\033[1m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[33mWarning: %s\033[0m\n' "$*" >&2; }
die() { printf '\033[31mError: %s\033[0m\n' "$*" >&2; exit 1; }

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --source)
                [[ -z "$FROM" || "$FROM" == source ]] || die "--source and --from ${FROM} exclude each other"
                MODE=source
                FROM=source
                if [[ $# -gt 1 && "$2" != --* ]]; then SOURCE_DIR="$2"; shift; fi ;;
            --branch) BRANCH="$2"; shift ;;
            --version) VERSION="$2"; shift ;;
            --from) FROM="$2"; shift ;;
            --wheels) WHEELS="$(cd "$2" && pwd)"; shift ;;
            --repo) REPO="$2"; shift ;;
            --home) HOME_DIR="$2"; shift ;;
            --library) LIBRARY_DIR="$2"; shift ;;
            --yes|-y) ASSUME_YES=true ;;
            --no-setup) RUN_SETUP=false ;;
            -h|--help) echo "See the comment at the top of install.sh for the options."; exit 0 ;;
            *) die "unknown option $1 (see --help)" ;;
        esac
        shift
    done
}

check_args() {
    if [[ -z "$FROM" ]]; then if [[ -n "$WHEELS" ]]; then FROM=github; else FROM=pypi; fi; fi
    [[ "$FROM" != source ]] || MODE=source
    if [[ "$MODE" == source && "$FROM" != source ]]; then die "--source and --from ${FROM} exclude each other"; fi
    if [[ -n "$WHEELS" && "$FROM" != github ]]; then die "--wheels and --from ${FROM} exclude each other"; fi
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
    local base="$api" release
    [[ "$VERSION" == latest ]] && api="${api}/latest" || api="${api}/tags/${VERSION}"
    log "Downloading the wheels of release ${VERSION} from ${REPO}"
    if ! release="$(curl -fsSL "$api" 2>/dev/null)"; then
        # No stable release yet: take the newest pre-release
        [[ "$VERSION" == latest ]] && release="$(curl -fsSL "${base}?per_page=20" | python3 -c '
import json, sys
for r in json.load(sys.stdin):
    if not r.get("draft") and any(a["name"].endswith(".whl") for a in r.get("assets", [])):
        print(json.dumps(r))
        break
')"
        [[ -n "${release:-}" ]] || die "no release ${VERSION} found in ${REPO}"
    fi
    python3 -c '
import json, sys
for asset in json.load(sys.stdin).get("assets", []):
    if asset["name"].endswith(".whl"):
        print(asset["browser_download_url"])
' <<< "$release" > "${target}/urls"
    [[ -s "${target}/urls" ]] || die "release ${VERSION} of ${REPO} has no wheels"
    (cd "$target" && xargs -n1 curl -fsSLO < urls)
}

# `uv tool install --force` removes the working installation before it knows the new one can be installed:
# keep the old one aside and put it back when the new one fails
tool_install() {
    local env bin
    env="$(uv tool dir)/lauschkiste"
    bin="$(uv tool dir --bin)"
    if [[ -d "$env" ]]; then
        rm -rf "${env}.previous"
        mv "$env" "${env}.previous"
    fi
    if uv tool install --force --compile-bytecode --python python3 "$@"; then
        rm -rf "${env}.previous"
        return
    fi
    if [[ -d "${env}.previous" ]]; then
        rm -rf "$env"
        mv "${env}.previous" "$env"
        for name in lauschctl lauschkiste; do
            [[ -e "${env}/bin/${name}" ]] && ln -sf "${env}/bin/${name}" "${bin}/${name}"
        done
        die "the installation failed; the previous installation was restored"
    fi
    die "the installation failed"
}

install_from_index() {
    local requirement=lauschkiste args=()
    [[ "$VERSION" == latest ]] || requirement="lauschkiste==${VERSION}"
    case "$FROM" in
        pypi)
            # piwheels (32-bit ARM) lists the Lauschkiste projects without their newest versions and would hide them
            case "$(uname -m)" in
                armv6l|armv7l)
                    for name in lauschkiste lauschkiste-core "${BUNDLED_PLUGINS[@]}"; do
                        args+=(--find-links "https://pypi.org/simple/${name}/")
                    done ;;
            esac ;;
        testpypi)
            # TestPyPI holds test copies of many projects (a "fastapi" 1.0 that does not build): PyPI, and
            # piwheels on 32-bit ARM, come first and TestPyPI only supplies what they lack, the Lauschkiste packages
            case "$(uname -m)" in armv6l|armv7l) args+=(--index https://www.piwheels.org/simple) ;; esac
            args+=(--index https://pypi.org/simple/ --default-index https://test.pypi.org/simple/) ;;
        *) args+=(--index "$FROM" --index-strategy unsafe-best-match) ;;  # an index of the Lauschkiste packages only
    esac
    local with=()
    for plugin in "${BUNDLED_PLUGINS[@]}"; do with+=(--with "$plugin"); done
    log "Installing ${requirement} from ${FROM}"
    tool_install "${args[@]}" "$requirement" "${with[@]}"
    CTL="$(uv tool dir --bin)/lauschctl"
}

install_package() {
    if [[ "$FROM" != github ]]; then
        install_from_index
        return
    fi
    local wheels="$WHEELS"
    if [[ -z "$wheels" ]]; then
        wheels="$(mktemp -d)"
        download_release_wheels "$wheels"
    fi
    local cli with=()
    cli="$(ls "$wheels"/lauschkiste-[0-9]*.whl 2>/dev/null | head -n1)"
    [[ -n "$cli" ]] || die "no lauschkiste wheel in ${wheels}"
    ls "$wheels"/lauschkiste_core-*.whl >/dev/null 2>&1 \
        || die "the wheels in ${wheels} are from before the packages were renamed (no lauschkiste_core wheel): use a newer release, --from source or --wheels"
    for wheel in "$wheels"/*.whl; do
        [[ "$wheel" == "$cli" ]] || with+=(--with "$wheel")
    done
    log "Installing the Lauschkiste package"
    tool_install "$cli" "${with[@]}"
    CTL="$(uv tool dir --bin)/lauschctl"
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
prefix = "lauschkiste/webapp/"
for wheel in glob.glob(f"{sys.argv[1]}/*.whl"):
    with zipfile.ZipFile(wheel) as archive:
        for name in archive.namelist():
            if name.startswith(prefix) and not name.endswith("/"):
                target = pathlib.Path(sys.argv[2], name[len(prefix):])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(name))
PYTHON
        fi
    fi
    mkdir -p "${HOME}/.local/bin"
    local command
    for command in lauschkiste lauschctl; do
        ln -sf "${SOURCE_DIR}/.venv/bin/${command}" "${HOME}/.local/bin/${command}"
    done
    CTL="${SOURCE_DIR}/.venv/bin/lauschctl"
}

choose_home() {
    if [[ -z "$HOME_DIR" ]]; then
        if [[ "$MODE" == source ]]; then
            HOME_DIR="${SOURCE_DIR}/shared"
        elif is_raspberry_pi; then
            HOME_DIR="${HOME}/lauschkiste"
        else
            return 0
        fi
    fi
    HOME_DIR="$(mkdir -p "$HOME_DIR" && cd "$HOME_DIR" && pwd)"
    export LAUSCHKISTE_HOME="$HOME_DIR"
    add_to_shell_profile "export LAUSCHKISTE_HOME=\"${HOME_DIR}\""
}

# Everything runs from main, so a partially downloaded script does nothing
main() {
    parse_args "$@"
    check_args
    SUDO=""
    if [[ "$(id -u)" -ne 0 ]]; then
        SUDO=sudo
    else
        warn "running as root; Lauschkiste will run as root too"
    fi

    install_system_packages
    install_uv
    configure_piwheels
    if [[ "$MODE" == source ]]; then install_source; else install_package; fi
    add_to_shell_profile 'export PATH="$HOME/.local/bin:$PATH"'
    choose_home

    "$CTL" home
    if [[ -n "$LIBRARY_DIR" ]]; then
        LIBRARY_DIR="$(mkdir -p "$LIBRARY_DIR" && cd "$LIBRARY_DIR" && pwd)"
        "$CTL" config set library.path "$LIBRARY_DIR"
    fi

    if [[ "$RUN_SETUP" == true ]]; then
        log "Setting up this machine"
        if [[ "$ASSUME_YES" == true ]]; then
            "$CTL" setup --yes
        elif [[ -t 0 ]]; then
            "$CTL" setup
        elif (: < /dev/tty) 2>/dev/null; then
            "$CTL" setup < /dev/tty
        else
            "$CTL" setup --yes
        fi
    fi

    log "Done. Open a new shell (or 'source ~/.profile') to use the 'lauschctl' command."
}

main "$@"
