## If using private DNS - this is work in progress

ssh -i heleneom.pem -N \
  -L 27017:ip-172-31-32-140.eu-west-3.compute.internal:27017 \
  -L 27018:ip-172-31-38-83.eu-west-3.compute.internal:27017 \
  -L 27019:ip-172-31-32-235.eu-west-3.compute.internal:27017 \
  ec2-user@ec2-35-180-174-110.eu-west-3.compute.amazonaws.com

Test that the tunnel is open : 
nc -zv localhost 27017
nc -zv localhost 27018
nc -zv localhost 27019

mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=myReplicaSet