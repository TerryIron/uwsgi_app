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


class Config(object):
    def __init__(self):
        self.registry = {}
        self.property = {}

    def add_request_method(self, func, name, reify=True):
        if reify:
            self.property[name] = func
        else:
            self.property[name] = func()


def init_loader(c, global_config, settings,
                default_framework='tornado', opt_frame='application.framework',
                default_callable='application', opt_callable='application.callable',
                default_route='make_route', opt_route='application.route',
                default_init='init', opt_init='application.init'):
    _c = c.settings
    _framework = _c.get(opt_frame, default_framework)
    _module = modprobe(__name__ + '.' + _framework)

    _init = _c.get(opt_init, default_init)
    getattr(_module, _init)(c, **settings)
    _route = _c.get(opt_route, default_route)
    getattr(_module, _route)(**get_routes())

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

    confinit(**global_config)
    config = Config()
    setattr(config, 'settings', get_config(confprobe()))
    application = init_loader(config, global_config, settings)

    return application() if  callable(application) else application


