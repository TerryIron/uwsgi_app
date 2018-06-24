#!/bin/bash

CONFIG=$1

[ "$CONFIG"  == "" ] && {
    CONFIG="./config.json"
}

./puwsgi run --target-app mxproxy.app --server-port 6543 --server-host 0.0.0.0 --config ${CONFIG}
