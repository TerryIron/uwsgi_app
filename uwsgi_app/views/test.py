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

from uwsgi_app.core import check_request_params, filter_session

import tornado.web


class MainHandler(tornado.web.RequestHandler):

    @check_request_params('test', need_exist=True,
                          request_target_arg_name='query_arguments')
    def get(self):
        print self.dbsession
        print dir(self.request)
        self.write("Hello, world")

# from flask_restful import Resource
# from flask import request
#
#
# class MainHandler(Resource):
#     @check_request_params('test', need_exist=True,
#                           request_target=request,
#                           request_target_arg_name='values')
#     @filter_session(autoremove=True)
#     def get(self):
#         print request.dbsession
#         print dir(request)
#         return {'hello': 'world'}
