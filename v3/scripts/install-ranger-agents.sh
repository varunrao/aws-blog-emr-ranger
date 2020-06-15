#!/bin/bash
#set -euo pipefail
#set -x

isMasterInstance=$(cat /mnt/var/lib/info/instance.json | jq '.isMaster')
s3bucket=$1
s3_key=$2
ranger_host=$3
ranger_version=$4
target=$5

if [ "${isMasterInstance}" == "true" ];
then
    echo "Master instance. Setting up..."
    sudo sed "s|null \&|null \&\& hadoop fs -get s3://${s3bucket}/${s3_key}/scripts/emr-steps/install-hive-hdfs-ranger-plugin.sh \&\& hadoop fs -get s3://${s3bucket}/${s3_key}/scripts/emr-steps/download-scripts.sh \&\& hadoop fs -get s3://${s3bucket}/${s3_key}/scripts/emr-steps/install-hive-hdfs-ranger-policies.sh \&\& sed -i 's/\r//' install-hive-hdfs-ranger-plugin.sh \&\& bash install-hive-hdfs-ranger-plugin.sh $ranger_host $ranger_version $target \&\& bash install-hive-hdfs-ranger-policies.sh \&\& bash download-scripts.sh $target \&\n|g" /usr/share/aws/emr/node-provisioner/bin/provision-node > ~/provision-node.new
    sudo cp ~/provision-node.new /usr/share/aws/emr/node-provisioner/bin/provision-node
#    echo "alias restart='sudo stop hadoop-hdfs-namenode && sudo start hadoop-hdfs-namenode && sudo stop hive-server2 && sudo start hive-server2'" >> ~/.bash_profile
else
echo "Slave instance. Doing nothing..."
fi
