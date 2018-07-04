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

import ConfigParser


GLOBAL_CONFIG = {}


def confinit(**config):
    global GLOBAL_CONFIG
    GLOBAL_CONFIG.update(**config)


def confprobe(file_name=None):
    file_name = GLOBAL_CONFIG.get('__file__') if not file_name else file_name
    c = ConfigParser.ConfigParser()
    c.read(file_name)
    return c


def modprobe(mod):
    return __import__(mod, globals(), locals(), [mod.split('.')[-1]])


def get_config(c, sect='app:main'):
    return dict([(o, c.get(sect, o, None)) for o in c.options(sect)])


def singleton(cls, *args, **kw):
    instances = {}
    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton


def classprobe(entry_method, **kwargs):
    def _singleton(cls, *args, **kw):
        instances = {}
        if hasattr(cls, entry_method) and callable(getattr(cls, entry_method)):
            getattr(cls, entry_method)(**kwargs)
        def __singleton():
            if cls not in instances:
                instances[cls] = cls(*args, **kw)
            return instances[cls]
        return __singleton
    return _singleton
