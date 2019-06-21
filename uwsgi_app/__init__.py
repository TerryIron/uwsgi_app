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

__version__ = (0, 1, 0)

import os.path

from uwsgi_app.config import get_config, confinit, confprobe, modprobe
from uwsgi_app.routes import get_routes
import uwsgi_app.models as init_models


class Config(object):
    def __init__(self):
        self.registry = {}
        self.property = {}
        self.settings = {}

    def add_request_method(self, func, name, reify=True):
        if reify:
            self.property[name] = func
        else:
            self.property[name] = func()


def init_loader(c,
                global_config,
                settings,
                default_framework='tornado',
                opt_frame='application.framework',
                default_callable='application',
                opt_callable='application.callable',
                default_route='make_route',
                opt_route='application.route',
                default_init='init',
                opt_init='application.init'):
    _c = c.settings
    _framework = _c.get(opt_frame, default_framework)
    _module_app = modprobe(__name__ + '.' + _framework + '_app')

    _init = _c.get(opt_init, default_init)
    getattr(_module_app, _init)(c, **settings)
    _route = _c.get(opt_route, default_route)
    _routes = get_routes()
    _module_plugin = modprobe(__name__ + '.' + _framework + '_plugin')
    _plugin = getattr(_module_plugin, 'PluginLoaderV1')
    _routes['/_PluginLoaderV1'] = _plugin

    _plugin_path = os.path.join(os.path.dirname(__file__), 'plugins')
    for i in os.listdir(_plugin_path):
        api_file = os.path.join(os.path.join(_plugin_path, i), 'routes.py')
        if os.path.exists(api_file):
            _mod = __import__('plugins.{}.routes'.format(i), globals(), locals(), ['routes'])
            if hasattr(_mod, 'get_routes') and callable(getattr(_mod, 'get_routes')):
                _routes.update(getattr(_mod, 'get_routes')())

    getattr(_module_app, _route)(**_routes)

    _callable = _c.get(opt_callable, default_callable)
    _application = getattr(_module_app, _callable)
    setattr(c, 'application', _application)

    return _application


def main(global_config, **settings):
    """
    程序主入口
    :param global_config: 全局配置表
    :param settings: 配置表
    :return:
    """

    confinit(**global_config)
    conf = Config()
    setattr(conf, 'settings', get_config(confprobe()))
    init_models.includeme(conf)
    application = init_loader(conf, global_config, settings)

    return application() if callable(application) else application
