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
sudo sed -i "s|emr_masternode|$hdfs_namenode_fqdn|g" ranger-hdfs-repo.json
sudo sed -i "s|emr_masternode|$hive_server2_fqdn|g" ranger-hive-repo.json
curl -iv --insecure -u admin:admin -d @ranger-hdfs-repo.json -H "Content-Type: application/json" -X POST $HTTP_URL/service/public/api/repository/
curl -iv --insecure -u admin:admin -d @ranger-hive-repo.json -H "Content-Type: application/json" -X POST $HTTP_URL/service/public/api/repository/
curl -iv --insecure -u admin:admin -d @ranger-hdfs-policy-analyst1.json -H "Content-Type: application/json" -X POST $HTTP_URL/service/public/api/policy/
curl -iv --insecure -u admin:admin -d @ranger-hdfs-policy-analyst2.json -H "Content-Type: application/json" -X POST $HTTP_URL/service/public/api/policy/
curl -iv --insecure -u admin:admin -d @ranger-hive-policy-analyst1.json -H "Content-Type: application/json" -X POST $HTTP_URL/service/public/api/policy/
curl -iv --insecure -u admin:admin -d @ranger-hive-policy-analyst2.json -H "Content-Type: application/json" -X POST $HTTP_URL/service/public/api/policy/
curl -iv --insecure -u admin:admin -d @ranger-hive-policy-admin1.json -H "Content-Type: application/json" -X POST $HTTP_URL/service/public/api/policy/
