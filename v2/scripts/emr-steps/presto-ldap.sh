#!/bin/bash
set -euo pipefail
set -x

cd /etc/presto/conf

aws s3 cp s3://aws-datalake-security/client.crt .

#openssl x509 -outform der -in ldap01_slapd_cert.pem -out ldap_server.crt

keytool -noprompt -import -keystore $JAVA_HOME/lib/security/cacerts -trustcacerts -alias ldap_server -file client.crt -storepass changeit

keytool -genkeypair -alias presto -keyalg RSA -keystore presto_keystore.jks

sudo keytool -export -keystore presto_keystore.jks -alias presto  -file presto_server_certi.crt

echo "http-server.authentication.type=LDAP
authentication.ldap.url=ldaps://xx.xx.xx.xxx:636
authentication.ldap.user-bind-pattern=uid=${USER},ou=People,dc=example,dc=com
http-server.https.enabled=true
http-server.https.port=8890
http-server.https.keystore.path=/etc/presto/conf/presto_keystore.jks
http-server.https.keystore.key=xxxxx" >> config.properties