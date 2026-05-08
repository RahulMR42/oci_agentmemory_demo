# OCI Agent Memory Feature

First enterprise AI feature slice for the workspace. This folder owns the live Oracle Agent Memory service layer, UI, and OCI setup.

## How to run the app

Run these commands from the repository root.

For the default local startup flow:

```bash
./bash.sh start
```

The wrapper supports three modes:

- `./bash.sh start`: install dependencies if needed and start Streamlit with the existing `.env`
- `./bash.sh provision`: run Terraform, pull OCI plus DB-backed app settings into `.env`, and stop
- `./bash.sh up`: run Terraform, sync `.env`, then start Streamlit

On `start` or `up`, the wrapper also prepares the local demo login:

- `APP_DEMO_USERNAME` defaults to `oci`
- if `APP_DEMO_PASSWORD` is blank, `bash.sh` generates one, writes it to `.env`, and prints it in the terminal
- if you want a fixed password, export `APP_DEMO_PASSWORD` before starting or set it directly in `.env`

Minimal Terraform ask:

- If you export `TF_VAR_compartment_ocid`, you can run provisioning without creating `terraform.tfvars`.
- If you prefer a var file, the example now only requires `compartment_ocid` by default.
- Database passwords, wallet settings, connection string, and ADB naming can all stay on defaults.
- Terraform appends one stable random 6-character suffix to generated OCI resource names, so you only set base names in `terraform.tfvars`.

If you want the raw manual steps instead of the wrapper:

1. Activate the virtual environment:

   ```bash
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -e .
   ```

3. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

   If you are not using `bash.sh start`, set `APP_DEMO_PASSWORD` yourself before launching Streamlit.

4. Start the Streamlit UI:

   ```bash
   streamlit run streamlit_app.py
   ```

5. Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Runtime mode

- The Streamlit app now runs only against live OCI and Oracle AI Database resources.
- If required environment values are missing or the backend cannot start, the UI shows a setup blocker instead of a simulated mock experience.
- The UI is now a left-sidebar multi-page studio with clean OpenAI SDK and LangGraph chat workspaces.

## Terraform actions

Run these commands from the repository root.

1. Create your feature-specific Terraform variables file:

   ```bash
   cp features/agent_memory/infra/terraform/terraform.tfvars.example \
      features/agent_memory/infra/terraform/terraform.tfvars
   ```

2. Edit `features/agent_memory/infra/terraform/terraform.tfvars` with your OCI and database values.

   With the current defaults, the only required Terraform input is `compartment_ocid`.
   You can provide it either in `terraform.tfvars` or as:

   ```bash
   export TF_VAR_compartment_ocid=ocid1.compartment.oc1..replaceMe
   ```

   The Terraform variables now include the app runtime values consumed by Streamlit:

   - `agent_memory_mode`
   - `agent_memory_schema_policy`
   - `oci_genai_chat_model`
   - `agent_memory_llm_model`
   - `agent_memory_embedding_model`

   It also includes Autonomous Database and network controls such as:

   - `adb_display_name`
   - `adb_db_version`
   - `adb_compute_count`
   - `adb_connection_service_level`
   - `adb_enable_private_endpoint`
   - `adb_vcn_cidr`
   - `adb_subnet_cidr`
   - `adb_client_cidr`

   Resource-name related inputs such as `feature_name`, `project_display_name`, `api_key_display_name`, `api_key_key_one_name`, `api_key_key_two_name`, `adb_display_name`, `adb_db_name_prefix`, and `adb_private_endpoint_label_prefix` are treated as base values. Terraform appends a shared random 6-character suffix automatically.

3. Initialize Terraform:

   ```bash
   terraform -chdir=features/agent_memory/infra/terraform init
   ```

4. Review the plan:

   ```bash
   terraform -chdir=features/agent_memory/infra/terraform plan
   ```

5. Apply the stack:

   ```bash
   terraform -chdir=features/agent_memory/infra/terraform apply
   ```

6. If you need to remove the Terraform-managed IAM policy state later:

   ```bash
   terraform -chdir=features/agent_memory/infra/terraform destroy
   ```

## Important behavior

- This Terraform uses `local-exec` scripts to call the OCI CLI for project and API key creation, rather than managing those two resources as native Terraform resources.
- Terraform generates one random 6-character suffix per stack and appends it to the OCI project name, API key names, IAM policy name, VCN/subnet/NSG display names, Autonomous Database display name, Autonomous Database DB name, and private endpoint label.
- Terraform now creates a real Autonomous Database, wallet artifacts, and a supporting VCN/subnet/NSG layout.
- `bash.sh` now resolves the generated wallet directory into the runtime env and extracts the OCI API key from the OCI response payload field used by the current API.
- Oracle Agent Memory now defaults to `create_if_necessary`, so the managed schema objects are created automatically when the app connects with a privileged database account such as `ADMIN`.
- The Autonomous Database defaults to a public endpoint so the local Streamlit app can connect with the generated wallet. Set `adb_enable_private_endpoint = true` if you want the database attached to the provisioned subnet and NSG instead.
- The Autonomous Database and VCN resources are normal OCI infrastructure and can incur cost.
- `terraform destroy` deletes the Terraform-managed Autonomous Database, wallet artifacts, network resources, and optional IAM policy.
- `terraform destroy` does not delete the generated OCI Generative AI project or API key, because those are still created by OCI CLI wrapper scripts.
- The creation scripts reuse existing IDs from `features/agent_memory/infra/terraform/generated/` if those files already exist.
- Because the project and API key wrappers reuse cached IDs, name changes only affect those resources when Terraform is creating them from scratch. If you need a fresh OCI project or API key with a new suffixed name, remove the generated ID files deliberately before reapplying.
- The API-key creation script now tries to extract the first returned key secret into `features/agent_memory/infra/terraform/generated/genai_api_key_value.txt` so `bash.sh` can start the app without a second manual copy step.
- The wallet zip and extracted wallet directory are generated under `features/agent_memory/infra/terraform/generated/`.
- If you need a brand new OCI project or API key, do not assume `apply` will rotate them automatically. You will need to clean up the generated files and handle OCI-side deletion or replacement deliberately.

## What Terraform sets up

- OCI Generative AI project creation for the feature
- OCI Generative AI API key creation
- Autonomous Database provisioning for the feature
- VCN, subnet, route table, internet gateway, and NSG resources for the database
- Optional IAM policy support for API-key based runtime access
- Local generated artifacts under `features/agent_memory/infra/terraform/generated/`

## Map Terraform outputs into the app

After `terraform apply`, `./bash.sh provision` or `./bash.sh up` will write `.env` automatically from Terraform outputs and generated artifacts.

If you want to inspect the mapped values manually, the resulting env shape is:

```bash
APP_DEMO_USERNAME=oci
APP_DEMO_PASSWORD=<generated on first ./bash.sh start unless you preset it>

OCI_GENAI_REGION=<terraform region>
OCI_GENAI_PROJECT_OCID=<generated project id>
OCI_GENAI_API_KEY=<copy one key value from generated api key response>

AGENT_MEMORY_SCHEMA_POLICY=create_if_necessary
AGENT_MEMORY_DB_USER=ADMIN
AGENT_MEMORY_DB_PASSWORD=<generated or overridden autonomous db admin password>
AGENT_MEMORY_DB_DSN=<generated autonomous db service connection string>
AGENT_MEMORY_WALLET_DIR=<generated extracted wallet directory>
AGENT_MEMORY_WALLET_PASSWORD=<generated or overridden wallet password>
```

## What the demo covers

- A left-rail multi-page Streamlit studio
- A direct OpenAI SDK page using the current `responses.create()` path against OCI
- A LangGraph page using a live `StateGraph` orchestration flow
- Oracle Agent Memory integration path through the `oracleagentmemory` Python library
- Retrieved memory, thread summary, context-card inspection, progress tracking, and backend logs for each live turn

## Folder structure

```text
features/agent_memory/
  infra/terraform/
    app.tf
    bootstrap.tf
    database.tf
    genai_api_key.tf
    genai_project.tf
    network.tf
    policies.tf
    providers.tf
    terraform.tfvars.example
    versions.tf
  scripts/
  templates/agent_memory/
  router.py
  service.py
```

## Required values for the live workspace

- `APP_DEMO_USERNAME` defaults to `oci`
- `APP_DEMO_PASSWORD` is required at runtime but generated automatically by `bash.sh start` if missing
- `OCI_GENAI_REGION`
- `OCI_GENAI_PROJECT_OCID`
- `OCI_GENAI_API_KEY`
- `AGENT_MEMORY_DB_USER`
- `AGENT_MEMORY_DB_PASSWORD`
- `AGENT_MEMORY_DB_DSN`
- `AGENT_MEMORY_WALLET_DIR`
- `AGENT_MEMORY_WALLET_PASSWORD`

## Official references used for this starter

- Oracle blog: <https://blogs.oracle.com/developers/oracle-ai-agent-memory-a-governed-unified-memory-core-for-enterprise-ai-agents>
- Oracle Agent Memory docs: <https://docs.oracle.com/en/database/oracle/agent-memory/26.4/agmea/index.html>
- Oracle Agent Memory get started: <https://docs.oracle.com/en/database/oracle/agent-memory/26.4/agmea/get-started.html>
- OCI Responses API: <https://docs.oracle.com/en-us/iaas/Content/generative-ai/responses-api.htm>
- OCI Generative AI API keys: <https://docs.oracle.com/en-us/iaas/Content/generative-ai/api-keys.htm>
- OCI Generative AI projects: <https://docs.oracle.com/en-us/iaas/Content/generative-ai/projects.htm>
- LangGraph reference: <https://reference.langchain.com/python/langgraph/>
