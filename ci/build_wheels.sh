#!/usr/bin/env bash
# Build the source distributions and wheels of the core, the CLI and the bundled plugins, with the web
# app inside the core's. The wheels are built from the source distributions, so what is published works.
#   ci/build_wheels.sh [output-dir]     (default: dist/)
# Set SKIP_WEBAPP_BUILD=1 to package an existing packages/webapp/build.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-${ROOT}/dist}"
WEBAPP_TARGET="${ROOT}/packages/lauschkiste/src/lauschkiste/webapp"

if [[ -z "${SKIP_WEBAPP_BUILD:-}" ]]; then
  (cd "${ROOT}/packages/webapp" && npm ci && npm run build)
fi
if [[ ! -f "${ROOT}/packages/webapp/build/index.html" ]]; then
  echo "No web app build in packages/webapp/build" >&2
  exit 1
fi
newer="$(find "${ROOT}/packages/webapp/src" "${ROOT}/packages/webapp/public" "${ROOT}/packages/webapp/package.json" \
  -newer "${ROOT}/packages/webapp/build/index.html" -type f -not -path '*/cover-cache/*' -print -quit)"
if [[ -n "${newer}" ]]; then
  echo "packages/webapp/build is older than its sources (e.g. ${newer#"${ROOT}/"}); rebuild it or unset SKIP_WEBAPP_BUILD" >&2
  exit 1
fi

rm -rf "${WEBAPP_TARGET:?}"
cp -r "${ROOT}/packages/webapp/build" "${WEBAPP_TARGET}"
rm -rf "${WEBAPP_TARGET:?}/cover-cache"

cd "${ROOT}"
uv build --all-packages -o "${OUT}"
rm -rf "${WEBAPP_TARGET:?}"
ls -1 "${OUT}"
