#!/usr/bin/env bash
set -euo pipefail

region="${1:?region is required}"
profile="${2:?oci cli profile is required}"
compartment_id="${3:?compartment ocid is required}"
display_name="${4:?project display name is required}"
description="${5:-}"
output_dir="${6:?output directory is required}"

response_file="${output_dir}/genai_project_response.json"
id_file="${output_dir}/genai_project_id.txt"

if [[ -s "${id_file}" ]]; then
  printf 'Reusing generated project id from %s\n' "${id_file}"
  exit 0
fi

tmp_file="$(mktemp)"
trap 'rm -f "${tmp_file}"' EXIT

cmd=(
  oci generative-ai generative-ai-project create
  --region "${region}"
  --profile "${profile}"
  --compartment-id "${compartment_id}"
  --display-name "${display_name}"
  --output json
)

if [[ -n "${description}" ]]; then
  cmd+=(--description "${description}")
fi

"${cmd[@]}" > "${tmp_file}"
mv "${tmp_file}" "${response_file}"

project_id="$(sed -n 's/^[[:space:]]*"id":[[:space:]]*"\([^"]*\)".*/\1/p' "${response_file}" | head -n 1)"
if [[ -z "${project_id}" ]]; then
  printf 'Unable to extract the project id from %s\n' "${response_file}" >&2
  exit 1
fi

printf '%s\n' "${project_id}" > "${id_file}"
chmod 600 "${response_file}" "${id_file}"
printf 'Created OCI Generative AI project %s\n' "${project_id}"
