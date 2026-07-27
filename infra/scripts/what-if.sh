#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
infra_dir="$(cd "${script_dir}/.." && pwd)"

: "${RUSHD_AZURE_SUBSCRIPTION_ID:?Set RUSHD_AZURE_SUBSCRIPTION_ID first.}"
: "${RUSHD_POSTGRES_ADMIN_PASSWORD:?Set RUSHD_POSTGRES_ADMIN_PASSWORD first.}"
: "${RUSHD_SITE_ADMIN_PASSWORD:?Set RUSHD_SITE_ADMIN_PASSWORD first.}"

if ! command -v az >/dev/null 2>&1; then
  echo "Azure CLI is required. Install it, then rerun this script." >&2
  exit 1
fi

az account set --subscription "${RUSHD_AZURE_SUBSCRIPTION_ID}"
az deployment sub what-if \
  --name "rushd-staging-foundation-preview" \
  --location "${RUSHD_AZURE_LOCATION:-uaenorth}" \
  --template-file "${infra_dir}/main.bicep" \
  --parameters "${infra_dir}/environments/staging.bicepparam"
