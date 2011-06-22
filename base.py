# -*- coding: utf-8 -*-

# CheckNerds - www.checknerds.com
# - base.py
# http://cnborn.net, http://twitter.com/CNBorn

import os
import sys

# Remove the standard version of Django
#for k in [k for k in sys.modules if k.startswith('django')]:
#    del sys.modules[k]

from google.appengine.dist import use_library
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext import db

import cgi
import logging

from libs import shardingcounter
import memcache

class tarsusaRequestHandler(webapp.RequestHandler):
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

    def param(self, name, **kw):
        return self.request.get(name, **kw)

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
            dst = self.referer
            if not dst : dst = '/m'
            return users.create_login_url(dst)
        else:
            return users.create_login_url(self.request.uri)

    def get_logout_url(self, from_referer=False):
        if from_referer:
            dst = self.referer
            if not dst : dst = '/m'
            return users.create_logout_url(dst)
        else:
            return users.create_logout_url(self.request.uri)
    
    def chk_login(self, redirect_url='/'):
        self.login_user = users.get_current_user()
        self.is_login = (self.login_user != None)

        if self.is_login:
            CurrentUser = self.get_user_db()
            if not CurrentUser:
                CurrentUser = self.create_user(users.get_current_user())
            return True
        return False

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

    def get_user_db(self):
        userdb_id = users.get_current_user().user_id()
        cached_user = memcache.get("userdb:%s" % userdb_id)
        if cached_user:
            return cached_user
        
        q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
        result = q.get()
        memcache.set("userdb:%s" % userdb_id, result)
        return result

    def verify_api(self):
        apiappid = self.request.get('apiappid') 
        apiservicekey = self.request.get('servicekey')
        
        if apiappid == "" or apiservicekey == "":
            self.response_status(403, "403 Not enough parameters.")
            return False 
        
        from models import AppModel 
        verified = verify_AppModel(int(apiappid), apiservicekey)
        
        apiuserid = self.request.get('apiuserid') 
        apikey = self.request.get('apikey')
        userid = self.request.get('userid')
        
        from models import tarsusaUser
        APIUser = tarsusaUser.get_by_id(int(apiuserid))
        
        if APIUser == None:
            self.response_status(403, "403 No Such User")
            return False
        if verified == False:
            self.response_status(403, "403 Application Verifiction Failed.")
            return False
        if verify_UserApi(int(apiuserid), apikey) == False:
            self.response_status(403, "403 UserID Authentication Failed.")
            return False
        
        try:
            if APIUser.apikey == None:
                return False
        except:
            return False

        return True

    def verify_api_limit(self):
        
        apiappid = self.request.get('apiappid') 
        apiservicekey = self.request.get('servicekey')
    
        AppApiUsage = memcache.get_item("appapiusage", int(apiappid))
        from models import AppModel 
        ThisApp = AppModel.get_by_id(int(apiappid))
        if not ThisApp:
            self.response_status(404, "404 Application does not exist.")
            return False
        if AppApiUsage >= ThisApp.api_limit:
            self.response_status(403, '403 API Limitation exceed. ')
            return False    
        elif AppApiUsage == None:
            AppApiUsage = 0
        
        AppApiUsage += 1 
        memcache.set("appapiusage:%s" % apiappid, AppApiUsage)
        
        return True

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

## Used for API setting.

global_vars = {}
global_vars['apilimit'] = 400

