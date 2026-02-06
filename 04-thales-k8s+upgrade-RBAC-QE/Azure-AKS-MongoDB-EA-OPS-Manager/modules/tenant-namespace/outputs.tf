# modules/tenant-namespace/outputs.tf

output "namespace" {
  description = "Tenant namespace name"
  value       = kubernetes_namespace_v1.tenant.metadata[0].name
}

output "tenant_name" {
  description = "Tenant name"
  value       = var.tenant_name
}

output "ops_manager_secret_name" {
  description = "Name of the secret containing Ops Manager connection details"
  value       = kubernetes_secret.ops_manager_connection.metadata[0].name
}

output "service_account_name" {
  description = "Name of the MongoDB service account"
  value       = kubernetes_service_account.mongodb.metadata[0].name
}
