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


import sqlalchemy
from sqlalchemy import create_engine, engine_from_config
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import configure_mappers
import zope.sqlalchemy
from zope.sqlalchemy import ZopeTransactionExtension
import transaction
import urlparse
import pymongo
import pymssql
import happybase

# import or define all models here to ensure they are attached to the
# Base.metadata prior to any initialization routines
from .meta import Base as Base

# run configure_mappers after defining all of the models to ensure
# all relationships can be setup
configure_mappers()


def _engine_from_config(configuration, prefix='sqlalchemy.', **kwargs):
    from sqlalchemy.pool import NullPool
    _kwargs = {}
    _kwargs.update(configuration)
    _kwargs['{}poolclass'.format(prefix)] = NullPool
    _kwargs['{}pool_recycle'.format(prefix)] = 7200
    return engine_from_config(_kwargs, prefix=prefix, **kwargs)


sqlalchemy.engine_from_config = _engine_from_config


__all__ = [
    'Engine', 'EngineFactory', 'Table', 'get_engine', 'get_sqlalchemy_engine',
    'get_hbase_engine', 'get_mongodb_engine', 'get_sqlserver_engine',
    'create_tables', 'get_session_factory', 'get_tm_session', 'get_mod_tables'
]


def _get_pointed_value(settings, prefix):
    """
    获取配置特性

    :param settings: 配置表
    :param prefix: 特征字段
    :return:
    """

    for k, v in settings.items():
        if prefix in k:
            return v.strip()
    return ''


def get_mod_tables(mod):
    """
    获取模块内表对象

    :param mod: 模块对象
    :return:
    """

    _n = []
    for d in dir(mod):
        n = getattr(mod, d)
        if n and hasattr(n, '__tablename__'):
            t = Table(n)
            if t not in _n:
                _n.append(t)
    return _n


def _parse_create_tables(engine, mod):
    """
    创建表

    :param engine: 数据引擎代理对象
    :param mod: 模块路径
    :return:
    """

    mod = __import__(mod, globals(), locals(), mod.split('.')[-1])
    create_tables(engine, mod)


class Engine(object):
    """
    数据引擎代理
    """

    def __init__(self, s, name='', engine=None):
        """
        数据引擎初始化
        :param engine: 数据引擎工厂函数入口
        :param name: 数据引擎名称
        """

        self._session = s
        self._engine = engine
        self.name = name

    @property
    def engine_factory(self):
        """
        数据引擎工厂函数
        :return:
        """

        return self._engine

    @property
    def session(self):
        """
        数据引擎会话/连接
        :return:
        """

        _instance = self._session if not callable(
            self._session) else self._session()
        if hasattr(_instance, 'open') and callable(getattr(_instance, 'open')):
            _instance.open()

        import transaction

        def _commit(*args, **kwargs):
            transaction.commit()

        _instance.commit = _commit
        return _instance

    @property
    def engine(self):
        """
        数据引擎实例
        :return:
        """

        _instance = self._engine if not callable(
            self._engine) else self._engine()
        if hasattr(_instance, 'open') and callable(getattr(_instance, 'open')):
            _instance.open()
        return _instance


class EngineFactory(object):
    """
    数据引擎工厂类
    """

    def __init__(self, factory, name='', engine=None):
        self.factory = factory
        self.name = name
        self.engine = engine


class Table(object):
    """
    数据表对象
    :param inst: 数据模型实例
    """

    def __init__(self, inst):
        self.name = getattr(inst, '__tablename__')
        self.inst = inst
        self.columns = [
            c for c in dir(inst)
            if not c.startswith('_') and c != 'id' and c != 'metadata'
        ]


def _get_engine(settings, prefix='sql.'):
    """
    生成数据引擎代理实例
    :param settings: 配置表
    :param prefix: 特征
    :return:
    """

    value = _get_pointed_value(settings, prefix)
    if value.startswith('hbase:'):
        return get_hbase_engine(value)
    else:
        _engine = sqlalchemy.engine_from_config(settings, prefix)
        return Engine(sessionmaker(_engine), 'sqlalchemy', _engine)


def get_engine(url):
    """
    生成数据引擎代理实例
    :param url: 数据库地址
    :return:
    """
    if url.startswith('hbase:'):
        return get_hbase_engine(url)
    elif url.startswith('mongodb:'):
        return get_mongodb_engine(url)
    elif url.startswith('sqlserver:'):
        return get_sqlserver_engine(url)
    else:
        return get_sqlalchemy_engine(url)


def get_hbase_engine(url):
    """
    生成Hbase数据引擎代理实例
    :param url: 数据库地址
    :return:
    """

    import urlparse
    _p = urlparse.urlparse(url)
    return Engine(
        lambda: happybase.Connection(
            host=_p.hostname,
            port=int(
                _p.port),
            autoconnect=False),
        'hbase')


def get_sqlalchemy_engine(url):
    """
    生成Sqlalchemy数据引擎代理实例
    :param url: 数据库地址
    :return:
    """

    _engine = create_engine(url)
    return Engine(sessionmaker(bind=_engine, extension=ZopeTransactionExtension()), 'sqlalchemy', _engine)


def get_sqlserver_engine(url):
    """
    获取sqlserver数据引擎
    :param url: 数据库地址
    :return:
    """

    _d = urlparse.urlparse(url)
    _username, _password, _database = None, None, None
    for i in _d.netloc.split(';'):
        if i.startswith('user='):
            _username = i.split('user=')[1]
            continue
        if i.startswith('password='):
            _password = i.split('password=')[1]
            continue
        if i.startswith('databaseName='):
            _database = i.split('databaseName=')[1]
            continue
    _host = _d.hostname
    _port = _d.netloc.split(':')
    if len(_port) > 1:
        _port = _port[1]
        _port = int(_port.split(';')[0])
    else:
        _port = 1433
    conn = pymssql.connect(
        host=_host,
        port=_port,
        user=_username,
        password=_password,
        database=_database,
        charset='utf8')
    return Engine(lambda: conn.cursor(as_dict=True), 'sqlserver')


def get_mongodb_engine(url):
    """
    获取mongodb数据引擎
    :param url: 数据库地址
    :return:
    """

    _p = urlparse.urlparse(url)
    _db, _table = _p.path.lstrip('/').split('.')
    return Engine(lambda: pymongo.MongoClient(url)[_db][_table], 'mongodb')


def create_tables(engine, mod=None):
    """
    创建数据引擎中模型, 最好先导入模型模块
    :param engine: 数据引擎代理
    :param mod: 指定模块支持第三方
    :return:
    """

    if engine.name == 'hbase':
        mod_instances = get_mod_tables(mod)
        _tables = engine.session.tables()
        for m in mod_instances:
            if m.name not in _tables:
                family = {}
                for c in m.columns:
                    if c not in family:
                        family[c] = {}
                engine.session.create_table(m.name, family)
    else:
        if mod and hasattr(mod, 'Base'):
            getattr(mod, 'Base').metadata.create_all(engine.engine)
        else:
            Base.metadata.create_all(engine.engine)


def _create_tables(engine, settings, prefix='model.'):
    """
    创建数据引擎中模型, 最好先导入模型模块
    :param engine: 数据引擎代理
    :param settings: 配置表
    :param prefix: 特征
    :return:
    """

    value = _get_pointed_value(settings, prefix)
    if not value:
        return
    _parse_create_tables(engine, value)


def get_session_factory(engine):
    """
    获取数据引擎工厂

    :param engine: 数据引擎代理
    :return:
    """

    if engine.name == 'hbase':
        return EngineFactory(engine.session_factory, engine.name)
    else:
        factory = sessionmaker()
        factory.configure(bind=engine.engine)
        return EngineFactory(factory, engine.name, engine.engine)


def get_tm_session(session_factory, transaction_manager):
    """
    Get a ``sqlalchemy.orm.Session`` instance backed by a transaction.

    This function will hook the session to the transaction manager which
    will take care of committing any changes.

    - When using pyramid_tm it will automatically be committed or aborted
      depending on whether an exception is raised.

    - When using scripts you should wrap the session in a manager yourself.
      For example::

          import transaction

          engine = _get_engine(settings)
          session_factory = get_session_factory(engine)
          with transaction.manager:
              dbsession = get_tm_session(session_factory, transaction.manager)

    """
    dbsession = session_factory.factory()
    if session_factory.name == 'hbase':
        dbsession.open()
        return dbsession
    else:
        zope.sqlalchemy.register(
            dbsession, transaction_manager=transaction_manager)
        setattr(dbsession, 'engine', session_factory.engine)
        return dbsession


def includeme(config):
    """
    Initialize the model for an application.

    Activate this setup using ``config.include('PROJECT.models')``.

    """

    try:
        settings = config.settings
    except:
        settings = config.get_settings()
    engine = _get_engine(settings=settings)
    session_factory = get_session_factory(engine=engine)
    _create_tables(engine=engine, settings=settings)
    config.registry['dbsession_factory'] = session_factory

    def _call(**kwargs):
        engine = _get_engine(settings=settings)
        session_factory = get_session_factory(engine=engine)
        return get_tm_session(session_factory, transaction.manager)

    config.add_request_method(
        # r.tm is the transaction manager used by pyramid_tm
        _call, 'dbsession',
        reify=True)
