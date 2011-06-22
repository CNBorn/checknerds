# -*- coding: utf-8 -*-

import cgi
import wsgiref.handlers
from google.appengine.ext.webapp import template

import sys
sys.path.append("../")
from base import *
import os

class Error404(tarsusaRequestHandler):
    def get(self):
        self.error(404)
        if self.chk_login():
            CurrentUser = self.get_user_db()        
            template_values = {
                    'UserLoggedIn': 'Logged In',
                    'UserNickName': cgi.escape(CurrentUser.dispname),
                    'UserID': CurrentUser.key().id(),
            }
        
        else:           
            template_values = {
                'UserNickName': "访客",
                'AnonymousVisitor': "Yes",
            }

        template_values['singlePageTitle'] = "页面没有找到"
        template_values['singlePageContent'] = "此页面内容不存在"
        path = '../pages/calit2/simple_page.html'
        self.response.out.write(template.render(path, template_values)) 

def main():
    application = webapp.WSGIApplication([('/.*', Error404)]
                                       , debug=True)

    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
