#!/bin/bash
set -euo pipefail
set -x
ldap_ip_address=$1
admin_user=$2
admin_password=$3
ldap_base_dn=$4

start=0
ldapsearch -x -D $admin_user -w $admin_password -H ldap://$ldap_ip_address -b "CN=Users, $ldap_base_dn"
while [ $? -ne 0 ]; do
    sleep 30
    start=$(($start+1))
    echo $start
    if [[ $start -gt 6 ]];
    then
      break
    fi
    ldapsearch -x -D $admin_user -w $admin_password -H ldap://$ldap_ip_address -b "CN=Users, $ldap_base_dn"
done
ldapadd -c -x -D $admin_user -w $admin_password -H ldap://$ldap_ip_address -f load-users-new.ldf || true
