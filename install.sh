#!/bin/bash

apt-get install build-essential python-dev python-pip libmysqlclient-dev virtualenv*
virtualenv env --no-site-packages
TORNADO=$(cat requirements.txt | grep "tornado=\|tornado$")
[ "$TORNADO" == "" ] && {
    UWSGI_EMBED_PLUGINS="greenlet"
} || {
    UWSGI_EMBED_PLUGINS="tornado,greenlet"
}
source env/bin/activate && pip install greenlet && cp -rf env/include/site/python2.7/greenlet /usr/local/include
source env/bin/activate && UWSGI_EMBED_PLUGINS=$UWSGI_EMBED_PLUGINS pip install $TORNADO greenlet uwsgi==2.0.15
source env/bin/activate && pip install -r requirements.txt

