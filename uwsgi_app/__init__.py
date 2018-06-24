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
import ConfigParser

import uwsgi_app.models as _models_loader

GLOBAL_CONFIG = {}


class Config(object):
    def __init__(self):
        self.registry = {}

    def add_request_method(self, func, name, reify=True):
        if reify:
            setattr(self, name, func)
        else:
            setattr(self, name, func())


Configurator = Config()


def modprobe(mod):
    return __import__(mod, globals(), locals(), [mod.split('.')[-1]])


def load_config(c, sect='app:main'):
    global Configurator 
    _settings = dict([(o, c.get(sect, o, None)) for o in c.options(sect)])
    setattr(Configurator , 'settings', _settings)
    return Configurator


def init_loader(c, global_config, settings,
                default_framework='tornado', opt_frame='application.framework',
                default_callable='application', opt_callable='application.callable',
                default_route='make_route', opt_route='application.route',
                default_init='init', opt_init='application.init'):
    _c = c.settings
    _framework = _c.get(opt_frame, default_framework)
    _module = modprobe(__name__ + '.' + _framework)

    _init = _c.get(opt_init, default_init)
    getattr(_module, _init)(global_config, **settings)
    _route = _c.get(opt_route, default_route)
    getattr(_module, _route)()

    _callable = _c.get(opt_callable, default_callable)
    _application = getattr(_module, _callable)
    setattr(c, 'application', _application)

    return _application


def main(global_config, **settings):
    """
    程序主入口
    :param global_config: 全局配置表
    :param settings: 配置表
    :return: 
    """

    GLOBAL_CONFIG.update(global_config)                                                                                                                                           
    file_name = global_config.get('__file__')
    c = ConfigParser.ConfigParser()
    c.read(file_name)
    config = load_config(c)

    application = init_loader(config, global_config, settings)

    _models_loader.includeme(config)
    
    return application() if  callable(application) else application


