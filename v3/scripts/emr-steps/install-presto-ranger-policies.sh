#!/bin/bash
set -euo pipefail
set -x
export JAVA_HOME=/usr/lib/jvm/java-openjdk
sudo -E bash -c 'echo $JAVA_HOME'
installpath=/usr/lib/ranger-pugins
ranger_server_fqdn=$1
default_domain=ec2.internal
hostname=`hostname -I | xargs`
hdfs_namenode_fqdn=$hostname
hive_server2_fqdn=$hostname
ranger_policybucket=$2

http_protocol=$3
if [ "$http_protocol" == "https" ]; then
  HTTP_URL=https://$ranger_server_fqdn:6182
else
  HTTP_URL=http://$ranger_server_fqdn:6080
fi

#Update repo/policies
sudo rm -rf $installpath
sudo mkdir -p $installpath
sudo chmod -R 777 $installpath
cd $installpath
aws s3 cp $ranger_policybucket . --recursive --exclude "*" --include "*.json" --region us-east-1
sudo sed -i "s|emr_masternode|$hdfs_namenode_fqdn|g" ranger-presto-repo.json
curl -iv --insecure -u admin:admin -d @ranger-presto-repo.json -H "Content-Type: application/json" -X POST $HTTP_URL/service/public/v2/api/service/
curl -iv --insecure -u admin:admin -d @ranger-presto-policy-general.json -H "Content-Type: application/json" -X POST $HTTP_URL/service/public/v2/api/policy/apply
curl -iv --insecure -u admin:admin -d @ranger-presto-policy-information-schema.json -H "Content-Type: application/json" -X POST $HTTP_URL/service/public/v2/api/policy/apply
curl -iv --insecure -u admin:admin -d @ranger-presto-policy-analyst1.json -H "Content-Type: application/json" -X POST $HTTP_URL/service/public/v2/api/policy/apply
curl -iv --insecure -u admin:admin -d @ranger-presto-policy-analyst2.json -H "Content-Type: application/json" -X POST $HTTP_URL/service/public/v2/api/policy/apply
