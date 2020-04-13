#!/bin/bash
set -euo pipefail
set -x
#Variables
export JAVA_HOME=/usr/lib/jvm/java-openjdk
sudo -E bash -c 'echo $JAVA_HOME'
installpath=/usr/lib/ranger
#mysql_jar_location=http://central.maven.org/maven2/mysql/mysql-connector-java/5.1.39/mysql-connector-java-5.1.39.jar
#mysql_jar=mysql-connector-java-5.1.39.jar
ranger_fqdn=$1
ranger_version=$2
s3bucket=$3

ranger_download_version=0.5
if [ "$ranger_version" == "2.0" ]; then
   ranger_download_version=2.1.0-SNAPSHOT
elif [ "$ranger_version" == "1.0" ]; then
   ranger_download_version=1.2.1-SNAPSHOT
elif [ "$ranger_version" == "0.7" ]; then
   ranger_download_version=0.7.1
elif [ "$ranger_version" == "0.6" ]; then
   ranger_download_version=0.6.1
else
   ranger_download_version=0.5
fi

ranger_s3bucket=$s3bucket/ranger/ranger-$ranger_download_version
ranger_s3_plugin=ranger-$ranger_download_version-s3-plugin

#Setup
sudo rm -rf $installpath/s3
sudo mkdir -p $installpath/s3
sudo chmod -R 777 $installpath
cd $installpath/s3
#wget $mysql_jar_location
aws s3 cp $s3bucket/emrfs/emrfs-s3-authz-1.0.jar . --region us-east-1
sudo mkdir -p /usr/share/aws/emr/emrfs/lib/
sudo mkdir -p /usr/share/aws/emr/emrfs/conf/
#sudo cp emrfs-hadoop-assembly-2.38.0.jar /usr/share/aws/emr/emrfs/lib/emrfs-hadoop-assembly-2.38.0.jar
sudo cp emrfs-s3-authz-1.0.jar /usr/share/aws/emr/emrfs/lib/

aws s3 cp $ranger_s3bucket/$ranger_s3_plugin.tar.gz . --region us-east-1
sudo mkdir $ranger_s3_plugin
sudo tar -xvf $ranger_s3_plugin.tar.gz -C $ranger_s3_plugin --strip-components=1
cd $installpath/s3/$ranger_s3_plugin


sudo cp lib/* /usr/share/aws/emr/emrfs/lib/
sudo sed -i "s|ranger_host|$ranger_fqdn|g" install/conf/ranger-awss3-audit.xml
sudo sed -i "s|ranger_host|$ranger_fqdn|g" install/conf/ranger-awss3-security.xml
sudo sed -i "s|service_name|awss3dev|g" install/conf/ranger-awss3-security.xml
sudo cp install/conf/* /usr/share/aws/emr/emrfs/conf/
sudo chmod -R 777 /usr/share/aws/emr/emrfs/conf/
sudo chmod -R 777 /usr/share/aws/emr/emrfs/lib/
sudo mkdir -p /var/log/emr-awss3/
sudo touch /var/log/emr-awss3/awss3.log || true
sudo chmod 777 /var/log/emr-awss3/awss3.log || true
sudo mkdir -p /etc/ranger/awss3/policycache/ || true
sudo chmod -R 777 /etc/ranger/awss3/ || true
