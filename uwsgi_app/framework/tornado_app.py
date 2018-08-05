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
import tornado.gen
import tornado.ioloop
import tornado.wsgi
import tornado.web
from tornado.ioloop import IOLoop
from functools import wraps

from uwsgi_app.config import modprobe
from uwsgi_app.settings import settings as config
import uwsgi_app.models as init_models

_host = config.get('server_host', 'localhost')
_host = str(_host)
_port = config.get('server_port', 8888)
_port = int(_port) if _port else 8888
_routes = config.get('filter_routes', [])
_routes = _routes if _routes else []

_ROUTE = {}


@tornado.gen.coroutine
def async_sleep(seconds):
    yield tornado.gen.Task(IOLoop.instance().add_timeout, time.time() + seconds)


def call_later(delay=0):
    def wrap_loop(func):
        @wraps(func)
        def wrap_func(*args, **kwargs):
            return IOLoop.instance().call_later(delay, func, *args, **kwargs)

        return wrap_func

    return wrap_loop


def call_event(delta=60):
    _delta = delta * 1000
    _args = {'args': []}

    def wrap_loop(func):
        @wraps(func)
        @tornado.gen.coroutine
        def wrap_func(*args, **kwargs):
            ret = None
            if not _args['args']:
                _args['args'] = args
            try:
                ret = func(*_args['args'], **kwargs)
            except Exception as e:
                pass

            IOLoop.instance().add_timeout(
                datetime.timedelta(milliseconds=_delta), wrap_func)
            return ret

        return wrap_func

    return wrap_loop


def initialize(self, **kwargs):
    for k, v in kwargs.items():
        setattr(self, k, v()) if callable(v) else setattr(self, k, v)


tornado.web.RequestHandler.initialize = initialize


class Application(tornado.web.Application):
    def __init__(self, *handlers, **settings):
        _session_settings = {
            'driver': 'memory',
            'driver_settings': dict(host=self),
            'force_persistence': True,
            'sid_name': 'torndsessionID',
            'session_lifetime': 1800
        }
        settings.update(**dict(session=_session_settings))
        super(Application, self).__init__(*handlers, **settings)


_APP = Application


def make_app(route=None):
    _target_route = route if route else _ROUTE
    return _APP(_target_route)


def init(config, **settings):
    init_models.includeme(config)

    class _Application(Application):
        def __init__(self, *handlers, **settings):
            _handlers = [[(_u, _h, config.property) for _u, _h in _handler]
                         for _handler in handlers]
            super(_Application, self).__init__(*_handlers, **settings)

    global _APP
    _APP = _Application


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
    return tornado.wsgi.WSGIAdapter(make_app())


if __name__ == "__main__":
    app = make_app()
    app.listen(_port, _host)
    tornado.ioloop.IOLoop.current().start()
