resource "azurerm_resource_group" "gateway" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_kubernetes_cluster" "gateway" {
  name                = var.cluster_name
  location            = azurerm_resource_group.gateway.location
  resource_group_name = azurerm_resource_group.gateway.name
  dns_prefix          = var.cluster_name

  # Free tier: the control plane carries no charge and no uptime SLA.
  # Correct for a cluster that is created for a demonstration and destroyed.
  sku_tier = "Free"

  default_node_pool {
    name       = "default"
    node_count = var.node_count
    vm_size    = var.vm_size

    # 32GB is the smallest managed disk AKS accepts. The default is 128GB,
    # which is billed per GB and never used by this workload.
    os_disk_size_gb = 32
  }

  # A managed identity avoids creating a service principal and storing its
  # secret in state. Azure creates and rotates it.
  identity {
    type = "SystemAssigned"
  }
}
