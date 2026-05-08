# Security Notes

This repository is intended to be safe to share without local credentials or generated infrastructure artifacts.

## Do Not Commit

- `.env`
- `.venv/`
- `*.egg-info/`
- `__pycache__/`
- Terraform state files
- `terraform.tfvars`
- `features/agent_memory/infra/terraform/generated/`
- OCI API-key response files
- OCI API-key secret value files
- Autonomous Database wallet zips or extracted wallet folders

## Before Opening a PR

Run a local scan for sensitive values:

```bash
rg -n -i "password|api[_-]?key|secret|fingerprint|private|ocid1|BEGIN .*PRIVATE|wallet|tenancy|token" \
  --glob '!*.gif' \
  --glob '!*.mp4' \
  --glob '!*.pyc' \
  --glob '!__pycache__/**' \
  --glob '!.venv/**' \
  --glob '!features/agent_memory/infra/terraform/generated/**' \
  --glob '!features/agent_memory/infra/terraform/terraform.tfstate*' \
  --glob '!features/agent_memory/infra/terraform/terraform.tfvars' \
  .
```

Expected hits should be placeholders, environment variable names, documentation text, or code references only.

## Runtime Secrets

Keep OCI and database credentials in local environment variables, OCI CLI configuration, or `.env`. Do not place real secret values in Markdown, Terraform examples, screenshots, videos, or generated artifacts committed to Git.
