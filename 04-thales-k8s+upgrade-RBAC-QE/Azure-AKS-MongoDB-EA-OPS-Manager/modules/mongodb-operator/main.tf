# modules/mongodb-operator/main.tf

variable "kubernetes_operator_version" {
  description = "MongoDB Kubernetes Operator Helm chart version"
  type        = string
  default     = "1.6.1"
}

resource "helm_release" "mongodb_enterprise_operator" {
  name             = "mongodb-enterprise-operator"
  repository       = "https://mongodb.github.io/helm-charts"
  chart            = "enterprise-operator"
  version          = var.kubernetes_operator_version
  namespace        = "opsmanager"
  create_namespace = true

  values = [
    yamlencode({
      operator = {
        name       = "mongodb-enterprise-operator"
        createCRDs = true
      }
    })
  ]
}