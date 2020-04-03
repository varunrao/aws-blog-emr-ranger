#!/bin/bash
set -euo pipefail
set -x
sudo yum -y install java-1.8.0
sudo yum -y remove java-1.7.0-openjdk
sudo yum -y install krb5-workstation krb5-libs krb5-auth-dialog

export JAVA_HOME=/usr/lib/jvm/jre
# Define variables
hostname=`hostname -I | xargs`
installpath=/usr/lib/ranger
ranger_version=$5
s3bucket_http_url=$6
db_host_name=$7
db_root_password=$8
ldap_admin_user=$9
ldap_admin_password=${10}
ranger_download_version=0.5
if [ "$ranger_version" == "2.0" ]; then
   ranger_download_version=2.1.0-SNAPSHOT
elif [ "$ranger_version" == "1.0" ]; then
   ranger_download_version=1.0.1
elif [ "$ranger_version" == "0.7" ]; then
   ranger_download_version=0.7.1
elif [ "$ranger_version" == "0.6" ]; then
   ranger_download_version=0.6.1
else
   ranger_download_version=0.5
fi

ranger_s3bucket=$s3bucket_http_url/ranger/ranger-$ranger_download_version
ranger_admin_server=ranger-$ranger_download_version-admin
ranger_user_sync=ranger-$ranger_download_version-usersync

mysql_jar_location=$s3bucket_http_url/ranger/ranger-$ranger_download_version/mysql-connector-java-5.1.39.jar
mysql_jar=mysql-connector-java-5.1.39.jar

ldap_ip_address=$1
ldap_server_url=ldap://$ldap_ip_address
ldap_base_dn=$2
ldap_bind_user_dn=$3
ldap_bind_password=$4
# Setup
yum install -y openldap openldap-clients openldap-servers
# Setup LDAP users
aws s3 cp $s3bucket_http_url/inputdata/load-users-new.ldf .
aws s3 cp $s3bucket_http_url/inputdata/modify-users-new.ldf .
aws s3 cp $s3bucket_http_url/scripts/create-users-using-ldap.sh .
chmod +x create-users-using-ldap.sh
./create-users-using-ldap.sh $ldap_ip_address $ldap_admin_user $ldap_admin_password $ldap_base_dn || true
#Install mySQL
yum -y install mysql-server
service mysqld start
chkconfig mysqld on
mysqladmin -u root password rangeradmin || true
rm -rf $installpath
mkdir -p $installpath/hadoop
cd $installpath
aws s3 cp $ranger_s3bucket/$ranger_admin_server.tar.gz .
aws s3 cp $ranger_s3bucket/$ranger_user_sync.tar.gz .
aws s3 cp $mysql_jar_location .
aws s3 cp $ranger_s3bucket/solr_for_audit_setup.tar.gz .
#Update ranger admin install.properties
mkdir $ranger_admin_server
tar -xvf $ranger_admin_server.tar.gz -C $ranger_admin_server --strip-components=1

cd $ranger_admin_server

sudo sed -i "s|SQL_CONNECTOR_JAR=.*|SQL_CONNECTOR_JAR=$installpath/$mysql_jar|g" install.properties

DB_ROOT_USERNAME="root"

RDS_RANGER_SCHEMA_DBNAME="rangerdb"
RDS_RANGER_SCHEMA_DBUSER="rangeradmin"
RDS_RANGER_SCHEMA_DBPASSWORD="rangeradmin"

MYSQL="/usr/bin/mysql"

_generateSQLGrantsAndCreateUser()
{
    touch ~/generate_grants.sql
    HOSTNAMEI=`hostname -I`
    HOSTNAMEI=`echo ${HOSTNAMEI}`
    cat >~/generate_grants.sql <<EOF
CREATE USER IF NOT EXISTS '${RDS_RANGER_SCHEMA_DBUSER}'@'localhost' IDENTIFIED BY '${RDS_RANGER_SCHEMA_DBPASSWORD}';
GRANT ALL PRIVILEGES ON \`%\`.* TO '${RDS_RANGER_SCHEMA_DBUSER}'@'localhost';
CREATE USER IF NOT EXISTS '${RDS_RANGER_SCHEMA_DBUSER}'@'%' IDENTIFIED BY '${RDS_RANGER_SCHEMA_DBPASSWORD}';
GRANT ALL PRIVILEGES ON \`%\`.* TO '${RDS_RANGER_SCHEMA_DBUSER}'@'%';
CREATE USER IF NOT EXISTS '${RDS_RANGER_SCHEMA_DBUSER}'@'${HOSTNAMEI}' IDENTIFIED BY '${RDS_RANGER_SCHEMA_DBPASSWORD}';
GRANT ALL PRIVILEGES ON \`%\`.* TO '${RDS_RANGER_SCHEMA_DBUSER}'@'${HOSTNAMEI}';
GRANT ALL PRIVILEGES ON \`%\`.* TO '${RDS_RANGER_SCHEMA_DBUSER}'@'${HOSTNAMEI}' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON \`%\`.* TO '${RDS_RANGER_SCHEMA_DBUSER}'@'localhost' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON \`%\`.* TO '${RDS_RANGER_SCHEMA_DBUSER}'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
exit
EOF

}
_setupMySQLDatabaseAndPrivileges()
{
    HOSTNAMEI=`hostname -I`
    ${MYSQL} -h ${db_host_name} -u ${DB_ROOT_USERNAME} -p${db_root_password} < ~/generate_grants.sql
    echo $?
}

_generateSQLGrantsAndCreateUser
_setupMySQLDatabaseAndPrivileges

sudo sed -i "s|db_root_user=.*|db_root_user=${DB_ROOT_USERNAME}|g" install.properties
sudo sed -i "s|db_root_password=.*|db_root_password=${db_root_password}|g" install.properties
sudo sed -i "s|db_host=.*|db_host=${db_host_name}|g" install.properties
sudo sed -i "s|db_name=.*|db_name=${RDS_RANGER_SCHEMA_DBNAME}|g" install.properties
sudo sed -i "s|db_user=.*|db_user=${RDS_RANGER_SCHEMA_DBUSER}|g" install.properties
sudo sed -i "s|db_password=.*|db_password=${RDS_RANGER_SCHEMA_DBPASSWORD}|g" install.properties
sudo sed -i "s|audit_db_password=.*|audit_db_password=rangerlogger|g" install.properties

## Update log4j to debug
sudo sed -i "s|info|debug|g" ews/webapp/WEB-INF/log4j.properties


sudo sed -i "s|audit_store=.*|audit_store=solr|g" install.properties
sudo sed -i "s|audit_solr_urls=.*|audit_solr_urls=http://localhost:8983/solr/ranger_audits|g" install.properties
sudo sed -i "s|policymgr_external_url=.*|policymgr_external_url=http://$hostname:6080|g" install.properties
#Update LDAP properties
sudo sed -i "s|authentication_method=.*|authentication_method=LDAP|g" install.properties
sudo sed -i "s|xa_ldap_url=.*|xa_ldap_url=$ldap_server_url|g" install.properties
sudo sed -i "s|xa_ldap_userDNpattern=.*|xa_ldap_userDNpattern=uid={0},cn=users,$ldap_base_dn|g" install.properties
sudo sed -i "s|xa_ldap_groupSearchBase=.*|xa_ldap_groupSearchBase=$ldap_base_dn|g" install.properties
sudo sed -i "s|xa_ldap_groupSearchFilter=.*|xa_ldap_groupSearchFilter=objectclass=group|g" install.properties
sudo sed -i "s|xa_ldap_groupRoleAttribute=.*|xa_ldap_groupRoleAttribute=cn|g" install.properties
sudo sed -i "s|xa_ldap_base_dn=.*|xa_ldap_base_dn=$ldap_base_dn|g" install.properties
sudo sed -i "s|xa_ldap_bind_dn=.*|xa_ldap_bind_dn=$ldap_bind_user_dn|g" install.properties
sudo sed -i "s|xa_ldap_bind_password=.*|xa_ldap_bind_password=$ldap_bind_password|g" install.properties
sudo sed -i "s|xa_ldap_referral=.*|xa_ldap_referral=ignore|g" install.properties
sudo sed -i "s|xa_ldap_userSearchFilter=.*|xa_ldap_userSearchFilter=(sAMAccountName={0})|g" install.properties

#Kerberos properties
sudo sed -i "s|admin_principal=.*|admin_principal=awsadmin@AWSEMR.COM)|g" install.properties
sudo sed -i "s|admin_keytab=.*|admin_keytab=/etc/awsadmin.keytab|g" install.properties
sudo sed -i "s|lookup_principal=.*|lookup_principal=awsadmin@AWSEMR.COM|g" install.properties
sudo sed -i "s|lookup_keytab=.*|lookup_keytab=/etc/awsadmin.keytab|g" install.properties


chmod +x setup.sh
./setup.sh
#Update ranger usersync install.properties
cd $installpath
mkdir $ranger_user_sync
tar -xvf $ranger_user_sync.tar.gz -C $ranger_user_sync --strip-components=1
cp ./$ranger_admin_server/ews/webapp/WEB-INF/lib/jackson-* ./$ranger_user_sync/lib/
chown ranger:ranger ./$ranger_user_sync/lib/*
chmod 755 ./$ranger_user_sync/lib/*

cd $ranger_user_sync


sudo sed -i "s|POLICY_MGR_URL =.*|POLICY_MGR_URL=http://$hostname:6080|g" install.properties
sudo sed -i "s|SYNC_SOURCE =.*|SYNC_SOURCE=ldap|g" install.properties
sudo sed -i "s|SYNC_LDAP_URL =.*|SYNC_LDAP_URL=$ldap_server_url|g" install.properties
sudo sed -i "s|SYNC_LDAP_BIND_DN =.*|SYNC_LDAP_BIND_DN=$ldap_bind_user_dn|g" install.properties
sudo sed -i "s|SYNC_LDAP_BIND_PASSWORD =.*|SYNC_LDAP_BIND_PASSWORD=$ldap_bind_password|g" install.properties


sudo sed -i "s|SYNC_LDAP_SEARCH_BASE =.*|SYNC_LDAP_SEARCH_BASE=$ldap_base_dn|g" install.properties
sudo sed -i "s|SYNC_LDAP_USER_SEARCH_BASE =.*|SYNC_LDAP_USER_SEARCH_BASE=$ldap_base_dn|g" install.properties
sudo sed -i "s|SYNC_LDAP_USER_SEARCH_FILTER =.*|SYNC_LDAP_USER_SEARCH_FILTER=sAMAccountName=*|g" install.properties
sudo sed -i "s|SYNC_LDAP_USER_NAME_ATTRIBUTE =.*|SYNC_LDAP_USER_NAME_ATTRIBUTE=sAMAccountName|g" install.properties
sudo sed -i "s|SYNC_INTERVAL =.*|SYNC_INTERVAL=2|g" install.properties
chmod +x setup.sh
./setup.sh
#Download the install solr for ranger
cd $installpath
mkdir solr_for_audit_setup
tar -xvf solr_for_audit_setup.tar.gz -C solr_for_audit_setup --strip-components=1
cd solr_for_audit_setup
sudo sed -i "s|SOLR_HOST_URL=.*|SOLR_HOST_URL=http://$hostname:8983|g" install.properties
sudo sed -i "s|SOLR_RANGER_PORT=.*|SOLR_RANGER_PORT=8983|g" install.properties
sudo sed -i "s|SOLR_MAX_MEM=.*|SOLR_MAX_MEM=4g|g" install.properties
sed -i 's/+90DAYS/+2DAYS/g' conf/solrconfig.xml
chmod +x setup.sh
./setup.sh
#Start Ranger Admin
sudo echo "log4j.appender.xa_log_policy_appender=org.apache.log4j.DailyRollingFileAppender
log4j.appender.xa_log_policy_appender.file=\${logdir}/ranger_admin_policy_updates.log
log4j.appender.xa_log_policy_appender.datePattern='.'yyyy-MM-dd
log4j.appender.xa_log_policy_appender.append=true
log4j.appender.xa_log_policy_appender.layout=org.apache.log4j.PatternLayout
log4j.appender.xa_log_policy_appender.layout.ConversionPattern=%d [%t] %-5p %C{6} (%F:%L) - %m%n

log4j.category.org.apache.ranger.rest.ServiceREST=debug,xa_log_policy_appender
log4j.additivity.org.apache.ranger.rest.ServiceREST=false" >> /usr/lib/ranger/$ranger_admin_server/ews/webapp/WEB-INF/log4j.properties
sudo ln -s /usr/lib/ranger/$ranger_admin_server/ews/webapp/WEB-INF/classes/ranger-plugins/hive/ranger-hive-plugin-$ranger_download_version* /usr/lib/ranger/$ranger_admin_server/ews/webapp/WEB-INF/lib/
sudo ln -s /usr/lib/ranger/$ranger_admin_server/ews/webapp/WEB-INF/classes/ranger-plugins/hdfs/ranger-hdfs-plugin-$ranger_download_version* /usr/lib/ranger/$ranger_admin_server/ews/webapp/WEB-INF/lib/
sudo /usr/bin/ranger-admin stop || true
sudo /usr/bin/ranger-admin start
i=0;
while ! timeout 1 bash -c "echo > /dev/tcp/$hostname/6080"; do
        sleep 10;
        i=$((i + 1))
        if (( i > 6 )); then
                break;
        fi
done
#Start Ranger Usersync
sudo /usr/bin/ranger-usersync stop || true
sudo /usr/bin/ranger-usersync start
cd $installpath
# Install S3 service defination
aws s3 cp $s3bucket_http_url/inputdata/ranger-servicedef-s3.json .
aws s3 cp $s3bucket_http_url/inputdata/ranger-s3-repo.json .
curl -u admin:admin -X DELETE http://localhost:6080/service/public/v2/api/servicedef/name/awss3
curl -u admin:admin -X POST -H "Accept: application/json" -H "Content-Type: application/json" http://localhost:6080/service/public/v2/api/servicedef -d @ranger-servicedef-s3.json
curl -iv -u admin:admin -d @ranger-s3-repo.json -H "Content-Type: application/json" -X POST http://localhost:6080/service/public/v2/api/service/
# Restart SOLR
sudo /opt/solr/ranger_audit_server/scripts/stop_solr.sh || true
sudo /opt/solr/ranger_audit_server/scripts/start_solr.sh
#curl -X POST -H 'Content-Type: application/json'  http://localhost:8983/solr/ranger_audits/update?commit=true -d '{ "delete": {"query":"*:*"} }'
