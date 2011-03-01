# -*- coding: utf-8 -*-

# ************************************************************* 
# CheckNerds - www.checknerds.com
# version 1.0, codename California
# - miscellaneous.py
# Copyright (C) CNBorn, 2008-2010
# http://cnborn.net, http://twitter.com/CNBorn
# ************************************************************* 

import os
import sys

import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template

import datetime

from modules import *
from base import *

import memcache
import logging
import tarsusaCore

class GuestbookPage(tarsusaRequestHandler):
    def get(self):
        strAboutPageTitle = "Guestbook"
        strAboutPageContent = '''<br /><iframe src="http://spreadsheets.google.com/embeddedform?key=pWd4_W1-LSL4xnGNRuHq6JA" width="95%" height="735" frameborder="0" marginheight="0" marginwidth="0">正在加载...</iframe><BR>
        
        '''
        if self.chk_login():
            CurrentUser = self.get_user_db()        
            template_values = {
                    'UserLoggedIn': 'Logged In',
                    'UserNickName': cgi.escape(CurrentUser.dispname),
                    'UserID': CurrentUser.key().id(),
                    'singlePageTitle': strAboutPageTitle,
                    'singlePageContent': strAboutPageContent,
            }
        
        else:
            template_values = {
                'UserNickName': "访客",
                'AnonymousVisitor': "Yes",
                'singlePageTitle': strAboutPageTitle,
                'singlePageContent': strAboutPageContent,
            }

        path = os.path.join(os.path.dirname(__file__), '../pages/calit2/simple_page.html')
        self.write(template.render(path, template_values))

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
            pageid = 'index'
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
    


class FlushCache(tarsusaRequestHandler):
    def get(self):
        from google.appengine.api import memcache 
        memcache.flush_all()
        logging.info("Memcache Flushed by force.")
        self.redirect('/')

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
                                       ('/flushcache', FlushCache),
                                       ('/cron_flushcache', cron_flushcache),
                                       ('/guestbook', GuestbookPage)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
