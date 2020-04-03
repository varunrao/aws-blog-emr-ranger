#!/bin/bash

TRUST_STORE_PASS=$(sudo cat /etc/presto/conf/config.properties | grep 'internal-communication.https.keystore.key' | cut -d '=' -f2 | tr -d ' ')

sudo sed -i "s/.*8889.*//" /etc/presto/conf/presto-env.sh

sudo sed -i "s/PASSWORD/${TRUST_STORE_PASS}/g" /etc/presto/conf/presto-env.sh

exit 0
