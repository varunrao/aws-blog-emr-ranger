#!/bin/bash
set -euo pipefail
set -x
export JAVA_HOME=/usr/lib/jvm/java-openjdk
sudo -E bash -c 'echo $JAVA_HOME'
installpath=/usr/lib/presto/plugin
s3bucket=$1
version=0.227.1
athena_connector_s3bucket=$s3bucket/presto
athena_connector=presto-athena-$version-SNAPSHOT

#Setup
sudo rm -rf $installpath/athena
cd $installpath
#wget $mysql_jar_location
aws s3 cp $athena_connector_s3bucket/$athena_connector.zip . --region us-east-1
sudo unzip $athena_connector.zip -d .
sudo rm -rf $athena_connector.zip
mv $athena_connector athena
aws s3 cp $athena_connector_s3bucket/AthenaJDBC42_2.0.9.jar athena/ --region us-east-1
sudo chown -R presto:presto $installpath/athena
cd  /etc/presto/conf/catalog/
echo "connector.name=athena" >athena.properties
echo "connection-url=jdbc:awsathena://AwsRegion=us-east-1;LogLevel=6;LogPath=/tmp;AwsCredentialsProviderClass=com.simba.athena.amazonaws.auth.InstanceProfileCredentialsProvider;S3OutputLocation=s3://aws-datalake-security-data-vbhamidi-us-east-1/athena-output/" >>athena.properties
echo "connection-user=" >>athena.properties
echo "connection-password=" >>athena.properties
sudo puppet apply -e 'service { "presto-server": ensure => false, }'
sudo puppet apply -e 'service { "presto-server": ensure => true, }'
