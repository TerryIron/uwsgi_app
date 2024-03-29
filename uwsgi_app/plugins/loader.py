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

import collections


__version__ = (0, 1, 0)


class DictWrapper(collections.Mapping):

   def __init__(self, **data):
       self._data = data

   def __setattr__(self, key, value):
       if key == '_data':
           if not hasattr(self, key):
               return super(DictWrapper, self).__setattr__(key, value)
       else:
           return super(DictWrapper, self).__setattr__(key, value)

   def __getitem__(self, key):
       return self._data[key]

   def __len__(self):
       return len(self._data)

   def __iter__(self):
       return iter(self._data)


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
            def __init__(self, namespace, level=logging.NOTSET):
                self.logger = None
                logging.Logger.__init__(self, namespace, level=level)

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

        def get_logger(_name):
            logger = Logger(_name)
            return logger

        return get_logger(name)

    _LOGGER = None

    class Result(object):
        pass

    class Config(object):
        pass

    class Loader(object):
        pass

    import sys
    import os.path as op
    from gevent import monkey
    monkey.patch_all()
    from gevent.pool import Pool
    pool = Pool(1000)

    __plug_globals__ = {}  # 插件imports模块环境, 如{'pluginA': PLUGINA}
    __plug_libpath__ = {}  # 插件私有库环境, 如{'pluginA': LIBPATH}
    __plug_path__ = {}  # 插件私有配置环境, 如{'pluginA': CONFPATH}
    plugin_generator = {}  # 插件数据生成器配置, 如{'pluginA': {NAME: GENERATOR}}
    plugin_registry = {}  # 插件action入口, 如{'pluginA': {NAME: FUNC}}
    plugin_public_registry = {}  # 插件public_action配置, 如{'pluginA': [NAME]}
    plugin_imports = {}  # 插件init配置, 如{'pluginA': {ACTION: NAME.ACTION}}
    plugin_init = {}  # 插件init配置, 如{'pluginA': [NAME]}
    plugin_call = {}  # 插件call配置, 如{'pluginA': [NAME]}
    plugin_lang = {}  # 插件私有环境, 如{'pluginA': 'python'}
    plugin_loops = {}  # 插件自循环配置, 如{'pipelineA': LOOPINDEX}
    plugin_pipeline = {}  # 插件流程配置, 如{'pipelineA': [PLUGINS]}
    plugin_channels = {}  # 插件数据管道配置, 如{'pipelineA': [CHANNEL]}
    plugins = []  # 插件配置入口, [pipelineA, pipelineB]

    plugin_config = Config()
    plugin_runner_config = Config()
    plugin_loader = Loader()
    results = Result()
    config_channel = 'config'
    result_channel = tuple(['data', 'result'] + [config_channel])
    git_host = 'https://pypi.douban.com/simple/'

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
    def list_plugins(cls):
        return cls.__plug_globals__.keys()

    @classmethod
    def import_plugin(cls, name):
        _name = str(name)
        return cls.__plug_globals__[
            _name] if _name in cls.__plug_globals__ else None

    @classmethod
    def run_plugin(cls, name, call, data=[], **config):
        _plugin = cls.import_plugin(name)
        if _plugin and hasattr(_plugin, call) and callable(getattr(_plugin, call)):
            _call = getattr(_plugin, call)
            d = cls.Loader()
            setattr(d, 'config', DictWrapper(**config))
            setattr(d, 'channel_scope', cls.result_channel)
            setattr(d, 'config_channel', cls.config_channel)
            setattr(d, 'current_channel', cls.result_channel[0])
            setattr(d, 'logger', cls.get_logger('.'.join(['core', name])))
            setattr(d, 'logger_name', '.'.join(['core', name]))
            _config = dict()
            _config['config'] = dict()
            _config['result'] = tuple([dict()])
            if isinstance(data, (list, tuple)):
                _config['data'] = tuple([i for i in data])
            else:
                _config['data'] = tuple([data])
            return _call(d, **_config)

    @classmethod
    def set_pipeline(cls, name, plugin_names, channel_names, idx=None):
        _new_name = name if not idx else name + str(idx)
        if _new_name not in cls.plugins:
            cls.plugins.append(_new_name)
        else:
            raise Exception('Pipeline {} is already exist'.format(_new_name))
        cls.plugin_pipeline[_new_name] = [p for p in plugin_names]
        cls.plugin_channels[_new_name] = [p for p in channel_names]
        setattr(cls.plugin_runner_config, _new_name, dict())
        getattr(cls.plugin_runner_config, _new_name).update(
            getattr(cls.plugin_config, name))

        setattr(cls.results, _new_name, dict())
        d = cls.Loader()
        setattr(d, 'config', DictWrapper(**getattr(cls.plugin_runner_config, _new_name)))
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
        cls.plugin_generator[name] = dict(
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
    def install_patch(cls, plugin_home, requirement_file):
        import commands
        import os.path
        _file_path = os.path.join(plugin_home, requirement_file)
        if os.path.exists(_file_path):
            with open(_file_path) as f:
                data = [i for i in f.read().split('\n') if i]
                for ld in data:
                    if ld.startswith('+'):
                        if len(ld.split(':')) == 2:
                            _file_name = ld.split(':')[0][1:]
                            _target_name = ld.split(':')[1]
                            if not os.path.exists(_file_name) and os.path.exists(_target_name):
                                with open(_target_name) as f:
                                    d = f.read()
                                    with open(_file_name, 'w') as tf:
                                        tf.write(d)
                        else:
                            commands.getoutput('cd {} && touch {}'.format(plugin_home, ld[1:]))
                    elif ld.startswith('-'):
                        commands.getoutput('cd {} && rm -rf {}'.format(plugin_home, ld[1:]))
                    elif ld.startswith('='):
                        commands.getoutput('cd {} && patch -p0 < {}'.format(plugin_home, ld[1:]))

    @classmethod
    def install_lib(cls, plugin_home, requirement_file):
        import commands
        import os.path
        _file_path = os.path.join(plugin_home, requirement_file)
        if os.path.exists(_file_path):
            with open(_file_path) as f:
                data = [i for i in f.read().split('\n') if i]
                if data:
                    data = ' '.join(data)
                    _cmd = 'sudo apt install {}'.format(data)
                    commands.getoutput(_cmd)

    @classmethod
    def install_requirements(cls, plugin_home, requirement_file, git_host):
        import commands
        import os.path
        _file_path = os.path.join(plugin_home, requirement_file)
        if os.path.exists(_file_path):
            _cmd = 'cd {} && virtualenv env --no-site-packages ' \
                   '&&. env/bin/activate && pip install --global-option=build_ext ' \
                   '--global-option="-I/usr/include/x86_64-linux-gnu" --global-option="-L/usr/lib/x86_64-linux-gnu" -r {} -i {} && cd -'
            commands.getoutput(_cmd.format(plugin_home, requirement_file, git_host))

    @classmethod
    def reload_plugin(cls, loader, plugin_name, plugin_action, plugin_version='0.1.0', **kwargs):
        import os
        import json

        _globals = {}
        if plugin_name in cls.plugin_lang:
            _app_lang = cls.plugin_lang[plugin_name]
            _globals['sys'] = cls.get_plugin_import_path(plugin_name, _app_lang)

        if plugin_name in cls.__plug_globals__ \
                and plugin_name in cls.plugin_imports \
                and plugin_action in cls.plugin_imports[plugin_name] \
                and plugin_name in cls.plugin_generator \
                and plugin_action in cls.plugin_generator[plugin_name] \
                and plugin_name in cls.plugin_registry \
                and plugin_action in cls.plugin_registry[plugin_name]:

            plugin_path = cls.get_plugin_path()
            _plugin_home = os.path.join(plugin_path, plugin_name)

            app_config = os.path.join(_plugin_home, 'app.json')
            if not os.path.exists(_plugin_home):
                app_json = json.load(open(app_config))
                app_install = app_json.get('install',
                                           'install.txt')
                cls.install_lib(_plugin_home, app_install)
                app_requirements = app_json.get('imports',
                                                'requirements.txt')

                cls.install_requirements(_plugin_home, app_requirements, cls.git_host)
                app_patch = app_json.get('patch',
                                         'patch.txt')
                cls.install_patch(_plugin_home, app_patch)

            _import_names = cls.plugin_imports[plugin_name][plugin_action]
            _import_name = _import_names.split('.')[0]
            _mod = __import__(_import_names, _globals, {},
                              _import_name)
            _callable = getattr(_mod, plugin_action)
            if callable(_callable):
                cls.plugin_registry[plugin_name][plugin_action] = _callable
                cls.plugin_generator[plugin_name][plugin_action] = _callable

            import abc

            class PluginBase(object):
                __metaclass__ = abc.ABCMeta
                __name__ = plugin_name
                __version__ = plugin_version

            p = PluginBase()
            for n, f in cls.plugin_registry[plugin_name].items():
                if n not in cls.plugin_public_registry[plugin_name]:
                    continue
                setattr(p, n, f)
            cls.plugin_registry[plugin_name][cls.plugin_init[plugin_name]]()
            cls.__plug_globals__[plugin_name] = p
            cls._LOGGER.warn('Plugin:{} action:{}, version:{}'.format(plugin_name,
                                                                      plugin_action,
                                                                      plugin_version))
            return _callable(loader, **kwargs)

    @classmethod
    def init_plugins(cls, plugin_path=op.abspath(op.dirname(__file__))):
        return plugin_path

    @classmethod
    def get_plugin_path(cls, home='env'):
        import os.path
        _plugin_path_list = []
        _plugin_path = os.path.abspath(os.path.dirname(__file__))
        _plugin_split = _plugin_path.split('/')
        addable = True
        for i in _plugin_split:
            if i == home:
                addable = False
            if i.endswith('.egg'):
                addable = True
                continue
            if addable:
                _plugin_path_list.append(i)
        return '/'.join(_plugin_path_list)

    @classmethod
    def get_plugin_import_path(cls, name, lang='python2'):
        import os
        _plugin_path = cls.get_plugin_path()
        _lib_path = cls.__plug_libpath__.get(name, os.path.join(_plugin_path, name))
        reload(cls.sys)
        cls.sys.path = ['', _plugin_path]
        cls.sys.path.insert(1, os.path.join(_lib_path, 'env/lib/python2.7/site-packages'))
        cls.sys.path.insert(1, os.path.join(_lib_path, 'env/local/lib/python2.7/site-packages'))
        cls.sys.path.insert(1, '/usr/lib/python2.7/plat-x86_64-linux-gnu')
        cls.sys.path.insert(1, '/usr/lib/python2.7')
        cls.sys.path.insert(1, os.path.join(_lib_path, 'env/lib/python2.7/lib-dynload'))
        cls.sys.path.insert(1, os.path.join(_lib_path, 'env/lib/python2.7/lib-old'))
        cls.sys.path.insert(1, os.path.join(_lib_path, 'env/lib/python2.7/plat-x86_64-linux-gnu'))
        cls.sys.path.insert(1, os.path.join(_lib_path, 'env/lib/python2.7'))
        return cls.sys

    @classmethod
    def _plugin_environ(cls, name, entry):
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
        _env['__plugin__'] = cls.__plug_path__[name]
        _env['__plugin_module__'] = name
        _env['__call__'] = None
        _env['__error__'] = []
        _env['__result__'] = cls.results
        _env['__channels__'] = cls.result_channel[0:2]
        globals().clear()
        globals().update(_env)
        return _env

    @classmethod
    def run_python_plugin(cls, pipe_name, name, channel, index):
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
            import traceback
            import functools
            _reg_func = cls.plugin_registry[_name][func_name]
            _loop_func = cls.plugin_generator[_name][func_name]
            _real_func = _loop_func if index > 0 and _reg_func != _loop_func else _reg_func
            env = cls._plugin_environ(_name, _real_func)
            # call plugin function
            d = getattr(cls.plugin_loader, pipe_name)
            setattr(d, 'current_pipeline', cls.plugin_pipeline[pipe_name])
            setattr(d, 'reload_plugin', functools.partial(cls.reload_plugin, d))
            setattr(d, 'channel_scope', cls.result_channel)
            setattr(d, 'config_channel', cls.config_channel)
            setattr(d, 'current_channel', channel)
            setattr(d, 'logger', cls.get_logger('.'.join([pipe_name, _name])))
            setattr(d, 'logger_name', '.'.join([pipe_name, _name]))
            env['__loader__'] = d

            env['__pipe__'] = pipe_name
            _taction = _name + '.' + func_name
            env['__action__'] = _taction
            env['__func__'] = func_name
            import types
            env['types'] = types

            env['__runner__'] = False

            _expr = """
if not isinstance({1}, types.GeneratorType) and not isinstance(__result__.{0}, types.GeneratorType):
    __kw__ = __result__.{0} if __result__.{0} else dict(data=dict(), result=dict(), config=dict())
    if 'config' not in __kw__:
        __kw__['config'] = dict()
    if 'data' not in __kw__:
        __kw__['data'] = dict()
    if 'result' not in __kw__:
        __kw__['result'] = dict()
    __kw__['data'] = tuple(__kw__['data']) if isinstance(__kw__['data'], list) else __kw__['data']
    __kw__['data'] = tuple([__kw__['data']]) if not isinstance(__kw__['data'], tuple) else __kw__['data']
    __kw__['result'] = tuple(__kw__['result']) if isinstance(__kw__['result'], list) else __kw__['result']
    __kw__['result'] = tuple([__kw__['result']]) if not isinstance(__kw__['result'], tuple) else __kw__['result']
    __result__.{0}, __runner__ = {1}({2}, **__kw__), True
            """
            exec(_expr.format(pipe_name, _name, '__loader__'), env)
            exec ('if __runner__: __call__ = {0}'.format(_name), env)

            env['__runner__'] = False
            try:
                exec (
                    'if isinstance({0}, types.GeneratorType): '
                    '__runner__, __call__, __error__ = True, {0}, {1}'.
                    format(_name, index), env)
                exec (
                    'if isinstance({1}, types.GeneratorType): __result__.{0} = {1}.next()'.
                    format(pipe_name, _name), env)
            except StopIteration:
                env['__error__'] = None
            except Exception as e:
                cls._LOGGER.error(traceback.format_exc())
                raise e

            if not env['__runner__']:
                try:
                    _expr_env = """
import os
os.environ['PYTHONOPTIMIZE'] = '1'
                    """
                    exec (_expr_env, env)
                    exec (
                        'if isinstance(__result__.{0}, types.GeneratorType): '
                        '__run__, __call__, __error__ = True, __result__.{0}, {1}'.
                        format(pipe_name, index), env)
                    exec (
                        'if isinstance(__result__.{0}, types.GeneratorType): '
                        '__result__.{0} = __result__.{0}.next()'.
                        format(pipe_name), env)
                except StopIteration:
                    env['__error__'] = None
                except Exception as e:
                    cls._LOGGER.error(traceback.format_exc())
                    raise e

            exec (
                'if isinstance(__error__, list) and not __error__ and __result__.{0}: __error__ = '
                '[Exception("Result Channel:" + c + '
                '" not found in Pipeline:" + __pipe__ + " Action:" + __action__) '
                'for c in __channels__ if c not in __result__.{0}]'.format(
                    pipe_name), env)
            exec (
                'if isinstance(__error__, list) and __error__: raise __error__[0]',
                env)

            _env = {}
            _env.update(env)
            _env.update(cls.globals)
            exec ('PluginLoader.plugin_generator[__plugin_module__].'
                  'update(dict({0}=__call__))'.format(env['__func__']), _env)
            exec ('if isinstance(__error__, int) and __pipe__ not in PluginLoader.plugin_loops: '
                  'PluginLoader.plugin_loops.update(dict({0}=__error__))'.format(pipe_name), _env)
            exec ('if __error__ is None and __pipe__ in PluginLoader.plugin_loops: '
                  'PluginLoader.plugin_loops.update(dict({0}=__error__))'.format(pipe_name), _env)
            exec ('PluginLoader.results = __result__', _env)

        call_plugin_func()

    @classmethod
    def run_plugins(cls):
        import os
        import multiprocessing
        __pids = []

        os.environ['PYTHONOPTIMIZE'] = '1'

        def kill_pid(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass

        def kill_process(*args, **kwargs):
            for _pid in __pids:
                kill_pid(_pid)

        cls.globals.update(globals())
        for p_entry in cls.plugins:
            _pipe_idx = [str(j) for j in range(1, len([i for i in cls.plugin_pipeline.keys() if i.startswith(p_entry)]))]
            if p_entry not in cls.plugin_pipeline:
                continue
            if p_entry not in cls.plugin_channels:
                continue
            if not hasattr(cls.results, p_entry):
                setattr(cls.results, p_entry, {})

            def _run_pipeline(_entry, idx=0):
                for i, p in enumerate(cls.plugin_pipeline[_entry][idx:]):
                    _p = cls._plugin_realname(p)
                    n = cls.plugin_channels[_entry][i]
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
                        cls.run_python_plugin(_entry, p, n, i)
                    else:
                        pass

            def _run_loop(_entry):
                _run_pipeline(p_entry)
                while _entry in cls.plugin_loops and cls.plugin_loops[_entry] is not None:
                    _run_pipeline(_entry, idx=cls.plugin_loops[_entry])

            _process = multiprocessing.Process(target=lambda: cls.pool.apply_async(_run_loop(p_entry)))
            _process.daemon = True
            _process.start()
            __pids.append(_process.pid)
            for pi_index in _pipe_idx:
                _process = multiprocessing.Process(target=lambda: cls.pool.apply_async(_run_loop(p_entry + pi_index)))
                _process.daemon = True
                _process.start()
                __pids.append(_process.pid)

        import signal
        signal.signal(signal.SIGTERM, kill_process)

        globals().clear()
        globals().update(cls.globals)
        import sys
        sys.path = cls.paths

    @classmethod
    def _load_plugins(cls, plugin_path):
        return cls.load_plugins(plugin_path)

    @classmethod
    def _run_plugins(cls):
        return cls.run_plugins()

    @classmethod
    def start_plugins(cls, load_eventloop=True):
        cls._LOGGER = cls.get_logger(__name__)
        _path = cls.init_plugins()

        def _start_plugins():
            cls._load_plugins(_path)
            if load_eventloop:
                cls._run_plugins()

        cls.pool.apply_async(_start_plugins())


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
        if hasattr(c, '__file__'):
            if not config.startswith('/'):
                config = os.path.join(os.path.dirname(getattr(c, '__file__')), config)
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
                    cls._LOGGER.info(
                        'Plugin:{} initalize and start'.format(_plugin_home))
                    _cmd = 'unzip {} -d {}'
                    commands.getoutput(_cmd.format(_plugin_path, plugin_path))

                    app_json = json.load(open(app_config))
                    app_install = app_json.get('install',
                                               'install.txt')
                    cls.install_lib(_plugin_home, app_install)
                    app_requirements = app_json.get('imports',
                                                    'requirements.txt')

                    cls.install_requirements(_plugin_home, app_requirements, cls.git_host)
                    app_patch = app_json.get('patch',
                                             'patch.txt')
                    cls.install_patch(_plugin_home, app_patch)
                else:
                    cls._LOGGER.info('Plugin:{} start'.format(_plugin_home))
                    app_json = json.load(open(app_config))

                app_name = app_json.get('name', '')
                if not app_name:
                    raise Exception(
                        'plugin {} app_name not found'.format(_home))
                global_plugin[s.split('app:')[1]] = app_name

                app_env = os.path.join(_plugin_home, 'env/lib/python2.7')
                app_lang = app_json.get('lang', 'python2')
                cls._LOGGER.info('App:{} lanuage:{}'.format(
                    app_name, app_lang))
                app_version = app_json.get('version', '0.1.0')
                cls._LOGGER.info('App:{} version:{}'.format(
                    app_name, app_version))
                app_actions = []
                _globals = {}
                _globals['sys'] = cls.get_plugin_import_path(app_name, app_lang)
                _mods = {}
                for k, v in app_json.get('actions', {}).items():
                    _callable_name = v.split('.')[-1]
                    _callable_mod = v.split('.')[-2]
                    _callable_mods = '.'.join([app_name] + v.split('.')[:-1])
                    try:
                        cls._LOGGER.info('App:{} import action:{} {}'.format(
                            app_name, k, v))
                        if app_name not in _mods:
                            _mod = __import__(_callable_mods, _globals, {},
                                              _callable_mod)
                            _mods[app_name] = _mod
                        else:
                            _mod = _mods[app_name]
                        _callable = getattr(_mod, _callable_name)
                        if app_name not in cls.plugin_imports:
                            cls.plugin_imports[app_name] = {}
                        cls.plugin_imports[app_name][_callable_name] = _callable_mods
                    except Exception as e:
                        import traceback
                        cls._LOGGER.error(traceback.format_exc())
                        raise Exception(
                            'App:{} inline function:{} {} not found'.format(
                                app_name, k, v))
                    d = (k, _callable)
                    app_actions.append(d)
                app_public_actions = app_json.get('public_actions', [])
                cls._LOGGER.info('App:{} public actions:{}'.format(
                    app_name, app_public_actions))
                app_init = app_json.get('init', None)
                cls._LOGGER.info('App:{} init action:{}'.format(
                    app_name, app_init))
                app_call = app_json.get('call', None)
                cls._LOGGER.info('App:{} default action:{}'.format(
                    app_name, app_call))
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
                    else:
                        getattr(cls.plugin_config, pipe_name)[_o] = p.get(pipe_name, _o)
                _aligns = p.get(_boardcast_name, 'align').split(' ')
                for _ai, _n in enumerate(_aligns):
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
                    else:
                        getattr(cls.plugin_config, n)[_o] = p.get(_pipe_name, _o)

                _aligns = p.get(_pipe_name, 'align').split(' ')
                for _ai, _n in enumerate(_aligns):
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
                            for _pi in range(len(pipe)):
                                pipe[_pi].append(_n)
                        else:
                            pipe.append(_n)
                    try:
                        _align_channel = _aligns[_ai + 1]
                        if _align_channel.startswith('c:'):
                            _channel_name = _align_channel.split('c:')[1]
                            if _channel_name not in cls.result_channel[0:2]:
                                raise Exception(
                                    'Inline channel type not support, check Pipeline {}'.
                                    format(n))
                        else:
                            _channel_name = 'data'
                    except Exception as e:
                        _channel_name = None
                    if _channel_name:
                        if len(channel) > 0 and isinstance(channel[0], list):
                            for _ci in range(len(channel)):
                                channel[_ci].append(_channel_name)
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

                _build_action = lambda x: '.'.join([global_plugin[cls._plugin_realname(x)], x.split('.')[1]])
                plugin_realaction = lambda x: _build_action(x) if len(x.split('.')) > 1 else global_plugin[
                    cls._plugin_realname(x)]
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
