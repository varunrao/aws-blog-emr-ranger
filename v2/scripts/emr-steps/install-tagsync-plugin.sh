#!/bin/bash
set -euo pipefail
set -x
#Variables
export JAVA_HOME=/usr/lib/jvm/java-openjdk
sudo -E bash -c 'echo $JAVA_HOME'
installpath=/usr/lib/ranger
service=hadoop
ranger_fqdn=$1
#mysql_jar_location=http://central.maven.org/maven2/mysql/mysql-connector-java/5.1.39/mysql-connector-java-5.1.39.jar
mysql_jar=mysql-connector-java-5.1.39.jar
ranger_version=$2
s3bucket=$3
ranger_download_version=0.5
if [ "$ranger_version" == "2.0" ]; then
   ranger_download_version=2.1.0-SNAPSHOT
elif [ "$ranger_version" == "1.0" ]; then
   ranger_download_version=1.1.0
elif [ "$ranger_version" == "0.7" ]; then
   ranger_download_version=0.7.1
elif [ "$ranger_version" == "0.6" ]; then
   ranger_download_version=0.6.1
else
   ranger_download_version=0.5
fi

ranger_s3bucket=$s3bucket/ranger/ranger-$ranger_download_version
ranger_tagsync_plugin=ranger-$ranger_download_version-tagsync

#Setup
sudo rm -rf $installpath/$ranger_tagsync_plugin
sudo chmod -R 777 $installpath
cd $installpath
aws s3 cp $ranger_s3bucket/$ranger_tagsync_plugin.tar.gz . --region us-east-1
mkdir $ranger_tagsync_plugin
tar -xvf $ranger_tagsync_plugin.tar.gz -C $ranger_tagsync_plugin --strip-components=1
cd $installpath/$ranger_tagsync_plugin

## Updates for new Ranger
#Update Ranger URL in Tag sync conf
sudo sed -i "s|TAG_DEST_RANGER_ENDPOINT =.*|TAG_DEST_RANGER_ENDPOINT = http://$ranger_fqdn:6080|g" install.properties
sudo sed -i "s|TAG_SOURCE_ATLAS_ENABLED =.*|TAG_SOURCE_ATLAS_ENABLED = false|g" install.properties
sudo sed -i "s|TAG_SOURCE_FILE_ENABLED =.*|TAG_SOURCE_FILE_ENABLED = true|g" install.properties
sudo sed -i "s|TAG_SOURCE_FILE_CHECK_INTERVAL_IN_MILLIS =.*|TAG_SOURCE_FILE_CHECK_INTERVAL_IN_MILLIS = 30000|g" install.properties

aws s3 cp $s3bucket/inputdata/tags.json /etc/ranger/data/tags.json

sudo -E bash setup.sh

sudo /usr/bin/ranger-tagsync-services.sh stop || true
sudo /usr/bin/ranger-tagsync-services.sh start


#curl -iv -u admin:admin -d @tags.json -H "Content-Type: application/json" -X POST http://10.0.1.145:6080/service/tags/importservicetags/