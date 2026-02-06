# Parler des 3 personas : 
- Data analyst -> lecture seule à une base, 0 accès ops manager
- App dev -> read/write sur base, pas de droits admin, accès lecture aux métriques ops manager 
- Platform / ops engineer -> 0 accès data, contrôle total sur le cluster : scale, upgrades, backups, automation

# Prereq
Les bases sur lesquelles les rôles sont configurées sont celles du folder 3-thalesradar-introMDB. 

# Création des rôles
Créer les roles dans Ops Manager : 

Rôle 1 : Data Analyst : observability read-only -> Rôle read sur observability demo 

Rôle 2 : radar_rw -> readWrite sur radar

# se logger en tant que data anlysts, et en tant que dev

mongodb://admin:pwd@localhost:27017/?authSource=admin&directConnection=true

## data analyst run commands
use observability
db.radar_metrics_ts.find()        // ✅ OK
db.orders.insertOne()   // ❌ forbidden
use admin               // ❌ forbidden

## dev run commands
use radar
db.radars.insertOne()   // ✅ OK
db.users.find()         // ❌ forbidden



# Démo RBAC Ops -> ça ça n'existe pas en community

## Rôles Ops Manager

Dans Ops Manager → Organization / Project - Project Users : 
- show the roles 
- explain that : Project Data Access Admin, Project Data Access Read/Write, Project Data Access Read Only are NOT mongoDB RBAC roles, but are ops manager data access (data explorer).

Rôle Ops 1 — Project Read-Only : View metrics, View alerts, No actions

Rôle Ops 2 — Project Automation Admin + Project Monitoring Admin + Project Backup Admin : Scale cluster, Modify automation, Trigger backups, No user management

# Se logger en tant que dev

Peut :
- voir CPU / RAM / ops/sec

Ne peut pas :
- scale le cluster
- modifier le replica set
- changer la config de sauvegarde

# se logger en tant qu'ops engineer 
tenter de modifier le replicaset 
