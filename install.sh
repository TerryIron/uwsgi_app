#!/bin/bash

apt-get install build-essential python-dev python-pip
UWSGI_PROFILE=gevent pip install uwsgi==2.0.14
