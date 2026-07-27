#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
infra_dir="$(cd "${script_dir}/.." && pwd)"

: "${RUSHD_AZURE_SUBSCRIPTION_ID:?Set RUSHD_AZURE_SUBSCRIPTION_ID first.}"
: "${RUSHD_POSTGRES_ADMIN_PASSWORD:?Set RUSHD_POSTGRES_ADMIN_PASSWORD first.}"

if [[ "${RUSHD_CONFIRM_DEPLOY:-}" != "staging" ]]; then
  echo "Deployment stopped. Set RUSHD_CONFIRM_DEPLOY=staging only after reviewing the what-if output." >&2
  exit 1
fi

if ! command -v az >/dev/null 2>&1; then
  echo "Azure CLI is required. Install it, then rerun this script." >&2
  exit 1
fi

az account set --subscription "${RUSHD_AZURE_SUBSCRIPTION_ID}"
az deployment sub create \
  --name "rushd-staging-foundation" \
  --location "${RUSHD_AZURE_LOCATION:-uaenorth}" \
  --template-file "${infra_dir}/main.bicep" \
  --parameters "${infra_dir}/environments/staging.bicepparam"
