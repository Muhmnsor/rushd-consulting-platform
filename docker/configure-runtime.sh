#!/usr/bin/env bash
set -euo pipefail

: "${DB_HOST:?DB_HOST is required}"
: "${DB_PORT:=5432}"
: "${REDIS_CACHE:=redis://127.0.0.1:6379}"
: "${REDIS_QUEUE:=redis://127.0.0.1:6380}"
: "${SOCKETIO_PORT:=9000}"
: "${RUSHD_ASSET_VERSION:=unversioned}"

bench_dir="/home/frappe/frappe-bench"
cd "${bench_dir}"

mkdir -p sites
if [[ ! -f sites/common_site_config.json ]]; then
  printf '{}\n' > sites/common_site_config.json
fi

find apps -mindepth 1 -maxdepth 1 -type d -exec basename {} \; \
  | sort -u > sites/apps.txt

# Azure Files does not support the symbolic links used by the upstream image's
# sites/assets directory. Materialize their targets once per application image
# so both Gunicorn and Nginx can read the asset manifests and static files.
assets_dir="sites/assets"
assets_marker="${assets_dir}/.rushd-asset-version"
installed_asset_version=""
if [[ -f "${assets_marker}" ]]; then
  installed_asset_version="$(<"${assets_marker}")"
fi

if [[ "${installed_asset_version}" != "${RUSHD_ASSET_VERSION}" ]]; then
  echo "Materializing Frappe assets for ${RUSHD_ASSET_VERSION}."
  mkdir -p "${assets_dir}"
  cp -RL assets/. "${assets_dir}/"
  printf '%s\n' "${RUSHD_ASSET_VERSION}" > "${assets_marker}"
fi

bench set-config --global db_host "${DB_HOST}"
bench set-config --global --parse db_port "${DB_PORT}"
bench set-config --global redis_cache "${REDIS_CACHE}"
bench set-config --global redis_queue "${REDIS_QUEUE}"
bench set-config --global redis_socketio "${REDIS_QUEUE}"
bench set-config --global --parse socketio_port "${SOCKETIO_PORT}"
bench set-config --global --parse serve_default_site True
