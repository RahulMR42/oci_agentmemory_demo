variable "adb_vcn_cidr" {
  description = "CIDR block for the Autonomous Database VCN."
  type        = string
  default     = "10.42.0.0/16"
}

variable "adb_subnet_cidr" {
  description = "CIDR block for the Autonomous Database subnet."
  type        = string
  default     = "10.42.10.0/24"
}

variable "adb_client_cidr" {
  description = "CIDR block allowed to reach the private Autonomous Database endpoint over SQL*Net and HTTPS."
  type        = string
  default     = "10.42.0.0/16"
}

variable "adb_vcn_dns_label" {
  description = "DNS label for the Autonomous Database VCN."
  type        = string
  default     = "agmemvcn"
}

variable "adb_subnet_dns_label" {
  description = "DNS label for the Autonomous Database subnet."
  type        = string
  default     = "adbsubnet"
}

variable "adb_enable_private_endpoint" {
  description = "When true, attach the Autonomous Database to the provisioned subnet and NSG using a private endpoint."
  type        = bool
  default     = false
}

variable "adb_private_endpoint_label_prefix" {
  description = "Base prefix used to generate the Autonomous Database private endpoint label. Terraform appends the shared random 6-character suffix."
  type        = string
  default     = "agmemadb"
}

resource "oci_core_vcn" "adb" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = [var.adb_vcn_cidr]
  display_name   = "${local.effective_feature_name}-vcn"
  dns_label      = var.adb_vcn_dns_label
}

resource "oci_core_internet_gateway" "adb" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.adb.id
  display_name   = "${local.effective_feature_name}-igw"
  enabled        = true
}

resource "oci_core_route_table" "adb" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.adb.id
  display_name   = "${local.effective_feature_name}-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.adb.id
  }
}

resource "oci_core_subnet" "adb_subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.adb.id
  cidr_block                 = var.adb_subnet_cidr
  display_name               = "${local.effective_feature_name}-subnet"
  dns_label                  = var.adb_subnet_dns_label
  route_table_id             = oci_core_route_table.adb.id
  prohibit_public_ip_on_vnic = true
}

resource "oci_core_network_security_group" "adb_private_endpoint_nsg" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.adb.id
  display_name   = "${local.effective_feature_name}-adb-nsg"
}

resource "oci_core_network_security_group_security_rule" "adb_private_endpoint_ingress_sqlnet" {
  network_security_group_id = oci_core_network_security_group.adb_private_endpoint_nsg.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = var.adb_client_cidr
  source_type               = "CIDR_BLOCK"
  description               = "Allow SQL*Net access to the Autonomous Database private endpoint."

  tcp_options {
    destination_port_range {
      min = 1522
      max = 1522
    }
  }
}

resource "oci_core_network_security_group_security_rule" "adb_private_endpoint_ingress_https" {
  network_security_group_id = oci_core_network_security_group.adb_private_endpoint_nsg.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = var.adb_client_cidr
  source_type               = "CIDR_BLOCK"
  description               = "Allow HTTPS access to Database Actions and other private-endpoint web surfaces."

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "adb_private_endpoint_egress_all" {
  network_security_group_id = oci_core_network_security_group.adb_private_endpoint_nsg.id
  direction                 = "EGRESS"
  protocol                  = "all"
  destination               = "0.0.0.0/0"
  destination_type          = "CIDR_BLOCK"
  description               = "Allow outbound traffic from the Autonomous Database private endpoint."
}

output "adb_vcn_id" {
  description = "VCN OCID for the Autonomous Database network."
  value       = oci_core_vcn.adb.id
}

output "adb_subnet_id" {
  description = "Subnet OCID for the Autonomous Database network."
  value       = oci_core_subnet.adb_subnet.id
}

output "adb_private_endpoint_nsg_id" {
  description = "NSG OCID used for the Autonomous Database private endpoint."
  value       = oci_core_network_security_group.adb_private_endpoint_nsg.id
}
