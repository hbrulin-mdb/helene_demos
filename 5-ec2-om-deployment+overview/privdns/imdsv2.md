# run the following if machines show up as localhost in OM (and therefore it displays only one tracked server)

```sh
echo "PRIVATE_HOSTNAME=[$(curl -s http://169.254.169.254/latest/meta-data/local-hostname)]"
curl -s -o /dev/null -w "%{http_code}\n" http://169.254.169.254/latest/meta-data/local-hostname
```

If you see 401, you need IMDSv2.

Fix : 

```sh
TOKEN=$(curl -sX PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

PRIVATE_HOSTNAME=$(curl -sH "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/local-hostname)

echo "Will set hostname to: $PRIVATE_HOSTNAME"

sudo hostnamectl set-hostname "$PRIVATE_HOSTNAME"
sudo hostname "$PRIVATE_HOSTNAME"   # sets transient immediately (belt + suspenders)
sudo systemctl restart mongodb-mms-automation-agent

hostname
```
-> should display : ip-172-31-xx-yy.eu-west-3.compute.internal