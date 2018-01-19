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

import tornado.ioloop
import tornado.wsgi
import tornado.web

from mxproxy.settings import settings as config

_host = config.get('server_host', 'localhost')
_host = str(_host)
_port = config.get('server_port', 8888)
_port = int(_port) if _port else 8888
_routes = config.get('filter_routes', [])
_routes = _routes if _routes else []


def make_route():
    return [(r'{0}'.format(i), j) for i, j in _routes]


def make_app():
    return tornado.web.Application(make_route())


def make_wsgi_app():
    return tornado.wsgi.WSGIAdapter(make_app())


application = make_wsgi_app()


if __name__ == "__main__":
    app = make_app()
    print app.listen
    app.listen(_port, _host)
    tornado.ioloop.IOLoop.current().start()
