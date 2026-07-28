#!/usr/bin/env bash
set -euo pipefail

: "${AZURE_ACR_NAME:?Set AZURE_ACR_NAME first.}"
: "${AZURE_ACR_TASK:?Set AZURE_ACR_TASK first.}"
: "${AZURE_CONTAINER_APP:?Set AZURE_CONTAINER_APP first.}"
: "${AZURE_RESOURCE_GROUP:?Set AZURE_RESOURCE_GROUP first.}"
: "${RUSHD_IMAGE_TAG:?Set RUSHD_IMAGE_TAG first.}"

for command_name in az jq curl; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "${command_name} is required." >&2
    exit 1
  fi
done

if [[ ! "${RUSHD_IMAGE_TAG}" =~ ^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$ ]]; then
  echo "RUSHD_IMAGE_TAG is not a valid container image tag." >&2
  exit 1
fi

release_sha="${GITHUB_SHA:-${RUSHD_IMAGE_TAG#0.1.0-}}"
revision_suffix="gh-${release_sha:0:12}"
registry_server="${AZURE_ACR_NAME}.azurecr.io"
application_image="${registry_server}/rushd:${RUSHD_IMAGE_TAG}"
current_app_file="$(mktemp)"
release_file="$(mktemp)"

cleanup() {
  rm -f "${current_app_file}" "${release_file}"
}
trap cleanup EXIT

az containerapp show \
  --resource-group "${AZURE_RESOURCE_GROUP}" \
  --name "${AZURE_CONTAINER_APP}" \
  --output json >"${current_app_file}"

jq \
  --arg application_image "${application_image}" \
  --arg image_tag "${RUSHD_IMAGE_TAG}" \
  --arg revision_suffix "${revision_suffix}" \
  '
    def update_asset_version:
      if has("env") then
        .env |= map(
          if .name == "RUSHD_ASSET_VERSION" then
            .value = $image_tag
          else
            .
          end
        )
      else
        .
      end;

    {
      name: .name,
      type: .type,
      properties: {
        template: (
          .properties.template
          | .revisionSuffix = $revision_suffix
          | .containers |= map(
              if (
                .name == "frontend"
                or .name == "backend"
                or .name == "websocket"
                or .name == "worker"
                or .name == "scheduler"
              ) then
                .image = $application_image
                | update_asset_version
              else
                .
              end
            )
          | .initContainers |= map(
              if .name == "configure" then
                .image = $application_image
                | update_asset_version
              else
                .
              end
            )
        )
      }
    }
  ' "${current_app_file}" >"${release_file}"

updated_images="$(
  jq -r '
    [
      .properties.template.initContainers[],
      .properties.template.containers[]
      | select(
          .name == "configure"
          or .name == "frontend"
          or .name == "backend"
          or .name == "websocket"
          or .name == "worker"
          or .name == "scheduler"
        )
        | .image
    ]
    | unique
    | .[]
  ' "${release_file}"
)"

if [[ "${updated_images}" != "${application_image}" ]]; then
  echo "Release payload does not update every Rushd application container." >&2
  exit 1
fi

if [[ "${RUSHD_PREPARE_ONLY:-false}" == "true" ]]; then
  echo "Release payload validation passed for ${application_image}."
  exit 0
fi

echo "Building ${application_image} in Azure Container Registry."
az acr task run \
  --registry "${AZURE_ACR_NAME}" \
  --name "${AZURE_ACR_TASK}" \
  --context . \
  --file Containerfile \
  --set "IMAGE_TAG=${RUSHD_IMAGE_TAG}" \
  --only-show-errors \
  --output none

echo "Creating Container Apps revision ${revision_suffix}."
az containerapp revision copy \
  --resource-group "${AZURE_RESOURCE_GROUP}" \
  --name "${AZURE_CONTAINER_APP}" \
  --yaml "${release_file}" \
  --only-show-errors \
  --output none

latest_revision="$(
  az containerapp show \
    --resource-group "${AZURE_RESOURCE_GROUP}" \
    --name "${AZURE_CONTAINER_APP}" \
    --query properties.latestRevisionName \
    --output tsv
)"

for attempt in {1..60}; do
  revision_state="$(
    az containerapp revision show \
      --resource-group "${AZURE_RESOURCE_GROUP}" \
      --name "${AZURE_CONTAINER_APP}" \
      --revision "${latest_revision}" \
      --query '[properties.provisioningState,properties.runningState,properties.healthState]' \
      --output tsv
  )"

  read -r provisioning_state running_state health_state <<<"${revision_state}"
  if [[ "${provisioning_state}" == "Succeeded" && "${running_state}" == "Running" && "${health_state}" == "Healthy" ]]; then
    break
  fi

  if [[ "${provisioning_state}" == "Failed" || "${running_state}" == "Failed" || "${health_state}" == "Unhealthy" ]]; then
    echo "Revision ${latest_revision} failed: ${revision_state}" >&2
    exit 1
  fi

  if [[ "${attempt}" -eq 60 ]]; then
    echo "Timed out waiting for revision ${latest_revision}: ${revision_state}" >&2
    exit 1
  fi

  sleep 10
done

application_fqdn="$(
  az containerapp show \
    --resource-group "${AZURE_RESOURCE_GROUP}" \
    --name "${AZURE_CONTAINER_APP}" \
    --query properties.configuration.ingress.fqdn \
    --output tsv
)"
application_url="https://${application_fqdn}"

curl \
  --silent \
  --show-error \
  --fail \
  --retry 12 \
  --retry-all-errors \
  --retry-delay 10 \
  "${application_url}/api/method/ping" >/dev/null

curl \
  --silent \
  --show-error \
  --fail \
  --retry 12 \
  --retry-all-errors \
  --retry-delay 10 \
  "${application_url}/login" >/dev/null

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "application_url=${application_url}" >>"${GITHUB_OUTPUT}"
  echo "revision_name=${latest_revision}" >>"${GITHUB_OUTPUT}"
  echo "image_tag=${RUSHD_IMAGE_TAG}" >>"${GITHUB_OUTPUT}"
fi

echo "Rushd staging release succeeded: ${latest_revision}"
echo "Application URL: ${application_url}"
