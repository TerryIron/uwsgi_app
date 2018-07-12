#!/bin/bash

CONFIG=$1

[ "$CONFIG"  == "" ] && {
    CONFIG="./production.ini"
} || { 
    [ "$CONFIG" == "-d" ] && {
        CONFIG="./development.ini"
    }
}

./puwsgi run --server-port 6543 --server-host 0.0.0.0 --config ${CONFIG}
