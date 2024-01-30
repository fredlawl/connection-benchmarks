#!/bin/bash -e

# ./run-generate-data.sh 9024 65535 500

MIN_PORT=$1
MAX_PORT=$2
RANDOM_OFFSET_WINDOW=${3:-0}
FILENAME=$(date +%s)-$(uname -r)

unshare -rUn --kill-child /bin/bash --init-file <(cat <<EOF
    set -x

    ip link set dev lo up
    
    ulimit -Sn $(ulimit -Hn)
    sysctl -w net.ipv4.ip_local_port_range="$MIN_PORT $MAX_PORT"
    ./generate-data.py --random_offset_window $RANDOM_OFFSET_WINDOW $MIN_PORT,$MAX_PORT $FILENAME

    set +x
    exit 0
EOF
)

./plot-data.py < $FILENAME.csv > $FILENAME.png
