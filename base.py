# -*- coding: utf-8 -*-
import os

from google.appengine.dist import use_library
use_library('django', '1.2')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.conf import settings 

views_path = os.path.join(os.path.dirname(__file__), 'pages/calit2')
settings.TEMPLATE_LOADERS = (('libs.templateloader.MvcTemplateLoader', views_path), 'django.template.loaders.filesystem.Loader', 'django.template.loaders.app_directories.Loader')

#Remove the standard version of Django
#for k in [k for k in sys.modules if k.startswith('django')]:
#    del sys.modules[k]

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext import db

import cgi
import logging

from libs import shardingcounter

class tarsusaRequestHandler(webapp.RequestHandler):
    from utils import cache
    def __init__(self):
        pass

    def initialize(self, request, response):
        webapp.RequestHandler.initialize(self, request, response)
        
        self.login_user = users.get_current_user()
        self.is_login = (self.login_user != None)
        
        if self.is_login:
            self.user = self.get_user_db()
        else:
            self.user = None

        try:
            self.referer = self.request.headers['referer']
        except:
            self.referer = None

    def write(self, s):
        self.response.out.write(s)

    def response_json(self, object):
        from django.utils import simplejson as json
        self.response.headers.add_header('Content-Type', "application/json")
        self.write(json.dumps(object))
    
    @property
    def host(self):
        if os.environ.get('HTTP_HOST'):
          return os.environ['HTTP_HOST']
        else:
          return os.environ['SERVER_NAME'] 

    def get_login_url(self, from_referer=False):
        if from_referer:
            return users.create_login_url(self.referer)
        else:
            return users.create_login_url(self.request.uri)

    def get_logout_url(self, from_referer=False):
        if from_referer:
            return users.create_logout_url(self.referer)
        else:
            return users.create_logout_url(self.request.uri)
    
    def chk_login(self):
        self.login_user = users.get_current_user()
        self.is_login = (self.login_user != None)

        if self.is_login:
            if not self.get_user_db():
                self.create_user(users.get_current_user())
            return True

    def create_user(self, user):
        from models import tarsusaUser
        CurrentUser = tarsusaUser(user=user, urlname=cgi.escape(user.nickname()))
        CurrentUser.put()
        CurrentUser.userid = CurrentUser.key().id()
        CurrentUser.dispname = user.nickname()
        CurrentUser.put()
        logging.info("New User, id:" + str(CurrentUser.key().id()) + " name:" + CurrentUser.dispname)
        shardingcounter.increment("tarsusaUser")
        return CurrentUser

    @cache("userdb:{users.get_current_user().user_id()}")
    def get_user_db(self):
        return db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user()).get()

    def response_status(self, status_code, status_info=None, return_value=False):
        '''
        Set the response status & its info, and return the specify result state
        mainly used in service.py, sample usage:
            return self.response_status(404, 'No such Item', False) 
            #This line returns False, because of the third para in the function
        '''
        self.response.set_status(status_code)
        self.write(status_info)
        return return_value
