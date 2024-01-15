#!/bin/bash -e

# don't feel like setting up the netnamespace for this
# unshare -rUn ./generate-data.py
ulimit -Sn $(ulimit -Hn)
#sudo sysctl -w net.ipv4.ip_local_port_range="9024 65535"
./generate-data.py
