# Show how to pin FCV

Connect to each member to the admin db (use port forwarding for each pod) and run db.version() : 

Also check FCV: db.adminCommand({ getParameter: 1, featureCompatibilityVersion: 1 })

It’s recommended to be on the latest patch release for your major version before upgrades.

Check that they are both version 8.0. 

# Replace the content of thales-mongodb.yaml resource with the content of the upgrade yaml file (in filder upgradefiles)

```sh
kubectl apply -f thales-mongodb.yaml
```

- Watch events : 
```sh
kubectl -n tenant-thales get mongodb thales-mongodb -w 
```
- See messages : 
```sh
kubectl -n tenant-thales describe mongodb thales-mongodb
```
-> check for warning events at the bottom
- watch stateful set roll : 
```sh
kubectl -n tenant-thales get pods -l app=thales-mongodb -w
```

- Check db.version and fcv again, on the primary
The version is now upgrades, but not FCV. 

- Check other pods : 
```sh
kubectl port-forward -n tenant-thales pod/thales-mongodb-1 27017:27017
kubectl port-forward -n tenant-thales pod/thales-mongodb-2 27017:27017
```

- Update fcv in the thales-mongodb.yaml file and reapply (note : il faut mettre 8.2, pas 8.2.4)
```sh
kubectl apply -f thales-mongodb.yaml
```

