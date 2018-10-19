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

for i in $(find | grep setup.py); do 
    j=$(dirname $i); 
    [ "$j" != "." ] && {
        cd $j && python setup.py bdist_egg && cd -
    }
done
python puwsgi run --framework $framework --server-port 6543 --server-host 0.0.0.0 --config ${CONFIG}
