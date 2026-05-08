terraform {
  required_version = ">= 1.5.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = ">= 2.5.1"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6.0"
    }
    oci = {
      source  = "oracle/oci"
      version = ">= 7.0.0"
    }
  }
}
