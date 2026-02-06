# main.tf
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

module "aks" {
  source = "./modules/aks"
  
  created_by  = var.created_by
  expired_on  = var.expired_on
  environment = var.environment

  cluster_name              = var.cluster_name
  ops_manager_allowed_cidrs = var.ops_manager_allowed_cidrs
  
  # Pass any required variables here
  # resource_group_name = var.resource_group_name
  # cluster_name        = var.cluster_name
  # location            = var.location
}

# Connect to the AKS cluster we are about to create
provider "kubernetes" {
  host                   = try(module.aks.host, null)
  client_certificate     = try(base64decode(module.aks.client_certificate), null)
  client_key             = try(base64decode(module.aks.client_key), null)
  cluster_ca_certificate = try(base64decode(module.aks.cluster_ca_certificate), null)
}

provider "helm" {
  kubernetes {
    host                   = try(module.aks.host, null)
    client_certificate     = try(base64decode(module.aks.client_certificate), null)
    client_key             = try(base64decode(module.aks.client_key), null)
    cluster_ca_certificate = try(base64decode(module.aks.cluster_ca_certificate), null)
  }
}

# Deploy MongoDB Enterprise Operator in its own namespace
module "mongodb_operator" {
  source = "./modules/mongodb-operator"
  
  kubernetes_operator_version = var.kubernetes_operator_version
  
  depends_on = [module.aks]
}

# Create tenant namespaces dynamically
module "tenant_namespace" {
  source   = "./modules/tenant-namespace"
  for_each = var.tenants

  tenant_name               = each.key
  tenant_namespace          = "tenant-${each.key}"
  environment               = var.environment
  ops_manager_namespace     = "opsmanager"
  ops_manager_url           = var.ops_manager_url
  ops_manager_user          = each.value.ops_manager_user
  ops_manager_public_key    = each.value.ops_manager_public_key
  ops_manager_org_id        = each.value.ops_manager_org_id
  ops_manager_project_id    = each.value.ops_manager_project_id
  
  # Resource quotas
  cpu_quota                 = lookup(each.value, "cpu_quota", "10")
  memory_quota              = lookup(each.value, "memory_quota", "20Gi")
  storage_quota             = lookup(each.value, "storage_quota", "100Gi")
  kubernetes_operator_version = var.kubernetes_operator_version
  
  depends_on = [module.mongodb_operator]
}
