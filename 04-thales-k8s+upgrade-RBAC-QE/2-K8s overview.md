# Show the UI
- Processes
- Servers : les pods. 

# Show the deploument 

```sh
kubectl get pods -n opsmanager -w
```

This shows : 
- the operator which manages mongodb enterprise resources
- the ops manager app pod (UI + API) -> this can be a satefulset if needed
- the ops manager backing db, which is itself a replicaset,statefulsetbased, a db which stored the metadata for the cluster, oplog, backups...  -> 2/2 (each pod has two containers, usually mongod + sidecar/monitoring agent)

```sh
kubectl get pods -n tenant-thales -w
```
This shows : 
- the operator for mongodb thales tenant project : manages resources in this namespace
- the replicaset of the cluster, stetfulset based, one mongodb process per pod

To see which pods are on which VMs : 
```sh
for p in $(kubectl get pod -n tenant-thales -o name); do
  node=$(kubectl get $p -n tenant-thales -o jsonpath='{.spec.nodeName}')
  pool=$(kubectl get node "$node" -o jsonpath='{.metadata.labels.kubernetes\.azure\.com/agentpool}')
  echo "$p  ->  $node  (pool=$pool)"
done
```

# Go to the overview of the RS, show primary and replica
# Show real time panel
# Show metrics 
# Show data explorer
# Show profiler
# Show performance advisor
# Show activation of TLS in Dpeloyment - Security Settings

# Encryption at rest

Prereq : A KMIP-compatible KMS reachable from all database hosts (examples: Thales/Gemalto, HashiCorp Vault KMIP, Entrust). Ensure network access, mutual TLS certificates, and firewall rules.

Go to deployment - processes - modfiy on the replicaset
Advanced configuration option : 
- Add the security.enableEncryption: true and the KMIP block shown above (one by one)
- add KMIP config - one param at a time
```sh
  kmip:
    serverName: "kms.example.com"
    port: 5696
    serverCAFile: "/path/to/ca.pem"
    clientCertificateFile: "/path/to/client.pem"
    # optionally keyIdentifier if using a specific key
```
- Save and deploy changes

Ops Manager will update the automation config to include the encryption settings and restart the processes accordingly.

Note : KMIP manages the CMK, MongoDB generates and rotates the DEK.

# On the same page, show the read and write concerns & replication settings 

# Check la partie Admin d'Ops Manager

# Other 
## show node pool list

```sh
az aks nodepool list \
  --resource-group aks-mongodb-rg \
  --cluster-name aks-mongodb-cluster \
  -o table
```

# show details for one node pool : default

```sh
az aks nodepool show -g aks-mongodb-rg --cluster-name aks-mongodb-cluster -n default --query "{name:name, mode:mode, count:count, vmSize:vmSize, kubeVersion:orchestratorVersion, enableAS:enableAutoScaling, min:minCount, max:maxCount, maxPods:maxPods, osType:osType, osSku:osSku, labels:nodeLabels, taints:nodeTaints}"  -o yaml
```

In AKS, count is the number of node VMs in that node pool