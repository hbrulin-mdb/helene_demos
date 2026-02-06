# az login
```sh
az login --tenant TENANTID
```
Select subscription id.

# cp terraform.tfvars.example terraform.tfvars

Edit the subscription id, edit the tenants. 
Leave ops_manager url and ops manager api key empty. 

# deploy
```sh
terraform init
terraform plan
terraform apply -target=module.aks
az aks get-credentials --resource-group aks-mongodb-rg --name aks-mongodb-cluster
terraform apply
```

# connect to cluster (optional, if not done before)
```sh
az aks get-credentials --resource-group aks-mongodb-rg --name aks-mongodb-cluster
```

# deploy ops manager

## Create the admin credentials secret
```sh
kubectl create secret generic ops-manager-admin-secret \
  -n opsmanager \
  --from-literal=Username=admin \
  --from-literal=Password=pwd \
  --from-literal=FirstName=Admin \
  --from-literal=LastName=User
```

## Deploy Ops Manager
```sh
kubectl apply -f manifests/ops-manager-deployment.yaml
```

## Check Ops Manager status
```sh
kubectl get opsmanagers -n opsmanager
```

(Note : I was able to continue the demo even when the state for opsmanager initially showed as failed for like 10 minutes)

## Watch the deployment (Ctrl+C to exit)
```sh
kubectl get pods -n opsmanager -w
```

## Get the Ops Manager external IP (once pods are running)
```sh
kubectl get svc -n opsmanager | grep ops-manager
```

# Access Ops Manager
Once Ops Manager is running, access it via external IP : 

```sh
kubectl get svc ops-manager-svc-ext -n opsmanager
```
Access at: http://IP:8080


# Create a new user from Ops Manager UI
username : admin
First Name : Admin
Last Name : User
mdp : motdepasse1234!

Smtp hostname : smtp.gmail.com
port : 465

#  Verify Deployments
## Check global MongoDB operator and Ops Manager namespace
```sh
kubectl get all -n opsmanager
```

## Check tenant namespaces
```sh
kubectl get namespaces | grep tenant-
```

## Check a specific tenant, including its per-tenant operator
```sh
kubectl get all -n tenant-thales
```

# Deploying MongoDB for a tenant
Once Ops Manager is running, deploy MongoDB instances into the tenant namespaces, not the opsmanager namespace.

## Create API Key in Ops Manager UI
Go to Admin → API Keys
Click Create API Key
Description: thales Operator
Permissions: Select Global Owner
Copy the Public Key and Private Key immediately. 

Important: Click Access List (or Manage Access List) for the key and add these CIDR blocks to allow internal cluster traffic:
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
104.30.164.0/28 -> CIDR for MongoDB VPN IPs. 

## Create Secret Replace YOUR_PUBLIC_KEY and YOUR_PRIVATE_KEY with the values you just copied, in a tenant you created (thales)
```sh
kubectl create secret generic thales-ops-manager-credentials \
  -n tenant-thales \
  --from-literal=user=YOUR_PUBLIC_KEY \
  --from-literal=publicApiKey=YOUR_PRIVATE_KEY
```

## Get Organization ID and Create ConfigMap

In Ops Manager: Administration → Organizations → Click org
Copy ID from URL (e.g., 6968ecc5067ea756a3d83ae2)

```sh
kubectl create configmap thales-ops-manager-config \
  -n tenant-thales \
  --from-literal=baseUrl=http://ops-manager-svc.opsmanager.svc.cluster.local:8080 \
  --from-literal=projectName=thales-project \
  --from-literal=orgId=696f49fa6d8c2f770c4821db
```

This creates a new project in the org.

## Apply file thales-mongodb.yaml

```sh
kubectl apply -f thales-mongodb.yaml
```
This creates a replicaset with version 8.0.10. 

## Monitor
```sh
kubectl describe mongodb thales-mongodb -n tenant-thales
kubectl get pods -n tenant-thales -w
```

Check Ops Manager UI: thales-projet - Deployments → Clusters

# Create database user

In Ops Manager, in thales project - Deployment → Security tab → Users.
Click Add User.
Create a user (e.g., Username: admin, Password: pwd).
Assign the root role (or appropriate permissions) for the admin database.
Click Add User.
Add my IP as well : 104.30.164.0/28
Click Review & Deploy at the top of the page to apply changes.

# Connect to Database 

To connect from your local machine, you must use port forwarding and specify directConnection=true to bypass replica set discovery (which would otherwise try to reach internal cluster IPs).

Start Port Forwarding:

```sh
kubectl port-forward svc/thales-mongodb-svc 27017:27017 -n tenant-thales
```

-> If not working, get the pod which runs the primary and 
```sh
kubectl port-forward -n tenant-thales pod/thales-mongodb-0 27017:27017
```

Note : run this to know the connectivity config of your cluster (ClusterIP, LB...) : 
```sh
kubectl get svc -n tenant-thales thales-mongodb-svc -o yaml | sed -n '1,120p'
```

Connect via Compass or mongosh: Use the following connection string (adjust credentials if you chose different ones):

mongodb://admin:pwd@localhost:27017/?authSource=admin&directConnection=true

# Pause and unpause the cluster

az aks stop --resource-group aks-mongodb-rg --name aks-mongodb-cluster

az aks start --resource-group aks-mongodb-rg --name aks-mongodb-cluster