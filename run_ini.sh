#!/bin/bash

CONFIG=$1

[ "$CONFIG"  == "" ] && {
    CONFIG="./production.ini"
} || { 
    [ "$CONFIG" == "-d" ] && {
        CONFIG="./development.ini"
    }
}

framework=$(cat $CONFIG | grep "application.framework")
[ "$(echo $framework | grep tornado)" != "" ] && {
    framework="tornado"
} || {
    framework="flask"
}
python puwsgi run --framework $framework --server-port 6543 --server-host 0.0.0.0 --config ${CONFIG}