variable "region" {
  description = "OCI region for the Generative AI project and API key."
  type        = string
  default     = "us-chicago-1"
}

variable "compartment_ocid" {
  description = "Compartment where the OCI Generative AI project and API key will be created. Set this in terraform.tfvars or TF_VAR_compartment_ocid."
  type        = string
  default     = ""
}

variable "oci_cli_profile" {
  description = "OCI CLI profile used by the local-exec wrappers."
  type        = string
  default     = "DEFAULT"
}

variable "project_display_name" {
  description = "Base display name for the OCI Generative AI project. Terraform appends the shared random 6-character suffix."
  type        = string
  default     = "enterprise-agent-demo-project"
}

variable "project_description" {
  description = "Description for the OCI Generative AI project."
  type        = string
  default     = "Project for the enterprise agent demo feature"
}

resource "terraform_data" "genai_project" {
  depends_on = [terraform_data.generated_dir]

  triggers_replace = {
    region            = var.region
    profile           = var.oci_cli_profile
    compartment_ocid  = var.compartment_ocid
    project_name      = local.effective_project_display_name
    project_desc      = var.project_description
    project_id_file   = local.project_id_file
    project_json_file = local.project_response_file
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-lc"]
    command     = <<-EOT
      "${path.module}/../../scripts/create_genai_project.sh" \
        "${var.region}" \
        "${var.oci_cli_profile}" \
        "${var.compartment_ocid}" \
        "${local.effective_project_display_name}" \
        "${var.project_description}" \
        "${local.generated_dir}"
    EOT
  }
}

data "local_file" "project_id" {
  depends_on = [terraform_data.genai_project]
  filename   = local.project_id_file
}

output "genai_project_ocid" {
  description = "Generated OCI Generative AI project OCID."
  value       = trimspace(data.local_file.project_id.content)
}
