# modules/tenant-namespace/main.tf

# Create a namespace for each tenant
resource "kubernetes_namespace_v1" "tenant" {
  metadata {
    name = var.tenant_namespace
    
    labels = {
      tenant      = var.tenant_name
      environment = var.environment
      managed-by  = "terraform"
    }
    
    annotations = {
      "ops-manager-project" = var.ops_manager_project_id
    }
  }
}

# Create a secret in the tenant namespace with Ops Manager credentials
resource "kubernetes_secret" "ops_manager_connection" {
  metadata {
    name      = "ops-manager-connection"
    namespace = kubernetes_namespace_v1.tenant.metadata[0].name
  }

  type = "Opaque"

  data = {
    user              = base64encode(var.ops_manager_user)
    publicApiKey      = base64encode(var.ops_manager_public_key)
    baseUrl           = base64encode(var.ops_manager_url)
    orgId             = base64encode(var.ops_manager_org_id)
    projectId         = base64encode(var.ops_manager_project_id)
  }

  depends_on = [kubernetes_namespace_v1.tenant]
}

# Resource quotas for the tenant namespace
resource "kubernetes_resource_quota" "tenant_quota" {
  count = var.enable_resource_quota ? 1 : 0

  metadata {
    name      = "${var.tenant_name}-quota"
    namespace = kubernetes_namespace_v1.tenant.metadata[0].name
  }

  spec {
    hard = {
      "requests.cpu"    = var.cpu_quota
      "requests.memory" = var.memory_quota
      "requests.storage" = var.storage_quota
      "persistentvolumeclaims" = var.pvc_quota
      "pods"            = var.pods_quota
    }
  }

  depends_on = [kubernetes_namespace_v1.tenant]
}

# Limit ranges for the tenant namespace
resource "kubernetes_limit_range" "tenant_limits" {
  count = var.enable_limit_range ? 1 : 0

  metadata {
    name      = "${var.tenant_name}-limits"
    namespace = kubernetes_namespace_v1.tenant.metadata[0].name
  }

  spec {
    limit {
      type = "Container"
      
      default = {
        cpu    = var.default_cpu_limit
        memory = var.default_memory_limit
      }
      
      default_request = {
        cpu    = var.default_cpu_request
        memory = var.default_memory_request
      }
    }
  }

  depends_on = [kubernetes_namespace_v1.tenant]
}

# Network policy to isolate tenant namespace
resource "kubernetes_network_policy" "tenant_isolation" {
  count = var.enable_network_policy ? 1 : 0

  metadata {
    name      = "${var.tenant_name}-isolation"
    namespace = kubernetes_namespace_v1.tenant.metadata[0].name
  }

  spec {
    pod_selector {}
    
    policy_types = ["Ingress", "Egress"]

    # Allow ingress from same namespace
    ingress {
      from {
        pod_selector {}
      }
    }

    # Allow ingress from ops-manager namespace (matched by namespace name)
    ingress {
      from {
        namespace_selector {
          match_labels = {
            "kubernetes.io/metadata.name" = var.ops_manager_namespace
          }
        }
      }
    }

    # Allow egress to same namespace
    egress {
      to {
        pod_selector {}
      }
    }

    # Allow egress to ops-manager namespace (matched by namespace name)
    egress {
      to {
        namespace_selector {
          match_labels = {
            "kubernetes.io/metadata.name" = var.ops_manager_namespace
          }
        }
      }
    }

    # Allow egress to kube-dns
    egress {
      to {
        namespace_selector {
          match_labels = {
            name = "kube-system"
          }
        }
      }
      ports {
        port     = "53"
        protocol = "UDP"
      }
    }

    # Allow egress to external (for pulling images, etc.)
    egress {
      to {
        ip_block {
          cidr = "0.0.0.0/0"
          except = ["169.254.169.254/32"]
        }
      }
    }
  }

  depends_on = [kubernetes_namespace_v1.tenant]
}

# Service account for MongoDB deployments in tenant namespace
resource "kubernetes_service_account" "mongodb" {
  metadata {
    name      = "mongodb-service-account"
    namespace = kubernetes_namespace_v1.tenant.metadata[0].name
  }

  depends_on = [kubernetes_namespace_v1.tenant]
}

# Optional per-tenant MongoDB Enterprise Operator instance
resource "helm_release" "mongodb_enterprise_operator_tenant" {
  count            = var.deploy_mongodb_operator ? 1 : 0
  name             = "mongodb-enterprise-operator-${var.tenant_name}"
  repository       = "https://mongodb.github.io/helm-charts"
  chart            = "enterprise-operator"
  version          = var.kubernetes_operator_version
  namespace        = kubernetes_namespace_v1.tenant.metadata[0].name
  create_namespace = false

  values = [
    yamlencode({
      operator = {
        name       = "mongodb-enterprise-operator-${var.tenant_name}"
        # CRDs are installed once by the global operator module
        createCRDs = false
      }
    })
  ]

  depends_on = [kubernetes_namespace_v1.tenant]
}
