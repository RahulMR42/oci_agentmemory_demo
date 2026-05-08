variable "policy_compartment_ocid" {
  description = "Compartment OCID where the IAM policy should live. Leave blank to reuse compartment_ocid."
  type        = string
  default     = ""
}

variable "api_key_policy_group_name" {
  description = "Optional IAM group name to receive the runtime policy for the generated API key."
  type        = string
  default     = ""
}

locals {
  policy_compartment_id = var.policy_compartment_ocid != "" ? var.policy_compartment_ocid : var.compartment_ocid
}

resource "oci_identity_policy" "genai_api_key_runtime_policy" {
  count = var.api_key_policy_group_name == "" ? 0 : 1

  compartment_id = local.policy_compartment_id
  name           = local.effective_policy_name
  description    = "Allows the generated OCI Generative AI API key to call the Responses API."
  statements = [
    "allow group ${var.api_key_policy_group_name} to manage generative-ai-response in tenancy where ALL { request.principal.type='generativeaiapikey', request.principal.id='${trimspace(data.local_file.api_key_id.content)}' }",
  ]
}
