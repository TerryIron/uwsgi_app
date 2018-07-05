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

import json
import os.path
import commands
import tornado.web
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from ConfigParser import ConfigParser

from uwsgi_app.config import get_config, confinit, confprobe, modprobe, classprobe, GLOBAL_CONFIG
from uwsgi_app.framework.tornado_app import call_later, call_event, async_sleep
from uwsgi_app.plugins.loader import PluginLoader


@classprobe('start_plugins')
class PluginLoaderV1(tornado.web.RequestHandler, PluginLoader):
    executor = ThreadPoolExecutor(1000)

    @classmethod
    def load_plugins(cls):
        c = confprobe()

        def get_plugin_config():
            if not c.has_section('app:main'):
                return
            if not c.has_option('app:main', 'application.load_plugins'):
                return
            if not bool(c.get('app:main', 'application.load_plugins')):
                return
            if not c.has_section('plugins'):
                return
            if not c.has_option('plugins', 'config'):
                return
            return c.get('plugins', 'config')
        
        config = get_plugin_config()
        p = ConfigParser()
        p.read(config)

        global_plugin = {}

        def init_plugin_path(plugin_path=os.path.join(os.path.dirname(__file__), '../plugins')):
            for s in p.sections():
                if not s.startswith('app:'):
                    continue
                if not p.has_option(s, 'load'):
                    continue
                _path = p.get(s, 'load')
                _plugin_path = os.path.join(plugin_path, _path)
                _home = p.get(s, 'load').split('.zip')[0]
                _plugin_home = os.path.join(plugin_path, _home)

                app_config = os.path.join(_plugin_home, 'app.json')
                print app_config

                if not os.path.exists(_plugin_home):
                    _cmd = 'unzip {} -d {}'
                    commands.getoutput(_cmd.format(_plugin_path, plugin_path))

                    app_json = json.load(open(app_config))
                    app_requirements = app_json.get('imports', 'requirements.txt')

                    _cmd = 'cd {}; virtualenv env; source env/bin/activate; pip install -r {}'
                    commands.getoutput(_cmd.format(_plugin_home, app_requirements))
                else:
                    app_json = json.load(open(app_config))

                app_env = os.path.join(_plugin_home, 'env/lib/python2.7')

                app_name = app_json.get('name', '')
                if not app_name:
                    raise Exception('plugin {} app_name not found'.format(_home))
                global_plugin[s] = app_name

                app_lang = app_json.get('lang', 'python')
                app_version = app_json.get('version', '0.01')
                app_actions = [(k, __import__(v, globals(), locals(), v.split('.')[-1])) 
                               for k, v in app_json.get('actions', {})]
                app_public_actions = app_json.get('public_actions', [])
                app_init = app_json.get('init', None)
                if not app_init:
                    raise Exception('plugin {} can not init'.format(_home))

                cls.set_plugin(app_name, app_version, app_actions, 
                               app_public_actions, app_init,
                               app_lang, app_env, _plugin_home)

        init_plugin_path()

        def init_plugin_config():

            def get_pipeline(n, pipe=None):
                _pipe = pipe if pipe else []
                for _n in p.get('pipeline:{}'.format(n), 'align').split(' '):
                    if _n.startswith('p:'):
                        get_pipeline(_n, _pipe)
                    else:
                        _pipe.append(_n)
                return _pipe

            if not p.has_section('plugin:main'):
                return
            if not p.has_option('plugin:main', 'start'):
                return
            for name in p.get('plugin:main', 'start').split(' '):
                if not p.has_section('pipeline:{}'.format(name)):
                    continue
                if not p.has_option('pipeline:{}'.format(name), 'align'):
                    continue
                _pipelines = [global_plugin[pn] for pn in get_pipeline(name) 
                              if pn in global_plugin and global_plugin[pn]]
                cls.set_pipeline(name, _pipelines)

        init_plugin_config()
