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

import tornado.web
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

from uwsgi_app.config import confprobe, classprobe
from uwsgi_app.framework.tornado_app import call_later
from uwsgi_app.plugins.loader import PluginLoaderV1


@classprobe('start')
class PluginLoaderV1(tornado.web.RequestHandler, PluginLoaderV1):
    executor = ThreadPoolExecutor(1000)

    @classmethod
    @call_later(2)
    @run_on_executor
    def start(cls):
        cls.start_plugins()

    @classmethod
    def load_plugins(cls, plugin_path):
        c = confprobe()
        cls.load_plugins_from_config(c)
