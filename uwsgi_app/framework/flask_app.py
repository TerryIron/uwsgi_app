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
import flask_restful 
from flask import Flask, request

from uwsgi_app.config import modprobe
from uwsgi_app.settings import settings as config

_host = config.get('server_host', 'localhost')
_host = str(_host)
_port = config.get('server_port', 8888)
_port = int(_port) if _port else 8888
_routes = config.get('filter_routes', [])
_routes = _routes if _routes else []


_ROUTE = {}
_APP = None


def _check_is_view(t):
    if hasattr(t, 'func_closure') and \
        hasattr(t, 'func_defaults') and \
        hasattr(t, 'func_dict') and \
        hasattr(t, 'func_doc') and \
        hasattr(t, 'func_globals') and \
            hasattr(t, 'func_name'):
        return True
    else:
        return False


def make_app(route=None):
    _target_route = route if route else _ROUTE
    api = flask_restful.Api(_APP)
    for name, target in _target_route: 
        if _check_is_view(target):
            t = target()
        else:
            t = target
        api.add_resource(t, name, endpoint=str(target))
    return _APP


def init(config, **settings):
    from flask.globals import _request_ctx_stack

    def _add_property(s):
        for k, v in config.property.items():
            if callable(v):
                setattr(s, k, v())
            else:
                setattr(s, k, v)

    class _Flask(Flask):
        def dispatch_request(self):
            req = _request_ctx_stack.top.request
            if req.routing_exception is not None:
                self.raise_routing_exception(req)
            rule = req.url_rule

            if getattr(rule, 'provide_automatic_options', False) \
               and req.method == 'OPTIONS':
                return self.make_default_options_response()

            _add_property(req)
            ret = self.view_functions[rule.endpoint](**req.view_args)
            return ret
             
    app = _Flask(__name__)

    global _APP
    _APP = app


def make_route(**routes):
    _target_routes = routes
    if not _target_routes:
        _target_routes = [(r'{0}'.format(i), modprobe(j)) for i, j in _routes]
    else:
        _target_routes = [(r'{0}'.format(i), j)
                          for i, j in _target_routes.items()]
    global _ROUTE
    _ROUTE = _target_routes
    return _ROUTE


def application():
    return make_app()
