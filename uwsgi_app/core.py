#!/usr/bin/env python
# coding=utf-8
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
import functools
import logging

logger = logging.getLogger(__name__)


def with_version(version_id, name):
    """
    用于定义接口版本

    :param version_id: 版本号
    :param name: 接口名称
    :return:
    """

    if '/' in name:
        return '/' + str(version_id) + str(name)
    else:
        return str(name) + '_' + str(version_id)


def get_settings(s, config_key=None, to_json=False):
    """
    获取配置参数
    :param s: 配置表
    :param config_key: 配置字段
    :param to_json: 是否转为Json
    :return:
    """

    d = s
    if config_key:
        d = d.get(config_key, '')
    if to_json:
        d = json.loads(d if d else '{}')
    return d


def check_request_params(arg_name,
                         need_exist=True,
                         or_exist_args=None,
                         arg_parser=None,
                         default_value=None,
                         err_result=None,
                         expect_values=None,
                         expect_request_arg_name=None,
                         expect_arg_name=None,
                         expect_out_name=None,
                         unexpected_values=None,
                         unexpected_request_arg_name=None,
                         unexpected_arg_name=None,
                         unexpected_out_name=None,
                         out_param_name='dict',
                         out_values_param_name='parm',
                         request_target=None,
                         request_target_arg_name='params'):
    """
    用于检查和处理请求参数

    :param arg_name: 请求参数名称
    :param need_exist: 是否必须
    :param or_exist_args: 可用于替代的请求参数名称列表
    :param arg_parser: 请求参数处理函数, 返回可用于以下判断函数
    :param default_value: 默认值或默认函数
    :param err_result: 参数错误返回结果
    :param expect_values: 参数可接受范围的判断函数
    :param expect_request_arg_name: 请求对象参数可用于判断函数（可接受范围）
    :param expect_arg_name: 参数可用于判断函数（可接受范围）
    :param expect_out_name: 可接受判断函数输出变量名
    :param unexpected_values: 参数不可接受范围或函数
    :param unexpected_request_arg_name: 请求对象参数可用于判断函数（不可接受范围）
    :param unexpected_arg_name: 参数可用于判断函数（不可接受范围）
    :param unexpected_out_name: 不可接受函数输出变量名
    :param out_param_name: 请求参数保存变量对象名称
    :param out_values_param_name: 请求期望或非期望值保存对象
    :param request_target: 请求对象
    :param request_target_arg_name: 请求对象参数
    :return:
    """

    err_result = err_result if err_result else []

    def _request_checker(func):
        class NotFound(object):
            pass

        @functools.wraps(func)
        def __request_checker(request, *args, **kwargs):
            _request = None
            if request_target:
                _request = request
                request = request_target
            if hasattr(request, 'request'):
                _request = request
                request = _request.request
            logger.info('request:{0} check on {1}, params:{2}'.format(
                request, arg_name, getattr(request, request_target_arg_name)))
            if not hasattr(request, out_values_param_name):
                setattr(request, out_values_param_name, {})
            if default_value is not None:
                _arg_value = request.params.get(
                    arg_name,
                    default_value()
                    if callable(default_value) else default_value)
            else:
                _arg_value = getattr(request, request_target_arg_name).get(arg_name, NotFound())
            if need_exist and isinstance(_arg_value, NotFound):
                _need_back = True
                if or_exist_args:
                    for _or_exist in or_exist_args:
                        if getattr(request, request_target_arg_name).get(_or_exist):
                            _need_back = False
                            break
                if _need_back:
                    logger.error(
                        'check arg_name:{0} is not exist'.format(arg_name))
                    return err_result
            if callable(expect_values):
                if expect_request_arg_name:
                    _expect_value = expect_values(
                        getattr(request, expect_request_arg_name))
                else:
                    _expect_value = expect_values()
            else:
                _expect_value = expect_values
            if expect_arg_name:
                _expect_value = getattr(request, request_target_arg_name).get(expect_arg_name)
            if expect_out_name:
                _values_dict = getattr(request, out_values_param_name)
                _values_dict[expect_out_name] = _expect_value

            if callable(unexpected_values):
                if unexpected_request_arg_name:
                    _unexpected_value = unexpected_values(
                        getattr(request, unexpected_request_arg_name))
                else:
                    _unexpected_value = unexpected_values()
            else:
                _unexpected_value = unexpected_values
            if unexpected_arg_name:
                _unexpected_value = getattr(request, request_target_arg_name).get(unexpected_arg_name)
            if unexpected_out_name:
                _values_dict = getattr(request, out_values_param_name)
                _values_dict[unexpected_out_name] = _unexpected_value

            def _err_back(_key=None):
                if not _key:
                    logger.error(
                        'check arg_name:{0} failed, expect:{1}, unexpected:{2}'.
                        format(arg_name, _expect_value, _unexpected_value))
                else:
                    logger.error(
                        'check arg_name:{0} failed, error key:{1} expect:{2}, unexpected:{3}'.
                        format(arg_name, _key, _expect_value,
                               _unexpected_value))
                return err_result

            if _arg_value:
                if arg_parser and not isinstance(_arg_value, NotFound):
                    _arg_value = arg_parser(_arg_value)
                if isinstance(_arg_value, str) or isinstance(
                        _arg_value, unicode):
                    if _expect_value and _arg_value not in _expect_value:
                        return _err_back()
                    if _unexpected_value and _arg_value in _unexpected_value:
                        return _err_back()
                elif not isinstance(_arg_value, NotFound):
                    for _arg in _arg_value:
                        if _expect_value and _arg not in _expect_value:
                            return _err_back(_arg)
                        if _unexpected_value and _arg in _unexpected_value:
                            return _err_back(_arg)
            if not hasattr(request, out_param_name):
                setattr(request, out_param_name, {})
            _request_dict = getattr(request, out_param_name)
            _request_dict[arg_name] = _arg_value
            logger.info('request check off {0}, params:{1}'.format(
                arg_name, getattr(request, request_target_arg_name)))
            if _request:
                request = _request
            return func(request, *args, **kwargs)

        return __request_checker

    return _request_checker


def filter_session(autoremove):
    """
    用于处理会话

    :param autoremove: 自动释放会话资源
    :return:
    """

    def _filter_session(func):
        @functools.wraps(func)
        def __filter_session(*args, **kwargs):
            if len(args) == 2:
                root_factory, request = args
            else:
                request = args[0]

            ret = func(request, **kwargs)
            if autoremove:
                if not hasattr(request, 'dbsession'):
                    if hasattr(request, 'request'):
                        request = getattr(request, 'request')
                if hasattr(request, 'dbsession'):
                    _session = getattr(request, 'dbsession')
                    from zope.sqlalchemy import mark_changed
                    mark_changed(_session)
                    # if hasattr(_session, 'close'):
                    #     _session.close()
            logger.info('Response:{0}'.format(ret))
            return ret

        return __filter_session

    return _filter_session
