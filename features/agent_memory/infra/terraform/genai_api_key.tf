variable "api_key_display_name" {
  description = "Base display name for the OCI Generative AI API key. Terraform appends the shared random 6-character suffix."
  type        = string
  default     = "enterprise-agent-demo-api-key"
}

variable "api_key_key_one_name" {
  description = "Base friendly name for the first generated key value. Terraform appends the shared random 6-character suffix."
  type        = string
  default     = "primary"
}

variable "api_key_key_two_name" {
  description = "Base friendly name for the second generated key value. Terraform appends the shared random 6-character suffix."
  type        = string
  default     = "secondary"
}

variable "api_key_expiry_rfc3339" {
  description = "Shared expiry timestamp for both generated API keys."
  type        = string
  default     = "2030-12-31T23:59:59Z"
}

resource "terraform_data" "genai_api_key" {
  depends_on = [terraform_data.genai_project]

  triggers_replace = {
    region           = var.region
    profile          = var.oci_cli_profile
    compartment_ocid = var.compartment_ocid
    api_key_name     = local.effective_api_key_display_name
    key_one_name     = local.effective_api_key_key_one_name
    key_two_name     = local.effective_api_key_key_two_name
    api_key_expiry   = var.api_key_expiry_rfc3339
    api_key_id_file  = local.api_key_id_file
    api_key_payload  = local.api_key_response_file
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-lc"]
    command     = <<-EOT
      "${path.module}/../../scripts/create_genai_api_key.sh" \
        "${var.region}" \
        "${var.oci_cli_profile}" \
        "${var.compartment_ocid}" \
        "${local.effective_api_key_display_name}" \
        "${local.effective_api_key_key_one_name}" \
        "${local.effective_api_key_key_two_name}" \
        "${var.api_key_expiry_rfc3339}" \
        "${local.generated_dir}"
    EOT
  }
}

data "local_file" "api_key_id" {
  depends_on = [terraform_data.genai_api_key]
  filename   = local.api_key_id_file
}

output "genai_api_key_ocid" {
  description = "Generated OCI Generative AI API key OCID."
  value       = trimspace(data.local_file.api_key_id.content)
}

output "genai_api_key_value_file" {
  description = "Local file that contains the extracted API key secret used by the app."
  value       = local.api_key_value_file
}

output "genai_api_key_response_file" {
  description = "Local file that contains the one-time API key response payload."
  value       = local.api_key_response_file
}
