#!/bin/bash

apt-get install build-essential python-dev python-pip libmysqlclient-dev
#UWSGI_PROFILE=gevent pip install uwsgi==2.0.14
UWSGI_EMBED_PLUGINS=tornado,greenlet pip install tornado==4.5.3 greenlet uwsgi==2.0.14

