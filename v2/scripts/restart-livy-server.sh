#!/usr/bin/env bash

echo "Stopping Livy Server"
sudo stop livy-server

echo "Starting Livy Server"
sudo start livy-server

exit 0