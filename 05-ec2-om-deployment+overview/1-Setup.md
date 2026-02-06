
# aws cli
- I have added the --profile option in the scripts to use the new aws cli sso option, which relies on profiles. 
- see my profiles in home/.aws/config
- used profile : helene.brulin 

Reinit token
```sh
aws sso login --profile helene.brulin
```


Be careful with the EXPIREON params of the script and config.

# To change versions : 
- change ops manager version in launch_om : https://info-mongodb-com.s3.amazonaws.com/com-download-center/ops_manager_release_archive.json
- change mongodb version (APP_DB) in launch_om : https://repo.mongodb.org/yum/amazon/2023/mongodb-org : APP_VERSION=https://repo.mongodb.org/yum/amazon/2023/mongodb-org/8.2/x86_64/RPMS/mongodb-org-server-8.2.2-1.amzn2023.x86_64.rpm
- change the agent version in launch hosts : https://www.mongodb.com/docs/ops-manager/current/release-notes/mongodb-agent/#std-label-mongodb-agent-changelog


# lancer le script

```sh
./launch-om.sh
```
login : admin@localhost.com / abc_ABC1


# Navigate to Org, then to Project

Check in Deployment - servers, that you have the three VMs. 
Activate Monitoring and Backup on each server.

# Invitation
Go to profile > invitations and accept the invite to demo-project

# Activate App DB Monitoring - Optional

Enable Ops Manager App DB Monitoring (in Admin): choose Amazon Linux 2023 – RPM (x86_64)
-> follow instructions

To edit config file, connect to your machine. 
```sh
ssh -i "heleneom.pem" ec2-user@ec2-51-44-22-52.eu-west-3.compute.amazonaws.com
```

Note : The API key is generated in the instructions -> if missed, then go to API keys, delete, and regenerate from the agent installation instructions.

Then config the connection of the backing database:  "hostname -f" to find the host on the machine. 

127.0.0.1:27017 -> works.
(wouldn't be the case if f I had 3 machines behind an LB for Ops Manager)

