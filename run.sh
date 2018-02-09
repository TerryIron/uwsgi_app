#!/bin/bash

CONFIG=$1

[ "$CONFIG"  == "" ] && {
    CONFIG="./config.json"
}

./puwsgi run --target-app uwsgi_app.app --server-port 9999 --server-host 0.0.0.0 --config ${CONFIG}
