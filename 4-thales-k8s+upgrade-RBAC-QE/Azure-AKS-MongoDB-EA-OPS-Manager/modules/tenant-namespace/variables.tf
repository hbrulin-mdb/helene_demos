# modules/tenant-namespace/variables.tf

variable "tenant_name" {
  description = "Name of the tenant"
  type        = string
}

variable "tenant_namespace" {
  description = "Kubernetes namespace for the tenant (defaults to tenant-{tenant_name})"
  type        = string
}

variable "environment" {
  description = "Environment label (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "ops_manager_namespace" {
  description = "Namespace where Ops Manager is deployed"
  type        = string
  default     = "opsmanager"
}

variable "ops_manager_url" {
  description = "Ops Manager URL"
  type        = string
}

variable "ops_manager_user" {
  description = "Ops Manager user for this tenant"
  type        = string
  sensitive   = true
}

variable "ops_manager_public_key" {
  description = "Ops Manager public API key for this tenant"
  type        = string
  sensitive   = true
}

variable "ops_manager_org_id" {
  description = "Ops Manager organization ID"
  type        = string
}

variable "ops_manager_project_id" {
  description = "Ops Manager project ID for this tenant"
  type        = string
}

# Resource quota variables
variable "enable_resource_quota" {
  description = "Enable resource quotas for tenant namespace"
  type        = bool
  default     = true
}

variable "cpu_quota" {
  description = "CPU quota for tenant namespace"
  type        = string
  default     = "10"
}

variable "memory_quota" {
  description = "Memory quota for tenant namespace"
  type        = string
  default     = "20Gi"
}

variable "storage_quota" {
  description = "Storage quota for tenant namespace"
  type        = string
  default     = "100Gi"
}

variable "pvc_quota" {
  description = "Maximum number of PVCs in tenant namespace"
  type        = string
  default     = "10"
}

variable "pods_quota" {
  description = "Maximum number of pods in tenant namespace"
  type        = string
  default     = "20"
}

# Limit range variables
variable "enable_limit_range" {
  description = "Enable limit ranges for tenant namespace"
  type        = bool
  default     = true
}

variable "default_cpu_limit" {
  description = "Default CPU limit per container"
  type        = string
  default     = "1"
}

variable "default_memory_limit" {
  description = "Default memory limit per container"
  type        = string
  default     = "2Gi"
}

variable "default_cpu_request" {
  description = "Default CPU request per container"
  type        = string
  default     = "100m"
}

variable "default_memory_request" {
  description = "Default memory request per container"
  type        = string
  default     = "256Mi"
}

# Network policy variables
variable "enable_network_policy" {
  description = "Enable network policies for tenant isolation"
  type        = bool
  default     = true
}

# Per-tenant MongoDB operator deployment
variable "deploy_mongodb_operator" {
  description = "Deploy a MongoDB Enterprise Operator instance in this tenant namespace"
  type        = bool
  default     = true
}

variable "kubernetes_operator_version" {
  description = "MongoDB Kubernetes Operator Helm chart version to use for tenant operator"
  type        = string
  default     = "1.33.0"
}
