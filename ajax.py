# -*- coding: utf-8 -*-

# ************************************************************* 
# CheckNerds - www.checknerds.com
# version 1.2, codename Arizona
# - ajax.py
# Author: CNBorn, 2008-2011
# http://cnborn.net, http://twitter.com/CNBorn
# ************************************************************* 

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import cgi, datetime, os
from models import tarsusaUser
from base import tarsusaRequestHandler
from google.appengine.ext.webapp import template

from tarsusaCore import format_done_logs, format_items
from django.utils import simplejson as json
from utils import login

class ajax_error(tarsusaRequestHandler):
    def post(self):
        self.write("载入出错，请刷新重试")
    def get(self):
        self.write("载入出错，请刷新重试")

class render(tarsusaRequestHandler):
    @login
    def get(self):
        func = self.request.get("func")
        
        maxitems = int(self.request.get("maxitems", "15"))
        
        user = self.get_user_db()
        user_id = user.key().id()

        if func == "done":
            self.response.headers.add_header('Content-Type', "application/json")
            done_items = user.get_done_items(maxitems)
            self.write(json.dumps(format_items(done_items)))
            return 

        elif func == "undone":
            self.response.headers.add_header('Content-Type', "application/json")
            before_item_id = self.request.get("before_item_id",None)
            if before_item_id:
                undone_items = user.get_more_undone_items(maxitems, before_item_id)
            else:
                undone_items = user.get_undone_items(maxitems)
            self.write(json.dumps(format_items(undone_items)))
            return 

        elif func == "dailyroutine":
            dailyroutine_items = tarsusaUser.get_user(user_id).get_items_duetoday()
            self.write(json.dumps(format_items(dailyroutine_items)))
            return 

        elif func == "logs":
            done_items = user.get_donelog()
            formatted_done_items = format_done_logs(done_items)
            self.response.headers.add_header('Content-Type', "application/json")
            self.write(json.dumps(formatted_done_items))
            return 
 
class sidebar(tarsusaRequestHandler):
    @login
    def get(self):
        current_user = self.get_user_db()
        template_values = {}

        operation_name = self.request.get("obj")
        template_name = self.request.get("template")

        if operation_name == 'user':
            template_values['UserInTemplate'] = current_user
            template_values['tarsusaItemCollection_Statstics'] = current_user.get_itemstats()

        template_values['UserNickName'] = cgi.escape(current_user.dispname)
        template_values['UserID'] = current_user.key().id()
        template_values['htmltag_today'] = datetime.date.today() 
        path = os.path.join(os.path.dirname(__file__), 'pages/%s/ajax_sidebar_%s.html' % (template_name, operation_name))
        self.write(template.render(path, template_values))


def main():
    application = webapp.WSGIApplication([
        (r'/ajax/render/.*', render),
        (r'/ajax/sidebar/.*', sidebar),
        ('/ajax/.+',ajax_error)],
    debug=True)


    run_wsgi_app(application)

if __name__ == "__main__":
    main()
