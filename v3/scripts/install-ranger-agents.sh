#!/bin/bash
set -euo pipefail
set -x
isMasterInstance=$(cat /mnt/var/lib/info/instance.json | jq '.isMaster')
s3bucket=$1
s3_key=$2
if [ "${isMasterInstance}" == "true" ];
then
    echo "Master instance. Setting up..."
    sudo sed 's/null &/null \&\& hadoop fs -get s3:\/\/aws-bigdata-blog\/artifacts\/aws-blog-emr-ranger-v3\/scripts\/emr-steps\/install-hive-hdfs-ranger-plugin.sh \&\& hadoop fs -get s3:\/\/aws-bigdata-blog\/artifacts\/aws-blog-emr-ranger-v3\/scripts\/emr-steps\/install-hive-hdfs-ranger-policies.sh \&\& bash install-hive-hdfs-ranger-plugin.sh >> $STDOUT_LOG 2>> $STDERR_LOG \&\& bash install-hive-hdfs-ranger-policies.sh >> $STDOUT_LOG 2>> $STDERR_LOG \&\n/g' /usr/share/aws/emr/node-provisioner/bin/provision-node > ~/provision-node.new
    sudo cat ~/provision-node.new
    sudo cp ~/provision-node.new /usr/share/aws/emr/node-provisioner/bin/provision-node
else
    echo "Slave instance. Doing nothing..."
fi
