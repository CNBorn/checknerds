# -*- coding: utf-8 -*-
import os
import cgi
import logging

import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from base import tarsusaRequestHandler

class AboutPage(tarsusaRequestHandler):
    def get(self):
        strdevVersion = os.environ['CURRENT_VERSION_ID']
        if self.chk_login():
            CurrentUser = self.get_user_db()        
            template_values = {
                    'UserLoggedIn': 'Logged In',
                    'UserNickName': cgi.escape(CurrentUser.dispname),
                    'UserID': CurrentUser.key().id(),
                    'devVersion': strdevVersion,
            }
        else:           
            template_values = {
                'UserNickName': "访客",
                'AnonymousVisitor': "Yes",
                'devVersion': strdevVersion,
            }
        path = os.path.join(os.path.dirname(__file__), '../pages/calit2/about.html')
        self.response.out.write(template.render(path, template_values))

class DocsPage(tarsusaRequestHandler):
    def get(self):

        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login():
            CurrentUser = self.get_user_db()        
            template_values = {
                    'PrefixCSSdir': "/",
                    'UserLoggedIn': 'Logged In',
                    'UserNickName': cgi.escape(CurrentUser.dispname),
                    'UserID': CurrentUser.key().id(),
            }
        
        else:           
            template_values = {
                'PrefixCSSdir': "/",
                'UserNickName': "访客",
                'AnonymousVisitor': "Yes",
            }
        
        pageid = self.request.path[len('/docs/'):]
        if pageid == '':
            pageid = 'docs_index'
        path = os.path.join(os.path.dirname(__file__), '../pages/calit2/docs/' + pageid + '.html')

        self.response.out.write(template.render(path, template_values))

class LabsPage(tarsusaRequestHandler):
    def get(self):

        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login():
            CurrentUser = self.get_user_db()        
            template_values = {
                    'PrefixCSSdir': "/",
                    'UserLoggedIn': 'Logged In',
                    'UserNickName': cgi.escape(CurrentUser.dispname),
                    'UserID': CurrentUser.key().id(),
            }
        
        else:           
            template_values = {
                'PrefixCSSdir': "/",
                'UserNickName': "访客",
                'AnonymousVisitor': "Yes",
            }
        
        pageid = self.request.path[len('/docs/'):]
        if pageid == '':
            pageid = 'index'
        path = os.path.join(os.path.dirname(__file__), '../pages/labs/index.html')

        self.response.out.write(template.render(path, template_values))


class cron_flushcache(tarsusaRequestHandler):
    def get(self):
        from google.appengine.api import memcache 
        memcache.flush_all()
        logging.info("memcache flushed by cron.")
        return True

def main():
    application = webapp.WSGIApplication([('/about',AboutPage),
                                       ('/docs.+', DocsPage),
                                       ('/labs.+', LabsPage),
                                       ('/cron_flushcache', cron_flushcache)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
