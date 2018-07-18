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
    @classmethod
    def get_logger(cls, name):
        import logging

        __LOGGER__ = None

        LOGGER_FORMAT = '[%(asctime)s][%(name)s][%(levelname)s][%(filename)s:%(lineno)d %(funcName)s] %(message)s'
        LOGGER_LEVEL = 'DEBUG'

        def handler_init(filename=None, level=LOGGER_LEVEL, fmt=LOGGER_FORMAT):
            if filename:
                handler = logging.FileHandler(filename)
            else:
                handler = logging.StreamHandler()

            if not level:
                level = LOGGER_LEVEL

            if not fmt:
                fmt = LOGGER_FORMAT
            handler.setFormatter(logging.Formatter(fmt))

            global __LOGGER__
            __LOGGER__ = (handler, level)
            return __LOGGER__

        # Color escape string
        COLOR_RED = '\033[1;31m'
        COLOR_GREEN = '\033[1;32m'
        COLOR_YELLOW = '\033[1;33m'
        COLOR_BLUE = '\033[1;34m'
        COLOR_PURPLE = '\033[1;35m'
        COLOR_CYAN = '\033[1;36m'
        COLOR_GRAY = '\033[1;37m'
        COLOR_WHITE = '\033[1;38m'
        COLOR_RESET = '\033[1;0m'

        # Define log color
        LOG_COLORS = {
            'DEBUG': '%s',
            'INFO': COLOR_GREEN + '%s' + COLOR_RESET,
            'WARNING': COLOR_YELLOW + '%s' + COLOR_RESET,
            'ERROR': COLOR_RED + '%s' + COLOR_RESET,
            'CRITICAL': COLOR_RED + '%s' + COLOR_RESET,
            'EXCEPTION': COLOR_RED + '%s' + COLOR_RESET,
        }

        class ColorFormatter(logging.Formatter):
            def __init__(self, fmt=None, datefmt=None):
                logging.Formatter.__init__(self, fmt, datefmt)

            def format(self, record):
                level_name = record.levelname
                msg = logging.Formatter.format(self, record)
                return LOG_COLORS.get(level_name, '%s') % msg

        class Logger(logging.Logger):
            def __init__(self, name, level=logging.NOTSET):
                self.logger = None
                logging.Logger.__init__(self, name, level=level)

            def _log(self, level, msg, args, exc_info=None, extra=None):
                if not self.logger:
                    self._init()
                super(Logger, self)._log(
                    level, msg, args, exc_info=exc_info, extra=extra)

            def _init(self, colorful=True):
                if not self.logger:
                    if not __LOGGER__:
                        _handler = logging.StreamHandler()
                        _level = LOGGER_LEVEL
                    else:
                        _handler, _level = __LOGGER__
                    if colorful:
                        _handler.setFormatter(ColorFormatter(LOGGER_FORMAT))
                    else:
                        _handler.setFormatter(logging.Formatter(LOGGER_FORMAT))
                    self.addHandler(_handler)
                    self.setLevel(_level)
                    self.logger = True

            def add_handler(self, file_name):
                _h = logging.FileHandler(file_name)
                _h.setFormatter(logging.Formatter(LOGGER_FORMAT))
                self.addHandler(_h)

        def get_logger(name):
            logger = Logger(name)
            return logger

        return get_logger(name)

    class Result(object):
        pass

    class Config(object):
        pass

    class Loader(object):
        pass

    import sys
    import os.path as op
    from gevent.pool import Pool
    pool = Pool(1000)

    __plug_globals__ = {}  # 插件imports模块环境, 如{'pluginA': PLUGINA}
    __plug_libpath__ = {}  # 插件私有库环境, 如{'pluginA': LIBPATH}
    __plug_path__ = {}  # 插件私有配置环境, 如{'pluginA': CONFPATH}
    plugin_registry = {}  # 插件action入口, 如{'pluginA': {NAME: FUNC}}
    plugin_public_registry = {}  # 插件public_action配置, 如{'pluginA': [NAME]}
    plugin_init = {}  # 插件init配置, 如{'pluginA': [NAME]}
    plugin_call = {}  # 插件call配置, 如{'pluginA': [NAME]}
    plugin_lang = {}  # 插件私有环境, 如{'pluginA': 'python'}
    plugin_pipeline = {}  # 插件流程配置, 如{'pipelineA': [PLUGINS]}
    plugin_channels = {}  # 插件数据管道配置, 如{'pipelineA': [CHANNEL]}
    plugins = []  # 插件配置入口, [pipelineA, pipelineB]

    plugin_config = Config()
    plugin_loader = Loader()
    results = Result()
    result_channel = ('data', 'result')

    globals = {}
    paths = []
    paths.extend(sys.path)

    @classmethod
    def _plugin_realaction(cls, name):
        _action = name.split('.')
        if len(_action) > 1:
            return _action[1]

    @classmethod
    def _plugin_realname(cls, name):
        return name.split('.')[0]

    @classmethod
    def import_plugin(cls, name):
        _name = 'plugin_' + str(name)
        return cls.__plug_globals__[
            _name] if _name in cls.__plug_globals__ else None

    @classmethod
    def set_pipeline(cls, name, plugin_names, channel_names, idx=None):
        _new_name = name if not idx else name + str(idx)
        if _new_name not in cls.plugins:
            cls.plugins.append(_new_name)
        else:
            raise Exception('Pipeline {} is already exist'.format(_new_name))
        cls.plugin_pipeline[_new_name] = [p for p in plugin_names]
        cls.plugin_channels[_new_name] = [p for p in channel_names]
        setattr(cls.plugin_config, _new_name, dict())
        getattr(cls.plugin_config, _new_name).update(
            getattr(cls.plugin_config, name))

        setattr(cls.results, _new_name, dict())
        d = cls.Loader()
        setattr(d, 'config', getattr(cls.plugin_config, _new_name))
        setattr(cls.plugin_loader, _new_name, d)

    @classmethod
    def set_plugin(cls,
                   name,
                   version,
                   funcs,
                   public_names,
                   init_name,
                   call_name,
                   lang='python',
                   libpath='.',
                   path='.'):
        cls.plugin_lang[name] = lang
        cls.plugin_registry[name] = dict(
            [(n, f) for n, f in funcs if callable(f)])
        cls.plugin_public_registry[name] = [
            n for n in public_names if n in cls.plugin_registry[name]
        ]
        cls.plugin_init[name] = init_name if init_name in cls.plugin_registry[
            name] else None
        if not cls.plugin_init[name]:
            raise Exception('Plugin {} will not initialize'.format(name))
        cls.plugin_call[name] = call_name if call_name in cls.plugin_registry[
            name] else None
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
        _env.update(
            dict(
                [('plugin_' + k, v) for k, v in cls.__plug_globals__.items()]))
        # entry point of plugin function
        _env[name] = entry
        # system environ of plugin function
        _env['sys'] = _lib_path
        _env['__builtins__'] = globals()['__builtins__']
        _env['__file__'] = globals()['__file__']
        _env['__package__'] = None
        _env['__name__'] = name
        _env['__error__'] = []
        _env['__plugin__'] = cls.__plug_path__[name]
        _env['__result__'] = cls.results
        _env['__channels__'] = cls.result_channel
        globals().clear()
        globals().update(_env)
        return _env

    @classmethod
    def run_python_plugin(cls, pipe_name, name, channel):

        _name = cls._plugin_realname(name)
        _action = cls._plugin_realaction(name)
        if not _action:
            func_name = cls.plugin_call[name]
        else:
            if _action in cls.plugin_registry[_name]:
                func_name = _action
            else:
                raise Exception('Plugin {} action {} not found'.format(
                    pipe_name, _action))

        def call_plugin_func():
            env = cls._plugin_environ(_name,
                                      cls.plugin_registry[_name][func_name])
            # call plugin function
            d = getattr(cls.plugin_loader, pipe_name)
            setattr(d, 'channel_scope', ('data', 'result'))
            setattr(d, 'channel', channel)
            setattr(d, 'logger', cls.get_logger('.'.join([pipe_name, _name])))
            env['__loader__'] = d

            env['__pipe__'] = pipe_name
            _taction = _name + '.' + func_name
            env['__action__'] = _taction

            exec ('__result__.{0} = {1}({2}, **__result__.{0})'.format(
                pipe_name, _name, '__loader__'), env)
            exec (
                '__error__ = [Exception("Result Channel:" + c + '
                '" not found in Pipeline:" + __pipe__ + " Action:" + __action__) '
                'for c in __channels__ if c not in __result__.{0}]'.format(
                    pipe_name), env)
            exec ('if __error__: raise __error__[0]', env)
            _env = {}
            _env.update(env)
            _env.update(cls.globals)
            exec ('PluginLoader.results = __result__', _env)

        cls.pool.apply_async(call_plugin_func())

    @classmethod
    def run_plugins(cls):
        cls.globals.update(globals())
        for p_entry in cls.plugins:
            if p_entry not in cls.plugin_pipeline:
                continue
            if p_entry not in cls.plugin_channels:
                continue
            if not hasattr(cls.results, p_entry):
                setattr(cls.results, p_entry, {})

            for i, p in enumerate(cls.plugin_pipeline[p_entry]):
                _p = cls._plugin_realname(p)
                n = cls.plugin_channels[p_entry][i]
                if _p not in cls.plugin_init:
                    continue
                if _p not in cls.plugin_call:
                    continue
                if _p not in cls.plugin_registry:
                    continue
                if _p not in cls.plugin_public_registry:
                    continue

                lang = cls.plugin_lang.get(_p, 'python')
                if 'python' in lang:
                    cls.run_python_plugin(p_entry, p, n)
                else:
                    pass
        globals().clear()
        globals().update(cls.globals)
        import sys
        sys.path = cls.paths

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
                    app_requirements = app_json.get('imports',
                                                    'requirements.txt')

                    _cmd = 'cd {}; virtualenv env; source env/bin/activate; pip install -r {}'
                    commands.getoutput(
                        _cmd.format(_plugin_home, app_requirements))
                else:
                    app_json = json.load(open(app_config))

                app_env = os.path.join(_plugin_home, 'env/lib/python2.7')

                app_name = app_json.get('name', '')
                if not app_name:
                    raise Exception(
                        'plugin {} app_name not found'.format(_home))
                global_plugin[s.split('app:')[1]] = app_name

                app_lang = app_json.get('lang', 'python')
                app_version = app_json.get('version', '0.01')
                _globals = globals()
                _globals['sys'] = cls.get_plugin_import_path(app_name)
                app_actions = []
                for k, v in app_json.get('actions', {}).items():
                    _callable_name = v.split('.')[-1]
                    try:
                        _callable = getattr(
                            __import__('.'.join(v.split('.')[:-1]), _globals,
                                       locals()), _callable_name)
                    except AttributeError as e:
                        raise Exception(
                            'App:{} inline function:{} not found'.format(
                                app_name, k))
                    d = (k, _callable)
                    app_actions.append(d)
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
            def config_boardcast(n, pipe_name, pipe=None, channel=None):
                pipe = pipe if pipe else []
                channel = channel if channel else []
                _boardcast_name = 'boardcast:{}'.format(n)
                _new_pipe, _new_channel = [], []
                for _o in p.options(_boardcast_name):
                    if _o == 'align':
                        continue
                    getattr(cls.plugin_config, pipe_name)[_o] = c.get(
                        _pipe_name, _o)
                _aligns = p.get(_boardcast_name, 'align').split(' ')
                for _i, _n in enumerate(_aligns):
                    if _n.startswith('c:'):
                        raise Exception(
                            'Inline Channel not support, check Boardcast {}'.
                            format(_boardcast_name))
                    if _n.startswith('p:'):
                        raise Exception(
                            'Inline Pipeline not support, check Boardcast {}'.
                            format(_boardcast_name))
                    if _n.startswith('b:'):
                        raise Exception(
                            'Inline Boardcast not support, check Boardcast {}'.
                            format(_boardcast_name))
                    _pipe, _channel = [], []
                    _pipe.extend(pipe)
                    _channel.extend(channel)
                    _pipe.append(_n)
                    _new_pipe.append(_pipe)
                    _new_channel.append(_channel)
                if not _new_pipe:
                    _new_pipe.extend(pipe)
                if not _new_channel:
                    _new_pipe.extend(channel)
                return _new_pipe, _new_channel

            def config_pipeline(n, pipe, channel):
                _pipe_name = 'pipeline:{}'.format(n)

                if not hasattr(cls.plugin_config, _pipe_name):
                    setattr(cls.plugin_config, n, dict())

                for _o in p.options(_pipe_name):
                    if _o == 'align':
                        continue
                    getattr(cls.plugin_config, n)[_o] = c.get(_pipe_name, _o)

                _aligns = p.get(_pipe_name, 'align').split(' ')
                for _i, _n in enumerate(_aligns):
                    if _n.startswith('p:'):
                        config_pipeline(_n.split('p:')[1], pipe, channel)
                    elif _n.startswith('b:'):
                        _p, _c = [], []
                        _p.extend(pipe)
                        _c.extend(channel)
                        for i in range(len(pipe)):
                            pipe.pop()
                        for i in range(len(channel)):
                            channel.pop()
                        _boardcast_result = config_boardcast(
                            _n.split('b:')[1], _pipe_name, _p, _c)
                        pipe.extend(_boardcast_result[0])
                        channel.extend(_boardcast_result[1])
                    elif _n.startswith('c:'):
                        continue
                    else:
                        if len(pipe) > 0 and isinstance(pipe[0], list):
                            for _i in range(len(pipe)):
                                pipe[_i].append(_n)
                        else:
                            pipe.append(_n)
                    try:
                        _align_channel = _aligns[_i + 1]
                        if _align_channel.startswith('c:'):
                            _channel_name = _align_channel.split('c:')[1]
                            if _channel_name not in cls.result_channel:
                                raise Exception(
                                    'Inline channel type not support, check Pipeline {}'.
                                    format(n))
                        else:
                            _channel_name = 'data'
                    except:
                        _channel_name = None
                    if _channel_name:
                        if len(channel) > 0 and isinstance(channel[0], list):
                            for _i in range(len(channel)):
                                channel[_i].append(_channel_name)
                        else:
                            channel.append(_channel_name)

            if not p.has_section('plugin:main'):
                return
            if not p.has_option('plugin:main', 'start'):
                return
            for name in p.get('plugin:main', 'start').split(' '):
                if not p.has_section('pipeline:{}'.format(name)):
                    continue
                if not p.has_option('pipeline:{}'.format(name), 'align'):
                    continue
                _pipelines, _channels = [], ['data']
                config_pipeline(name, _pipelines, _channels)

                plugin_realaction = lambda x: '.'.join([global_plugin[cls._plugin_realname(pn)], x.split('.')[1]]) if len(x.split('.')) > 1 else global_plugin[cls._plugin_realname(pn)]

                if len(_pipelines) > 0 and isinstance(_pipelines[0], list):
                    for _i, _pipeline in enumerate(_pipelines):
                        _pipeline = [
                            plugin_realaction(pn) for pn in _pipeline
                            if cls._plugin_realname(pn) in global_plugin
                            and global_plugin[cls._plugin_realname(pn)]
                        ]
                        cls.set_pipeline(name, _pipeline, _channels[_i], _i)
                else:
                    _pipelines = [
                        plugin_realaction(pn) for pn in _pipelines
                        if cls._plugin_realname(pn) in global_plugin
                        and global_plugin[cls._plugin_realname(pn)]
                    ]
                    cls.set_pipeline(name, _pipelines, _channels)

        init_plugin_config()
