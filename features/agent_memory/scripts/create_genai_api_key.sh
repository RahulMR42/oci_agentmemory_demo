#!/usr/bin/env bash
set -euo pipefail

region="${1:?region is required}"
profile="${2:?oci cli profile is required}"
compartment_id="${3:?compartment ocid is required}"
display_name="${4:?api key display name is required}"
key_one_name="${5:?key one name is required}"
key_two_name="${6:?key two name is required}"
expiry_rfc3339="${7:?expiry timestamp is required}"
output_dir="${8:?output directory is required}"

response_file="${output_dir}/genai_api_key_response.json"
id_file="${output_dir}/genai_api_key_id.txt"
key_details_file="${output_dir}/genai_api_key_key_details.json"
key_value_file="${output_dir}/genai_api_key_value.txt"

if [[ -s "${id_file}" ]]; then
  printf 'Reusing generated API key id from %s\n' "${id_file}"
  exit 0
fi

cat > "${key_details_file}" <<EOF
[
  {
    "keyName": "${key_one_name}",
    "timeExpiry": "${expiry_rfc3339}"
  },
  {
    "keyName": "${key_two_name}",
    "timeExpiry": "${expiry_rfc3339}"
  }
]
EOF

tmp_file="$(mktemp)"
trap 'rm -f "${tmp_file}"' EXIT

oci generative-ai api-key create \
  --region "${region}" \
  --profile "${profile}" \
  --compartment-id "${compartment_id}" \
  --display-name "${display_name}" \
  --key-details "file://${key_details_file}" \
  --output json > "${tmp_file}"

mv "${tmp_file}" "${response_file}"

api_key_id="$(sed -n 's/^[[:space:]]*"id":[[:space:]]*"\([^"]*\)".*/\1/p' "${response_file}" | head -n 1)"
if [[ -z "${api_key_id}" ]]; then
  printf 'Unable to extract the API key id from %s\n' "${response_file}" >&2
  exit 1
fi

printf '%s\n' "${api_key_id}" > "${id_file}"

python3 - "${response_file}" "${key_one_name}" "${key_value_file}" <<'PY'
import json
import sys
from pathlib import Path

response_path = Path(sys.argv[1])
preferred_name = sys.argv[2]
output_path = Path(sys.argv[3])
data = json.loads(response_path.read_text(encoding="utf-8"))

preferred_paths = [
    ("data", "keyDetails", 0, "value"),
    ("data", "keyDetails", 0, "keyValue"),
    ("data", "keys", 0, "key"),
    ("data", "keys", 0, "value"),
    ("data", "keys", 0, "keyValue"),
    ("keyDetails", 0, "value"),
    ("keyDetails", 0, "keyValue"),
    ("keys", 0, "key"),
    ("keys", 0, "value"),
    ("keys", 0, "keyValue"),
]


def resolve_path(payload, path):
    node = payload
    for part in path:
        if isinstance(part, int):
            if not isinstance(node, list) or len(node) <= part:
                return None
            node = node[part]
            continue
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, str) and node.strip() else None


def walk(payload):
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from walk(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from walk(item)


for path in preferred_paths:
    value = resolve_path(data, path)
    if value:
        output_path.write_text(f"{value.strip()}\n", encoding="utf-8")
        raise SystemExit(0)

candidates = []
for obj in walk(data):
    if not isinstance(obj, dict):
        continue

    lowered = {str(key).lower(): value for key, value in obj.items()}
    key_name = None
    for field_name in ("keyname", "key_name", "name"):
        value = lowered.get(field_name)
        if isinstance(value, str):
            key_name = value
            break

    for key, value in obj.items():
        if not isinstance(value, str) or not value.strip():
            continue

        normalized = str(key).lower()
        if normalized in {
            "id",
            "displayname",
            "display_name",
            "lifecyclestate",
            "lifecycle_state",
            "compartmentid",
            "compartment_id",
            "timecreated",
            "time_created",
            "timeexpiry",
            "time_expiry",
            "description",
        }:
            continue

        score = 0
        if normalized in {"key", "keyvalue", "key_value", "secret", "secretvalue", "secret_value"}:
            score = 100
        elif normalized in {"token", "api_key", "apikey"}:
            score = 95
        elif normalized == "value":
            score = 90
        elif "secret" in normalized or "token" in normalized:
            score = 85
        elif "value" in normalized and "id" not in normalized:
            score = 80

        if score == 0:
            continue
        if key_name == preferred_name:
            score += 10
        candidates.append((score, value.strip()))

if candidates:
    candidates.sort(key=lambda item: item[0], reverse=True)
    output_path.write_text(f"{candidates[0][1]}\n", encoding="utf-8")
PY

chmod 600 "${response_file}" "${id_file}" "${key_details_file}"
if [[ -f "${key_value_file}" ]]; then
  chmod 600 "${key_value_file}"
fi

printf 'Created OCI Generative AI API key %s\n' "${api_key_id}"
if [[ -s "${key_value_file}" ]]; then
  printf 'Extracted the first API key secret into %s\n' "${key_value_file}"
else
  printf 'Inspect %s once and copy one returned key value into OCI_GENAI_API_KEY.\n' "${response_file}"
fi
