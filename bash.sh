#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
TF_DIR="${ROOT_DIR}/features/agent_memory/infra/terraform"
TF_VARS_FILE="${TF_VARS_FILE:-${TF_DIR}/terraform.tfvars}"
GENERATED_DIR="${TF_DIR}/generated"
APP_ENV_FILE="${ROOT_DIR}/.env"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8501}"
SKIP_INSTALL="${SKIP_INSTALL:-0}"
TF_AUTO_APPROVE="${TF_AUTO_APPROVE:-0}"

COMMAND="${1:-start}"

cd "${ROOT_DIR}"

usage() {
  cat <<'EOF'
Usage:
  ./bash.sh start      Install deps if needed and start the Streamlit app.
  ./bash.sh provision  Run Terraform for OCI + DB-backed app config and sync .env.
  ./bash.sh up         Run Terraform, sync .env, then start the Streamlit app.

Environment overrides:
  HOST=127.0.0.1
  PORT=8501
  SKIP_INSTALL=0
  TF_AUTO_APPROVE=0
  APP_DEMO_USERNAME=oci
  APP_DEMO_PASSWORD=<optional preset password>
  TF_VARS_FILE=features/agent_memory/infra/terraform/terraform.tfvars
  TF_VAR_compartment_ocid=ocid1.compartment.oc1..replaceMe
EOF
}

ensure_venv() {
  if [[ ! -d "${VENV_DIR}" ]]; then
    python3 -m venv "${VENV_DIR}"
  fi
}

activate_venv() {
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
}

install_dependencies() {
  if [[ "${SKIP_INSTALL}" != "1" ]]; then
    python -m pip install -e .
  fi
}

ensure_terraform_inputs() {
  if [[ -f "${TF_VARS_FILE}" || -n "${TF_VAR_compartment_ocid:-}" ]]; then
    return
  fi

  if [[ -f "${TF_DIR}/terraform.tfvars.example" ]]; then
    cp "${TF_DIR}/terraform.tfvars.example" "${TF_VARS_FILE}"
    printf 'Created %s from the example file.\n' "${TF_VARS_FILE}"
    printf 'Set compartment_ocid in that file or export TF_VAR_compartment_ocid before rerunning.\n'
    exit 1
  fi

  printf 'Set TF_VAR_compartment_ocid or provide a Terraform var file at %s.\n' "${TF_VARS_FILE}" >&2
  exit 1
}

terraform_state_exists() {
  [[ -f "${TF_DIR}/terraform.tfstate" ]]
}

terraform_output_raw() {
  local name="${1:?output name is required}"
  terraform -chdir="${TF_DIR}" output -raw "${name}"
}

resolve_tf_path() {
  local value="${1:-}"
  if [[ -z "${value}" || "${value}" == /* ]]; then
    printf '%s' "${value}"
    return
  fi

  printf '%s/%s' "${TF_DIR}" "${value#./}"
}

extract_generated_api_key() {
  local key_value_file="${GENERATED_DIR}/genai_api_key_value.txt"
  local response_file="${GENERATED_DIR}/genai_api_key_response.json"

  if [[ -s "${key_value_file}" ]]; then
    tr -d '\r' < "${key_value_file}"
    return 0
  fi

  if [[ ! -s "${response_file}" ]]; then
    return 1
  fi

  python3 - "${response_file}" <<'PY'
import json
import sys
from pathlib import Path

response_path = Path(sys.argv[1])
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
        print(value.strip())
        raise SystemExit(0)

candidates = []
for obj in walk(data):
    if not isinstance(obj, dict):
        continue
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

        if score:
            candidates.append((score, value.strip()))

if not candidates:
    raise SystemExit(1)

candidates.sort(key=lambda item: item[0], reverse=True)
print(candidates[0][1])
PY
}

env_file_has_populated_value() {
  local key="${1:?env key is required}"
  [[ -f "${APP_ENV_FILE}" ]] || return 1

  local value
  value="$(sed -n "s/^${key}=//p" "${APP_ENV_FILE}" | tail -n 1)"
  [[ -n "${value}" ]]
}

env_file_value() {
  local key="${1:?env key is required}"
  [[ -f "${APP_ENV_FILE}" ]] || return 1

  sed -n "s/^${key}=//p" "${APP_ENV_FILE}" | tail -n 1
}

env_file_needs_refresh() {
  [[ -f "${APP_ENV_FILE}" ]] || return 0

  local required_keys=(
    OCI_GENAI_PROJECT_OCID
    OCI_GENAI_API_KEY
    AGENT_MEMORY_SCHEMA_POLICY
    AGENT_MEMORY_DB_USER
    AGENT_MEMORY_DB_PASSWORD
    AGENT_MEMORY_DB_DSN
    AGENT_MEMORY_WALLET_DIR
    AGENT_MEMORY_WALLET_PASSWORD
  )

  local key
  for key in "${required_keys[@]}"; do
    if ! env_file_has_populated_value "${key}"; then
      return 0
    fi
  done

  return 1
}

upsert_env_value() {
  local key="${1:?env key is required}"
  local value="${2:-}"

  python3 - "${APP_ENV_FILE}" "${key}" "${value}" <<'PY'
from pathlib import Path
import sys

env_path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]

lines = []
if env_path.exists():
    lines = env_path.read_text(encoding="utf-8").splitlines()

updated = False
for index, line in enumerate(lines):
    if line.startswith(f"{key}="):
        lines[index] = f"{key}={value}"
        updated = True
        break

if not updated:
    lines.append(f"{key}={value}")

env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
}

generate_random_password() {
  python3 - <<'PY'
import secrets

print(secrets.token_urlsafe(16))
PY
}

ensure_demo_credentials() {
  [[ -f "${APP_ENV_FILE}" ]] || return

  local demo_username demo_password

  demo_username="${APP_DEMO_USERNAME:-$(env_file_value APP_DEMO_USERNAME || true)}"
  if [[ -z "${demo_username}" ]]; then
    demo_username="oci"
  fi
  upsert_env_value APP_DEMO_USERNAME "${demo_username}"

  if [[ -n "${APP_DEMO_PASSWORD:-}" ]]; then
    upsert_env_value APP_DEMO_PASSWORD "${APP_DEMO_PASSWORD}"
    return
  fi

  if env_file_has_populated_value APP_DEMO_PASSWORD; then
    return
  fi

  demo_password="$(generate_random_password)"
  upsert_env_value APP_DEMO_PASSWORD "${demo_password}"
  printf 'Generated demo login for the Streamlit workspace.\n'
  printf '  user: %s\n' "${demo_username}"
  printf '  password: %s\n' "${demo_password}"
}

repair_env_file_from_generated_artifacts() {
  [[ -f "${APP_ENV_FILE}" ]] || return

  local api_key wallet_dir

  local demo_username

  upsert_env_value APP_NAME "OCI Agent Memory Workspace"
  demo_username="${APP_DEMO_USERNAME:-$(env_file_value APP_DEMO_USERNAME || true)}"
  if [[ -z "${demo_username}" ]]; then
    demo_username="oci"
  fi
  upsert_env_value APP_DEMO_USERNAME "${demo_username}"
  upsert_env_value AGENT_MEMORY_MODE "live"
  upsert_env_value AGENT_MEMORY_SCHEMA_POLICY "create_if_necessary"

  if ! env_file_has_populated_value OCI_GENAI_API_KEY; then
    api_key="$(extract_generated_api_key || true)"
    if [[ -n "${api_key}" ]]; then
      upsert_env_value OCI_GENAI_API_KEY "${api_key}"
    fi
  fi

  wallet_dir="$(resolve_tf_path "./generated/agent_memory_wallet")"
  if [[ -d "${wallet_dir}" ]]; then
    upsert_env_value AGENT_MEMORY_WALLET_DIR "${wallet_dir}"
  fi
}

sync_env_from_terraform() {
  if ! terraform_state_exists; then
    printf 'Terraform state not found under %s. Run ./bash.sh provision first.\n' "${TF_DIR}" >&2
    return 1
  fi

  local app_name
  local app_demo_username
  local app_demo_password
  local agent_memory_mode
  local agent_memory_schema_policy
  local oci_genai_region
  local oci_genai_project_ocid
  local oci_genai_api_key
  local oci_genai_chat_model
  local agent_memory_db_user
  local agent_memory_db_password
  local agent_memory_db_dsn
  local agent_memory_wallet_dir
  local agent_memory_wallet_password
  local agent_memory_llm_model
  local agent_memory_embedding_model

  app_demo_username="${APP_DEMO_USERNAME:-$(env_file_value APP_DEMO_USERNAME || true)}"
  if [[ -z "${app_demo_username}" ]]; then
    app_demo_username="oci"
  fi
  app_demo_password="${APP_DEMO_PASSWORD:-$(env_file_value APP_DEMO_PASSWORD || true)}"
  app_name="$(terraform_output_raw app_name)"
  agent_memory_mode="$(terraform_output_raw agent_memory_mode)"
  agent_memory_schema_policy="$(terraform_output_raw agent_memory_schema_policy)"
  oci_genai_region="$(terraform_output_raw oci_genai_region)"
  oci_genai_project_ocid="$(terraform_output_raw genai_project_ocid)"
  oci_genai_api_key="$(extract_generated_api_key || true)"
  oci_genai_chat_model="$(terraform_output_raw oci_genai_chat_model)"
  agent_memory_db_user="$(terraform_output_raw agent_memory_db_user)"
  agent_memory_db_password="$(terraform_output_raw agent_memory_db_password)"
  agent_memory_db_dsn="$(terraform_output_raw agent_memory_db_dsn)"
  agent_memory_wallet_dir="$(resolve_tf_path "$(terraform_output_raw agent_memory_wallet_dir)")"
  agent_memory_wallet_password="$(terraform_output_raw agent_memory_wallet_password)"
  agent_memory_llm_model="$(terraform_output_raw agent_memory_llm_model)"
  agent_memory_embedding_model="$(terraform_output_raw agent_memory_embedding_model)"

  cat > "${APP_ENV_FILE}" <<EOF
APP_NAME=${app_name}
APP_DEMO_USERNAME=${app_demo_username}
APP_DEMO_PASSWORD=${app_demo_password}
AGENT_MEMORY_MODE=${agent_memory_mode}
AGENT_MEMORY_SCHEMA_POLICY=${agent_memory_schema_policy}

OCI_GENAI_REGION=${oci_genai_region}
OCI_GENAI_PROJECT_OCID=${oci_genai_project_ocid}
OCI_GENAI_API_KEY=${oci_genai_api_key}
OCI_GENAI_CHAT_MODEL=${oci_genai_chat_model}

AGENT_MEMORY_DB_USER=${agent_memory_db_user}
AGENT_MEMORY_DB_PASSWORD=${agent_memory_db_password}
AGENT_MEMORY_DB_DSN=${agent_memory_db_dsn}
AGENT_MEMORY_WALLET_DIR=${agent_memory_wallet_dir}
AGENT_MEMORY_WALLET_PASSWORD=${agent_memory_wallet_password}
AGENT_MEMORY_LLM_MODEL=${agent_memory_llm_model}
AGENT_MEMORY_EMBEDDING_MODEL=${agent_memory_embedding_model}
EOF

  chmod 600 "${APP_ENV_FILE}"
  printf 'Wrote %s from Terraform outputs.\n' "${APP_ENV_FILE}"

  if [[ -z "${oci_genai_api_key}" ]]; then
    printf 'Warning: OCI_GENAI_API_KEY is blank. Inspect %s and update %s if the key could not be extracted automatically.\n' \
      "${GENERATED_DIR}/genai_api_key_response.json" \
      "${APP_ENV_FILE}" >&2
  fi
}

run_terraform() {
  local tf_args=()

  ensure_terraform_inputs
  if [[ -f "${TF_VARS_FILE}" ]]; then
    tf_args+=("-var-file=${TF_VARS_FILE}")
  fi
  terraform -chdir="${TF_DIR}" init
  terraform -chdir="${TF_DIR}" plan "${tf_args[@]}"

  if [[ "${TF_AUTO_APPROVE}" == "1" ]]; then
    terraform -chdir="${TF_DIR}" apply -auto-approve "${tf_args[@]}"
  else
    terraform -chdir="${TF_DIR}" apply "${tf_args[@]}"
  fi

  sync_env_from_terraform
}

ensure_env_file() {
  if terraform_state_exists && env_file_needs_refresh; then
    sync_env_from_terraform || true
  fi

  if [[ ! -f "${APP_ENV_FILE}" && -f "${ROOT_DIR}/.env.example" ]]; then
    cp "${ROOT_DIR}/.env.example" "${APP_ENV_FILE}"
  fi

  repair_env_file_from_generated_artifacts
  ensure_demo_credentials

  if [[ -f "${APP_ENV_FILE}" ]]; then
    return
  fi
}

start_streamlit() {
  ensure_venv
  activate_venv
  install_dependencies
  ensure_env_file
  exec streamlit run streamlit_app.py --server.address "${HOST}" --server.port "${PORT}"
}

case "${COMMAND}" in
  start)
    start_streamlit
    ;;
  provision)
    run_terraform
    ;;
  up)
    run_terraform
    start_streamlit
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    printf 'Unknown command: %s\n\n' "${COMMAND}" >&2
    usage >&2
    exit 1
    ;;
esac
