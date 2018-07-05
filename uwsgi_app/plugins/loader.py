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
    import os.path as op
    from gevent.pool import Pool
    pool = Pool(1000)

    __plug_globals__ = {} # 插件imports模块环境, 如{'pluginA': PLUGINA}
    __plug_libpath__ = {} # 插件私有库环境, 如{'pluginA': LIBPATH}
    __plug_path__ = {} # 插件私有配置环境, 如{'pluginA': CONFPATH}
    plugin_registry = {} # 插件action入口, 如{'pluginA': {NAME: FUNC}}
    plugin_public_registry = {} # 插件public_action配置, 如{'pluginA': [NAME]}
    plugin_init = {} # 插件init配置, 如{'pluginA': [NAME]}
    plugin_lang = {} # 插件私有环境, 如{'pluginA': 'python'}
    plugin_pipeline = {} # 插件流程配置, 如{'pipelineA': [PLUGINS]}
    plugins = [] # 插件配置入口, [pipelineA, pipelineB]

    results = {}

    @classmethod
    def set_pipeline(cls, name, plugin_names):
        if name not in cls.plugins:
            cls.plugins.append(name)
        else:
            raise Exception('Pipeline {} is already exist'.format(name))
        cls.plugin_pipeline[name] = [p for p in plugin_names]

    @classmethod
    def set_plugin(cls, name, version, funcs, public_names, init_name, lang='python', libpath='.', path='.'):
        cls.plugin_lang[name] = lang
        cls.plugin_registry[name] = dict([(n, f) for n, f in funcs if callable(f)])
        cls.plugin_public_registry[name] = [n for n in public_names if n in cls.plugin_registry[name]]
        cls.plugin_init[name] = init_name if init_name in cls.plugin_registry[name] else None
        if not cls.plugin_init[name]:
            raise Exception('Plugin {} will not initialize'.format(name))

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
        cls.__plug_globals__[name] = p

    @classmethod
    def load_plugins(cls, plugin_path):
        pass

    @classmethod
    def init_plugins(cls, plugin_path=op.abspath(op.dirname(__file__))):
        return plugin_path

    @classmethod
    def _plugin_environ(cls, name, entry):
        import os.path as op
        _plugin_path = op.abspath(op.dirname(__file__))
        _env, _lib_path = {}, cls.__plug_libpath__.get(name, op.join(_plugin_path, name))
        import sys
        sys.path = ['.', _plugin_path]
        sys.path.insert(0, _lib_path)
        # basic plugin environ
        _env.update(dict([('plugin_' + k, v) for k, v in cls.__plug_globals__.items()]))
        # entry point of plugin function 
        _env[name] = entry
        # system environ of plugin function 
        _env['sys'] = sys
        _env['__builtins__'] = globals()['__builtins__']
        _env['__file__'] = globals()['__file__']
        _env['__package__'] = None
        _env['__name__'] = name
        _env['__plugin__'] = cls.__plug_path__[name]
        globals().clear()
        globals().update(_env)
        return _env

    @classmethod
    def run_python_plugin(cls, pipe_name, name):
        func_name = cls.plugin_init[name]
        def call_plugin_func():
            env = cls._plugin_environ(name, cls.plugin_registry[name][func_name])
            # call plugin function 
            exec('cls.results[{0}] = {1}(**cls.results[{0}])'.format(pipe_name, name), env)
        cls.pool.apply_async(call_plugin_func())

    @classmethod
    def run_plugins(cls):
        _globals = {}
        _globals.update(globals())
        for p_entry in cls.plugins:                                                                                                                                               
            if p_entry not in cls.plugin_pipeline:
                continue
            if p_entry not in cls.plugins_result:
                cls.plugins_result[p_entry] = {}

            for p in cls.plugin_pipeline[p_entry]:
                if p not in cls.plugin_init:
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
        globals().update(_globals)

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

