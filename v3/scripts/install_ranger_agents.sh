#!/bin/bash

isMasterInstance=$(cat /mnt/var/lib/info/instance.json | jq '.isMaster')
s3bucket_http_url=$1
scripts_s3bucket=$s3bucket_http_url/scripts/emr-steps/
if [ "${isMasterInstance}" == "true" ];
then
    echo "Master instance. Setting up..."
    sudo sed "s/null &/null \&\&
                hadoop fs -get s3:\/\/${scripts_s3bucket}\/install-hive-hdfs-ranger-plugin.sh \&\&
                hadoop fs -get s3:\/\/${scripts_s3bucket}\/install-hive-hdfs-ranger-policies.sh \&\&
                bash install-hive-hdfs-ranger-plugin.sh \&\& bash install-hive-hdfs-ranger-policies.sh>> $STDOUT_LOG 2>> $STDERR_LOG \&\n/" /usr/share/aws/emr/node-provisioner/bin/provision-node > ~/provision-node.new
    sudo cp ~/provision-node.new /usr/share/aws/emr/node-provisioner/bin/provision-node
else
    echo "Slave instance. Doing nothing..."
fi
