
#!/bin/bash

PWD=$(pwd)
CONFIG=$1
PORT=$2

[ "$PORT"  == "" ] && {
    PORT=6543
}

[ "$CONFIG"  == "" ] && {
    CONFIG="$PWD/production.ini"
} || { 
    [ "$CONFIG" == "-d" ] && {
        CONFIG="$PWD/development.ini"
    }
}

framework=$(cat $CONFIG | grep "application.framework")
[ "$(echo $framework | grep tornado)" != "" ] && {
    framework="tornado"
} || {
    framework="flask"
}

for i in $(find | grep setup.py$); do 
    j=$(dirname $i); 
    [ "$j" != "." ] && [ "$(echo $j | grep env)" == "" ] && {
        cd $j && python setup.py bdist_egg && cd -
    }
done

cd $PWD
export PYTHONPATH=$PWD
python setup.py develop
export PYTHONOPTIMIZE=1
python puwsgi run --framework $framework --server-port $PORT --server-host 0.0.0.0 --config ${CONFIG}
