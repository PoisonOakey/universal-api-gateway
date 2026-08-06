output "cluster_name" {
  description = "The name of the cluster"
  value       = azurerm_kubernetes_cluster.gateway.name
}

output "resource_group_name" {
  description = "The resource group holding every resource in this configuration"
  value       = azurerm_resource_group.gateway.name
}

output "kubectl_connect_command" {
  description = "Command to get credentials for the cluster"
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.gateway.name} --name ${azurerm_kubernetes_cluster.gateway.name}"
}
