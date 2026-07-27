#!/usr/bin/env bash
set -euo pipefail

: "${RUSHD_SITE_NAME:?RUSHD_SITE_NAME is required}"
: "${DB_HOST:?DB_HOST is required}"
: "${DB_PORT:=5432}"
: "${DB_ROOT_USERNAME:?DB_ROOT_USERNAME is required}"
: "${DB_ROOT_PASSWORD:?DB_ROOT_PASSWORD is required}"
: "${SITE_ADMIN_PASSWORD:?SITE_ADMIN_PASSWORD is required}"

bench_dir="/home/frappe/frappe-bench"
site_dir="${bench_dir}/sites/${RUSHD_SITE_NAME}"
cd "${bench_dir}"

if [[ -f "${site_dir}/site_config.json" ]]; then
  echo "Site ${RUSHD_SITE_NAME} already exists; running migrations."
  bench --site "${RUSHD_SITE_NAME}" migrate
else
  echo "Creating site ${RUSHD_SITE_NAME}."
  bench new-site "${RUSHD_SITE_NAME}" \
    --db-type postgres \
    --db-host "${DB_HOST}" \
    --db-port "${DB_PORT}" \
    --db-root-username "${DB_ROOT_USERNAME}" \
    --db-root-password "${DB_ROOT_PASSWORD}" \
    --admin-password "${SITE_ADMIN_PASSWORD}" \
    --install-app consultation_center \
    --set-default
fi

bench --site "${RUSHD_SITE_NAME}" enable-scheduler
bench --site "${RUSHD_SITE_NAME}" clear-cache

