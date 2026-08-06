terraform {
  required_version = ">= 1.6"

  # Using local state as this is for a throwaway learning cluster
  # backend "local" {} (default)

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  subscription_id = var.subscription_id

  features {}
}
