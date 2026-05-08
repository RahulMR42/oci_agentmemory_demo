variable "app_name" {
  description = "Display name used by the Streamlit app."
  type        = string
  default     = "OCI Agent Memory Workspace"
}

variable "agent_memory_mode" {
  description = "Runtime mode for the app. Use live."
  type        = string
  default     = "live"
}

variable "agent_memory_schema_policy" {
  description = "Schema policy for Oracle Agent Memory. Use create_if_necessary for automatic setup."
  type        = string
  default     = "create_if_necessary"
}

variable "oci_genai_chat_model" {
  description = "Responses API model used by the Streamlit app."
  type        = string
  default     = "openai.gpt-oss-120b"
}

output "app_name" {
  description = "Display name used by the Streamlit app."
  value       = var.app_name
}

output "agent_memory_mode" {
  description = "Configured runtime mode for the app."
  value       = var.agent_memory_mode
}

output "agent_memory_schema_policy" {
  description = "Schema policy used by Oracle Agent Memory."
  value       = var.agent_memory_schema_policy
}

output "oci_genai_region" {
  description = "OCI region used by the app."
  value       = var.region
}

output "oci_genai_chat_model" {
  description = "Responses API model used by the app."
  value       = var.oci_genai_chat_model
}
