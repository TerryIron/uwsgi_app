#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015-2018  Terry Xi
# All Rights Reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import time
import datetime
from flask import Flask
from flask_restful import Resource, Api
from gevent import pywsgi

from uwsgi_app.config import modprobe
from uwsgi_app.settings import settings as config

_host = config.get('server_host', 'localhost')
_host = str(_host)
_port = config.get('server_port', 8888)
_port = int(_port) if _port else 8888
_routes = config.get('filter_routes', [])
_routes = _routes if _routes else []


_ROUTE = {}


def make_app(route=None):
    _target_route = route if route else _ROUTE
    app = Flask(__name__)
    api = Api(app)
    for name, target in _target_route: 
        if hasattr(target, 'func_closure') and \
            hasattr(target, 'func_defaults') and \
            hasattr(target, 'func_dict') and \
            hasattr(target, 'func_doc') and \
            hasattr(target, 'func_globals') and \
            hasattr(target, 'func_name'):
            t = target()
        else:
            t = target
        api.add_resource(t, name, endpoint=str(target))
    return app


def init(config, **settings):
    pass


def make_route(**routes):
    global _ROUTE
    _target_routes = routes
    if not _target_routes:
        _target_routes = [(r'{0}'.format(i), modprobe(j)) for i, j in _routes]
    else:
        _target_routes = [(r'{0}'.format(i), j)
                          for i, j in _target_routes.items()]
    _ROUTE = _target_routes
    return _ROUTE


def application():
    return make_app()
