#!/usr/bin/env bash
# Runs install.sh from this checkout in a fresh Debian container (as user pi), then starts the
# server and checks the API and the web app.
#
#   ci/test_install.sh <debian codename> <install.sh options...>
#   ci/test_install.sh trixie --wheels dist      (wheels built into ./dist)
#   ci/test_install.sh trixie --index dist       (a package index made of ./dist, installed from like from PyPI)
#   ci/test_install.sh trixie --source           (this checkout; web app built into packages/webapp/build)

set -euo pipefail

CODENAME="$1"
shift

tar -C "$(dirname "$0")/.." --exclude=./.venv --exclude=./packages/webapp/node_modules --exclude=./shared \
    -cf - . | docker run --rm -i -e INSTALL_ARGS="$*" "debian:${CODENAME}-slim" bash -euo pipefail -c '
apt-get -qq update && apt-get -qq install -y sudo procps curl >/dev/null
useradd -m -s /bin/bash pi && echo "pi ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/pi
mkdir /home/pi/checkout && tar -C /home/pi/checkout -xf - && chown -R pi:pi /home/pi/checkout
args="${INSTALL_ARGS/--source/--source /home/pi/checkout}"
args="${args/--wheels /--wheels /home/pi/checkout/}"
if [[ "$INSTALL_ARGS" == --index\ * ]]; then
    apt-get -qq install -y python3 >/dev/null
    python3 /home/pi/checkout/ci/make_index.py "/home/pi/checkout/${INSTALL_ARGS#--index }" /home/pi/index
    chown -R pi:pi /home/pi/index
    su - pi -c "nohup python3 -m http.server 8099 -d /home/pi/index >/tmp/index.log 2>&1 &"
    args="--from http://localhost:8099/simple/"
fi
su - pi -c "bash ~/checkout/install.sh --yes ${args}"
su - pi -c "
    set -e
    cd /tmp && source ~/.profile
    lauschctl home
    lauschctl setup --check --yes
    (lauschkiste > /tmp/run.log 2>&1 &)
    for i in \$(seq 1 120); do curl -fsS localhost:5556/api/v1/health 2>/dev/null && break; sleep 1; done
    echo
    curl -fsS localhost:5556/ | grep -q \"<div id=\\\"root\\\">\" || { tail -50 /tmp/run.log; exit 1; }
    curl -fsS localhost:5556/api/v1/modules > /dev/null
    echo \"Lauschkiste runs and serves the web app.\"
"
'
