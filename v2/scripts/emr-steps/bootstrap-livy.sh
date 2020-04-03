#!/bin/bash

set -e

LIVY_SETUP=$(cat <<EOF
while [ ! -f /etc/livy/conf/livy.conf ]
do
    sleep 5
done

# Enable Livy
sed -i 's/^# livy.repl.enable-hive-context/livy.repl.enable-hive-context true/' /etc/livy/conf/livy.conf

sudo echo "	livy.superusers=hue,zeppelin
	livy.server.access_control.enabled = true
	livy.server.access_control.users = livy,zeppelin,hue" >> /etc/livy/conf/livy.conf

# Restart Livy
restart livy-server

exit 0
EOF
)
echo "${LIVY_SETUP}" | tee -a /tmp/livy_setup.sh
chmod +x /tmp/livy_setup.sh
sudo /tmp/livy_setup.sh &
exit 0
