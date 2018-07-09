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


class PluginLoader(object):

    class Result(object):
        pass 

    import os.path as op
    from gevent.pool import Pool
    pool = Pool(1000)

    __plug_globals__ = {} # 插件imports模块环境, 如{'pluginA': PLUGINA}
    __plug_libpath__ = {} # 插件私有库环境, 如{'pluginA': LIBPATH}
    __plug_path__ = {} # 插件私有配置环境, 如{'pluginA': CONFPATH}
    plugin_registry = {} # 插件action入口, 如{'pluginA': {NAME: FUNC}}
    plugin_public_registry = {} # 插件public_action配置, 如{'pluginA': [NAME]}
    plugin_init = {} # 插件init配置, 如{'pluginA': [NAME]}
    plugin_call = {} # 插件call配置, 如{'pluginA': [NAME]}
    plugin_lang = {} # 插件私有环境, 如{'pluginA': 'python'}
    plugin_pipeline = {} # 插件流程配置, 如{'pipelineA': [PLUGINS]}
    plugins = [] # 插件配置入口, [pipelineA, pipelineB]

    plugin_config = {}
    globals = {}
    results = Result()

    @classmethod
    def import_plugin(cls, name):
        _name = 'plugin_' + str(name)
        return cls.__plug_globals__[_name] if _name in cls.__plug_globals__ else None

    @classmethod
    def set_pipeline(cls, name, plugin_names):
        if name not in cls.plugins:
            cls.plugins.append(name)
        else:
            raise Exception('Pipeline {} is already exist'.format(name))
        cls.plugin_pipeline[name] = [p for p in plugin_names]

    @classmethod
    def set_plugin(cls, name, version, funcs, public_names, init_name, call_name, lang='python', libpath='.', path='.'):
        cls.plugin_lang[name] = lang
        cls.plugin_registry[name] = dict([(n, f) for n, f in funcs if callable(f)])
        cls.plugin_public_registry[name] = [n for n in public_names if n in cls.plugin_registry[name]]
        cls.plugin_init[name] = init_name if init_name in cls.plugin_registry[name] else None
        if not cls.plugin_init[name]:
            raise Exception('Plugin {} will not initialize'.format(name))
        cls.plugin_call[name] = call_name if call_name in cls.plugin_registry[name] else None
        if not cls.plugin_call[name]:
            raise Exception('Plugin {} will not startup/callable'.format(name))

        cls.__plug_libpath__[name] = libpath
        cls.__plug_path__[name] = path

        import abc

        class PluginBase(object):
            __metaclass__ = abc.ABCMeta
            __name__ = name
            __version__ = version

        p = PluginBase()
        for n, f in cls.plugin_registry[name].items():
            if n not in cls.plugin_public_registry[name]:
                continue
            setattr(p, n, f)
        cls.plugin_registry[name][cls.plugin_init[name]]()
        cls.__plug_globals__[name] = p

    @classmethod
    def load_plugins(cls, plugin_path):
        pass

    @classmethod
    def init_plugins(cls, plugin_path=op.abspath(op.dirname(__file__))):
        return plugin_path

    @classmethod
    def get_plugin_path(cls):
        import os.path as op
        _plugin_path = op.abspath(op.dirname(__file__))
        return _plugin_path

    @classmethod
    def get_plugin_import_path(cls, name):
        import os.path as op
        _plugin_path = cls.get_plugin_path()
        _lib_path = cls.__plug_libpath__.get(name, op.join(_plugin_path, name))
        import sys
        sys.path = ['.', _plugin_path]
        sys.path.insert(0, _lib_path)
        return sys

    @classmethod
    def _plugin_environ(cls, name, entry):
        _plugin_path = cls.get_plugin_path()
        _lib_path = cls.get_plugin_import_path(name)
        _env = {}
        # basic plugin environ
        _env.update(dict([('plugin_' + k, v) for k, v in cls.__plug_globals__.items()]))
        # entry point of plugin function 
        _env[name] = entry
        # system environ of plugin function 
        _env['sys'] = _lib_path
        _env['__builtins__'] = globals()['__builtins__']
        _env['__file__'] = globals()['__file__']
        _env['__package__'] = None
        _env['__name__'] = name
        _env['__plugin__'] = cls.__plug_path__[name]
        _env['__result__'] = cls.results
        globals().clear()
        globals().update(_env)
        return _env

    @classmethod
    def run_python_plugin(cls, pipe_name, name):
        func_name = cls.plugin_call[name]
        def call_plugin_func():
            env = cls._plugin_environ(name, cls.plugin_registry[name][func_name])
            # call plugin function 
            exec('__result__.{0} = {1}({2}, **__result__.{0})'.format(pipe_name, name, cls.plugin_config), env)
            exec('_result = {}', env)
            exec('__result__.{0} = _result'.format(pipe_name), env)
            _env = {} 
            _env.update(env)
            _env.update(cls.globals)
            exec('PluginLoader.results = __result__', _env)
        cls.pool.apply_async(call_plugin_func())

    @classmethod
    def run_plugins(cls):
        cls.globals.update(globals())
        for p_entry in cls.plugins:                                                                                                                                               
            if p_entry not in cls.plugin_pipeline:
                continue
            if not hasattr(cls.results, p_entry):
                setattr(cls.results, p_entry, {})

            for p in cls.plugin_pipeline[p_entry]:
                if p not in cls.plugin_init:
                    continue
                if p not in cls.plugin_call:
                    continue
                if p not in cls.plugin_registry:
                    continue
                if p not in cls.plugin_public_registry:
                    continue

                lang = cls.plugin_lang.get(p, 'python')
                if 'python' in lang:
                    cls.run_python_plugin(p_entry, p)
                else:
                    pass
        globals().clear()
        globals().update(cls.globals)

    @classmethod
    def _load_plugins(cls, plugin_path):
        return cls.load_plugins()

    @classmethod
    def _run_plugins(cls):
        return cls.run_plugins()

    @classmethod
    def start_plugins(cls):
        _path = cls.init_plugins()
        cls._load_plugins(_path)
        cls._run_plugins()


class PluginLoaderV1(PluginLoader):

    @classmethod
    def load_plugins_from_config(cls, c):

        import json
        import os.path
        import commands
        from ConfigParser import ConfigParser

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

        def init_plugin_path():
            plugin_path = cls.get_plugin_path()
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
                global_plugin[s.split('app:')[1]] = app_name

                app_lang = app_json.get('lang', 'python')
                app_version = app_json.get('version', '0.01')
                _globals = globals()
                _globals['sys'] = cls.get_plugin_import_path(app_name)
                app_actions = [(k, getattr(__import__('.'.join(v.split('.')[:-1]), _globals, locals()), v.split('.')[-1])) 
                               for k, v in app_json.get('actions', {}).items()]
                app_public_actions = app_json.get('public_actions', [])
                app_init = app_json.get('init', None)
                app_call = app_json.get('call', None)
                if not app_init:
                    raise Exception('plugin {} can not init'.format(_home))

                cls.set_plugin(app_name, app_version, app_actions, 
                               app_public_actions, app_init, app_call,
                               app_lang, app_env, _plugin_home)

        init_plugin_path()

        def init_plugin_config():

            def config_pipeline(n, pipe=None):
                _pipe = pipe if pipe else []
                _pipe_name = 'pipeline:{}'.format(n)
                for _o in p.options(_pipe_name):
                    if _o == 'align':
                        continue
                    cls.plugin_config[_o] = c.get(_pipe_name, _o)
                for _n in p.get(_pipe_name, 'align').split(' '):
                    if _n.startswith('p:'):
                        config_pipeline(_n.split('p:')[1], _pipe)
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
                _pipelines = [global_plugin[pn] for pn in config_pipeline(name) 
                              if pn in global_plugin and global_plugin[pn]]
                cls.set_pipeline(name, _pipelines)

        init_plugin_config()
