#!/usr/bin/env bash
set -euo pipefail

: "${RUSHD_SITE_NAME:?RUSHD_SITE_NAME is required}"
: "${RUSHD_ASSET_VERSION:=unversioned}"

bench_dir="/home/frappe/frappe-bench"
site_dir="${bench_dir}/sites/${RUSHD_SITE_NAME}"
migration_marker="${site_dir}/.rushd-migrated-version"
cd "${bench_dir}"

if [[ -f "${site_dir}/site_config.json" ]]; then
  migrated_version=""
  if [[ -f "${migration_marker}" ]]; then
    migrated_version="$(<"${migration_marker}")"
  fi

  if [[ "${migrated_version}" != "${RUSHD_ASSET_VERSION}" ]]; then
    echo "Waiting for Redis before migrating ${RUSHD_SITE_NAME}."
    for attempt in {1..60}; do
      if (
        exec 3<>"/dev/tcp/127.0.0.1/6379"
        exec 4<>"/dev/tcp/127.0.0.1/6380"
      ) 2>/dev/null; then
        break
      fi

      if [[ "${attempt}" -eq 60 ]]; then
        echo "Redis did not become ready before migration." >&2
        exit 1
      fi

      sleep 1
    done

    echo "Migrating ${RUSHD_SITE_NAME} for ${RUSHD_ASSET_VERSION}."
    bench --site "${RUSHD_SITE_NAME}" migrate
    bench --site "${RUSHD_SITE_NAME}" clear-cache
    printf '%s\n' "${RUSHD_ASSET_VERSION}" >"${migration_marker}"
  else
    echo "Migration already completed for ${RUSHD_ASSET_VERSION}."
  fi
else
  echo "Site ${RUSHD_SITE_NAME} does not exist yet; skipping migration."
fi

exec /usr/local/bin/start.sh
