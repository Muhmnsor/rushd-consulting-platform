#!/usr/bin/env bash
set -euo pipefail

: "${DB_HOST:?DB_HOST is required}"
: "${DB_PORT:=5432}"
: "${REDIS_CACHE:=redis://127.0.0.1:6379}"
: "${REDIS_QUEUE:=redis://127.0.0.1:6380}"
: "${SOCKETIO_PORT:=9000}"

bench_dir="/home/frappe/frappe-bench"
cd "${bench_dir}"

mkdir -p sites
find apps -mindepth 1 -maxdepth 1 -type d -exec basename {} \; \
  | sort -u > sites/apps.txt

bench set-config --global db_host "${DB_HOST}"
bench set-config --global --parse db_port "${DB_PORT}"
bench set-config --global redis_cache "${REDIS_CACHE}"
bench set-config --global redis_queue "${REDIS_QUEUE}"
bench set-config --global redis_socketio "${REDIS_QUEUE}"
bench set-config --global --parse socketio_port "${SOCKETIO_PORT}"
bench set-config --global --parse serve_default_site True
