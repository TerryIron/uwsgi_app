import tornado.web

from uwsgi_app.core import check_request_params


class MainHandler(tornado.web.RequestHandler):

    @check_request_params('test', need_exist=True,
                          request_target_arg_name='query_arguments')
    def get(self):
        print self.dbsession
        print self.request.body_arguments
        print self.request.query_arguments
        print dir(self.request)
        self.write("Hello, world")
