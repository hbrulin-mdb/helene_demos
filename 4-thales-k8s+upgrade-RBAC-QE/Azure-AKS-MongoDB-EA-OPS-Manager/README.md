# MongoDB Ops Manager on Azure AKS with Multi-Tenant Support

This Terraform configuration deploys:
1. **Azure Kubernetes Service (AKS)** cluster
2. **MongoDB Enterprise Operator** in the `opsmanager` namespace (for Ops Manager and global CRDs)
3. **MongoDB Ops Manager** (deployed via manifest in the `opsmanager` namespace)
4. **Tenant-specific namespaces** with isolation, resource quotas, and **per-tenant MongoDB operators**

## Version Compatibility

This project is configured to use:
- **MongoDB Kubernetes Operator**: Helm chart version 1.33.0 (latest)
- **MongoDB Ops Manager**: 8.0.0+
- **MongoDB Enterprise Server**: 8.0.10+ (required for operator compatibility)

**Note**: The Helm chart version (1.33.0) is different from the operator release tag. The Helm chart is continuously updated and the version number follows its own scheme.

## Architecture

```
AKS Cluster
├── opsmanager (namespace)
│   ├── MongoDB Enterprise Operator (global / Ops Manager)
│   └── MongoDB Ops Manager (deployed via Custom Resource)
├── tenant-<tenant-name> (namespace per tenant)
│   ├── Resource Quotas
│   ├── Network Policies (default-deny, allow Ops Manager + DNS + egress)
│   ├── Per-tenant MongoDB Enterprise Operator
│   └── MongoDB Deployments for that tenant
└── ... (additional tenant namespaces)
```

**Note**: The global operator in `opsmanager` installs CRDs and manages Ops Manager. Each tenant namespace gets its **own** MongoDB Enterprise Operator instance that only watches that namespace, providing stricter tenant isolation.

## Prerequisites

1. Azure CLI installed and authenticated
2. Terraform >= 1.5.0
3. kubectl installed
4. Helm 3.x installed

### Getting Your Azure Subscription ID

Before you begin, you'll need your Azure subscription ID. You can retrieve it using the Azure CLI:

```bash
# List all subscriptions
az account list -o table

# Or get just your current subscription ID
az account show --query id -o tsv
```

Copy the subscription ID and save it—you'll need it in the configuration step below.

## Quick Start

### 1. Configure Variables

Copy the example variables file:
```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and fill in your values:
- **subscription_id**: Your Azure subscription ID (see Prerequisites section above)
- **ops_manager_url**: URL for your MongoDB Ops Manager instance
- **ops_manager_api_key**: API key for Ops Manager authentication
- **tenants**: Configurations for each tenant with their Ops Manager projects

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Plan the Deployment

```bash
terraform plan
```

### 4. Deploy

Due to provider dependencies, deploy in two stages:

**Stage 1: Deploy AKS cluster first**
```bash
terraform apply -target=module.aks
```

**Stage 2: Deploy MongoDB Operator and Tenant Namespaces**
```bash
terraform apply
```

Alternatively, you can run a single apply and confirm twice when prompted.

### 5. Connect to the Cluster

```bash
az aks get-credentials --resource-group aks-mongodb-rg --name aks-mongodb-cluster
```

### 6. Deploy Ops Manager

Ops Manager is deployed as a Custom Resource in the `opsmanager` namespace (where the global operator watches):

```bash
# Create the admin credentials secret
kubectl create secret generic ops-manager-admin-secret \
  -n opsmanager \
  --from-literal=Username=admin \
  --from-literal=Password=your-secure-password \
  --from-literal=FirstName=Admin \
  --from-literal=LastName=User

# Deploy Ops Manager
kubectl apply -f manifests/ops-manager-deployment.yaml

# Check Ops Manager status
kubectl get opsmanagers -n opsmanager

# Watch the deployment (Ctrl+C to exit)
kubectl get pods -n opsmanager -w

# Get the Ops Manager external IP (once pods are running)
kubectl get svc -n opsmanager | grep ops-manager
```

**Note**: The global operator only watches the `opsmanager` namespace, so Ops Manager must be deployed there. Separate per-tenant operators watch each `tenant-<tenant-name>` namespace.

### Access Ops Manager

Once Ops Manager is running, you can access it in two ways:

**Option 1: Direct Access via LoadBalancer (if external IP is available)**
```bash
# Get the external IP
kubectl get svc ops-manager-svc-ext -n opsmanager

# Access at: http://<EXTERNAL-IP>:8080
```

**Option 2: Port Forward (if external IP is not available)**
```bash
# Forward local port 8080 to the Ops Manager service
kubectl port-forward svc/ops-manager-svc-ext 8080:8080 -n opsmanager

# In another terminal, access: http://localhost:8080
```

On first access, you'll be prompted to create the initial admin user. Set up your username and password through the web interface.

### 7. Verify Deployments

```bash
# Check global MongoDB operator and Ops Manager namespace
kubectl get all -n opsmanager

# Check tenant namespaces
kubectl get namespaces | grep tenant-

# Check a specific tenant, including its per-tenant operator
kubectl get all -n tenant-thales-corp
```

## Tenant Management

### Adding a New Tenant

1. Add a new entry to the `tenants` variable in `terraform.tfvars`:

```hcl
tenants = {
  # ... existing tenants ...
  
  "new-tenant" = {
    ops_manager_user       = "new-tenant-user"
    ops_manager_public_key = "new-tenant-api-key"
    ops_manager_org_id     = "new-tenant-org-id"
    ops_manager_project_id = "new-tenant-project-id"
    cpu_quota              = "15"
    memory_quota           = "30Gi"
    storage_quota          = "150Gi"
  }
}
```

2. Apply the changes:
```bash
terraform apply
```

### Removing a Tenant

1. Remove the tenant entry from `terraform.tfvars`
2. Apply the changes:
```bash
terraform apply
```

**Note:** This will delete the namespace and all resources within it!

## Tenant Isolation Features

Each tenant namespace includes:

### 1. Resource Quotas
- CPU limits
- Memory limits
- Storage limits
- Pod count limits
- PVC limits

### 2. Network Policies
- Isolated network traffic between tenants
- Allowed communication with Ops Manager namespace
- Allowed DNS resolution
- Allowed external egress for image pulls

### 3. Dedicated Resources
- Service account for MongoDB deployments
- Secret with Ops Manager connection details
- Limit ranges for default container resources

## Module Structure

```
.
├── main.tf                          # Root configuration
├── variables.tf                     # Input variables
├── outputs.tf                       # Output values
├── modules/
│   ├── aks/                        # AKS cluster module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── mongodb-operator/           # MongoDB Operator module
│   │   └── main.tf
│   ├── ops-manager/                # Ops Manager module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── tenant-namespace/           # Tenant namespace module
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── manifests/                       # Additional K8s manifests
```

## Deploying MongoDB for a Tenant

Once Ops Manager is running, deploy MongoDB instances into the **tenant namespaces**, not the `opsmanager` namespace.

### Quick Steps (Example: Air France)

**1. Create API Key** in Ops Manager UI
- Go to **Account Settings** → **API Keys**
- Click **Create API Key**
- Description: `thales Operator`
- Permissions: Select **Global Owner**
- **Copy** the Public Key and Private Key immediately
- **Important**: Click **Access List** (or Manage Access List) for the key and add these CIDR blocks to allow internal cluster traffic:
  - `10.0.0.0/8`
  - `172.16.0.0/12`
  - `192.168.0.0/16`

**2. Create Secret**
Replace `YOUR_PUBLIC_KEY` and `YOUR_PRIVATE_KEY` with the values you just copied:
```bash
kubectl create secret generic thales-ops-manager-credentials \
  -n tenant-thales \
  --from-literal=user=YOUR_PUBLIC_KEY \
  --from-literal=publicApiKey=YOUR_PRIVATE_KEY
```

**3. Get Organization ID and Create ConfigMap**
- In Ops Manager: **Administration** → **Organizations** → Click org
- Copy ID from URL (e.g., `6940126c889b3d5f048fb0c1`)

```bash
kubectl create configmap thales-ops-manager-config \
  -n tenant-thales \
  --from-literal=baseUrl=http://ops-manager-svc.opsmanager.svc.cluster.local:8080 \
  --from-literal=projectName=thales-project \
  --from-literal=orgId=YOUR_ORG_ID
```

**4. Deploy MongoDB**
```yaml
apiVersion: mongodb.com/v1
kind: MongoDB
metadata:
  name: thales-mongodb
  namespace: tenant-thales
spec:
  members: 3
  # Use a version present in Ops Manager's Version Manifest (Admin -> Version Manifest). For Ops Manager 8.0,
  # stick with 8.0.x (example below) unless you've imported a newer manifest.
  version: "8.0.10-ent"
  type: ReplicaSet
  opsManager:
    configMapRef:
      name: thales-ops-manager-config
  credentials: thales-ops-manager-credentials
  security:
    authentication:
      enabled: true
      modes: ["SCRAM"]
  persistent: true
  statefulSet:
    spec:
      volumeClaimTemplates:
        - metadata:
            name: data-volume
          spec:
            accessModes: ["ReadWriteOnce"]
            resources:
              requests:
                storage: 10Gi
```

Apply: `kubectl apply -f thales-mongodb.yaml`

**5. Monitor**
```bash
kubectl describe mongodb thales-mongodb -n tenant-thales
kubectl get pods -n tenant-thales -w
```

Check Ops Manager UI: **Deployments** → **Clusters**

**6. Create Database User**
1. In Ops Manager, go to **Deployment** → **Security** → **Users**.
2. Click **Add User**.
3. Select the **Air France** project (if not already selected).
4. Create a user (e.g., Username: `admin`, Password: `MongoDB`).
5. Assign the `root` role (or appropriate permissions) for the `admin` database.
6. Click **Add User**.
7. Click **Review & Deploy** at the top of the page to apply changes.

**7. Connect to Database**
To connect from your local machine, you must use port forwarding and specify `directConnection=true` to bypass replica set discovery (which would otherwise try to reach internal cluster IPs).

1. **Start Port Forwarding**:
   ```bash
   kubectl port-forward svc/thales-mongodb-svc 27017:27017 -n tenant-thales
   ```

2. **Connect via Compass or mongosh**:
   Use the following connection string (adjust credentials if you chose different ones):
   ```text
   mongodb://admin:MongoDB@localhost:27017/?authSource=admin&directConnection=true
   ```

## Monitoring

View resources across all tenant namespaces:

```bash
# All pods in tenant namespaces
kubectl get pods -A | grep tenant-

# Resource usage by namespace
kubectl top nodes
kubectl top pods -n tenant-thales-corp

# Check resource quotas
kubectl describe resourcequota -n tenant-thales-corp
```

## Security Best Practices

1. **Secrets Management**: Consider using Azure Key Vault for sensitive data
2. **RBAC**: Implement role-based access control per tenant
3. **Network Policies**: Review and adjust network policies based on requirements
4. **Resource Quotas**: Set appropriate limits based on tenant SLAs
5. **Backup**: Configure regular backups in Ops Manager

## Troubleshooting

### Check Ops Manager status and logs
```bash
# Check Ops Manager resource
kubectl get opsmanagers -n opsmanager
kubectl describe opsmanagers ops-manager -n opsmanager

# Check pods
kubectl get pods -n opsmanager

# Check logs
kubectl logs -n opsmanager -l app=ops-manager-db
```

### Check MongoDB Operator logs
```bash
kubectl logs -n opsmanager -l app=mongodb-enterprise-operator
```

### Verify tenant namespace resources
```bash
kubectl get all,secrets,configmaps -n tenant-thales-corp
```

### Check network policies
```bash
kubectl get networkpolicies -n tenant-thales-corp
kubectl describe networkpolicy -n tenant-thales-corp
```

## Clean Up

To destroy all resources:

```bash
terraform destroy
```

**Warning:** This will delete the AKS cluster and all data!

## Support

For issues or questions:
- MongoDB Enterprise Operator: https://github.com/mongodb/mongodb-enterprise-kubernetes
- MongoDB Ops Manager: https://docs.mongodb.com/ops-manager/current/
- Terraform AzureRM Provider: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs
