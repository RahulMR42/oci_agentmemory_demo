variable "feature_name" {
  description = "Base name used to build generated OCI resource names. Terraform appends a stable random 6-character suffix."
  type        = string
  default     = "agent-memory"
}

resource "random_string" "resource_name_suffix" {
  length  = 6
  upper   = false
  lower   = true
  numeric = true
  special = false
}

locals {
  generated_dir                        = "${path.module}/generated"
  project_id_file                      = "${local.generated_dir}/genai_project_id.txt"
  project_response_file                = "${local.generated_dir}/genai_project_response.json"
  api_key_id_file                      = "${local.generated_dir}/genai_api_key_id.txt"
  api_key_response_file                = "${local.generated_dir}/genai_api_key_response.json"
  api_key_value_file                   = "${local.generated_dir}/genai_api_key_value.txt"
  resource_name_suffix                 = random_string.resource_name_suffix.result
  effective_feature_name               = "${var.feature_name}-${local.resource_name_suffix}"
  effective_project_display_name       = "${var.project_display_name}-${local.resource_name_suffix}"
  effective_api_key_display_name       = "${var.api_key_display_name}-${local.resource_name_suffix}"
  effective_api_key_key_one_name       = "${var.api_key_key_one_name}-${local.resource_name_suffix}"
  effective_api_key_key_two_name       = "${var.api_key_key_two_name}-${local.resource_name_suffix}"
  effective_adb_display_name           = "${var.adb_display_name}-${local.resource_name_suffix}"
  effective_adb_db_name_suffix         = local.resource_name_suffix
  effective_adb_private_endpoint_label = "${var.adb_private_endpoint_label_prefix}${local.resource_name_suffix}"
  effective_policy_name                = "${local.effective_feature_name}-responses-api-key-policy"
}

resource "terraform_data" "inputs" {
  lifecycle {
    precondition {
      condition     = var.compartment_ocid != ""
      error_message = "Set compartment_ocid in terraform.tfvars or TF_VAR_compartment_ocid before running Terraform."
    }
  }
}

resource "terraform_data" "generated_dir" {
  depends_on = [terraform_data.inputs]

  provisioner "local-exec" {
    interpreter = ["bash", "-lc"]
    command     = "mkdir -p '${local.generated_dir}'"
  }
}

output "generated_dir" {
  description = "Directory containing generated project and API key artifacts."
  value       = local.generated_dir
}

output "resource_name_suffix" {
  description = "Stable random 6-character suffix appended to generated OCI resource names."
  value       = local.resource_name_suffix
}
