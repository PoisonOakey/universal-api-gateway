terraform {
  required_version = ">= 1.6"

  # Using local state as this is for a throwaway learning cluster
  # backend "local" {} (default)

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}
