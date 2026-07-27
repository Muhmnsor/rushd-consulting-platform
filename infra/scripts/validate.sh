#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
infra_dir="$(cd "${script_dir}/.." && pwd)"

if [[ -z "${RUSHD_POSTGRES_ADMIN_PASSWORD:-}" ]]; then
  echo "Set RUSHD_POSTGRES_ADMIN_PASSWORD before validating staging parameters." >&2
  exit 1
fi

if [[ -n "${RUSHD_BICEP_BIN:-}" ]]; then
  "${RUSHD_BICEP_BIN}" --version
  "${RUSHD_BICEP_BIN}" build "${infra_dir}/main.bicep" --stdout >/dev/null
  "${RUSHD_BICEP_BIN}" build-params "${infra_dir}/environments/staging.bicepparam" --stdout >/dev/null
elif command -v bicep >/dev/null 2>&1; then
  bicep --version
  bicep build "${infra_dir}/main.bicep" --stdout >/dev/null
  bicep build-params "${infra_dir}/environments/staging.bicepparam" --stdout >/dev/null
elif command -v az >/dev/null 2>&1; then
  az bicep version
  az bicep build --file "${infra_dir}/main.bicep" --stdout >/dev/null
  az bicep build-params --file "${infra_dir}/environments/staging.bicepparam" --stdout >/dev/null
else
  echo "Bicep CLI or Azure CLI is required. Install one, then rerun this script." >&2
  exit 1
fi

echo "Rushd Azure Bicep validation passed."
