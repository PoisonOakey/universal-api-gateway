variable "subscription_id" {
  description = "The Azure subscription ID to create resources in. No default, so it cannot be committed by accident."
  type        = string
}

variable "location" {
  description = "The Azure region. Southeast Asia is Singapore, the closest region to Malaysia."
  type        = string
  default     = "southeastasia"
}

variable "resource_group_name" {
  description = "Name of the resource group holding every resource in this configuration. Deleting it removes everything."
  type        = string
  default     = "gateway-rg"
}

variable "cluster_name" {
  description = "The name of the AKS cluster"
  type        = string
  default     = "gateway-cluster"
}

variable "node_count" {
  description = "Number of nodes in the node pool"
  type        = number
  default     = 2
}

variable "vm_size" {
  description = <<-EOT
    VM size for the nodes. Standard_DC2s_v3 is not the obvious choice: the
    B, D and F families are restricted on trial subscriptions in every
    region, and the DC family is one of the few AKS accepts. At 2 vCPUs a
    node, two nodes exactly fill the 4 vCPU regional quota.
  EOT
  type        = string
  default     = "Standard_DC2s_v3"
}
