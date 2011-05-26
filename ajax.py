# -*- coding: utf-8 -*-

# ************************************************************* 
# CheckNerds - www.checknerds.com
# version 1.2, codename Arizona
# - ajax.py
# Author: CNBorn, 2008-2011
# http://cnborn.net, http://twitter.com/CNBorn
# ************************************************************* 

import os
import cgi
import datetime
import wsgiref.handlers
import urllib
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from modules import *
from base import *
import logging

import tarsusaCore
from tarsusaCore import format_done_logs, format_items
import memcache
from models.user import get_user
from django.utils import simplejson as json

def userloggedin_or_403(function):
    '''
    Decorator:
        to check with UserLoggingIn
    '''
    def user_loggedin_warpper(tRequestHandler, *args, **kw):
        if tRequestHandler.chk_login():
            #CurrentUser = tRequestHadler.get_user_db()
            return function(tRequestHandler, *args, **kw)
        else:
        	return tRequestHandler.response_status(403,'You are not logged in.',False)
    return user_loggedin_warpper

class edititem(tarsusaRequestHandler):
    def get(self):

        urllen = len('/ajax/allpage_edititem/')
        RequestItemId = urllib.unquote(self.request.path[urllen:])
        user = users.get_current_user() 
    
        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login():
            CurrentUser = self.get_user_db()
        
        tItem = tarsusaItem.get_by_id(int(RequestItemId))
    
        if tItem.user == users.get_current_user():
            
            ## Handle Tags
            # for modified Tags (db.key)
            tItemTags = ''
            try:
                for each_tag in db.get(tItem.tags):
                    if tItemTags == '':
                        tItemTags += cgi.escape(each_tag.name)
                    else:
                        tItemTags += ',' + cgi.escape(each_tag.name)
            except:
                # There is some chances that ThisItem do not have any tags.
                pass    
            
            try:
                tItemExpectdate = datetime.datetime.date(tItem.expectdate)
            except:
                tItemExpectdate = None
            
            try:

                template_values = {
                    'tItemId': tItem.key().id(),
                    'tItemName': cgi.escape(tItem.name),
                    'tItemComment': cgi.escape(tItem.comment),
                    'tItemTag': tItemTags,
                    'tItemRoutine': tItem.routine,
                    'tItemExpectdate': tItemExpectdate, 
                    'tItemPublic': tItem.public,
                    }           

                #Manupilating Templates 
                path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_edititem.html')
                self.response.out.write(template.render(path, template_values))

            except:
                ## GAE Localhost Environment
                template_values = {
                    'tItemId': tItem.key().id(),
                    'tItemName': cgi.escape(tItem.name.encode('utf-8')),
                    'tItemComment': cgi.escape(tItem.comment.encode('utf-8')),
                    'tItemTag': tItemTags.encode('utf-8'),
                    'tItemRoutine': tItem.routine,
                    'tItemExpectdate': tItemExpectdate,
                    'tItemPublic': tItem.public,
                    }           

                #Manupilating Templates 
                path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_edititem.html')
                self.response.out.write(template.render(path, template_values)) 

        else:
            self.write("您没有登录或没有权限编辑该项目")

class ajax_error(tarsusaRequestHandler):
    def post(self):
        self.write("载入出错，请刷新重试")
    def get(self):
        self.write("载入出错，请刷新重试")

class admin_runpatch(tarsusaRequestHandler):
    def get(self):
        urllen = len('/ajax/admin_runpatch/')
        RequestUserID = urllib.unquote(self.request.path[urllen:])
        AppliedUser = tarsusaUser.get_by_id(int(RequestUserID))
        self.write('dispname: ' +  AppliedUser.dispname)
        import DBPatcher
        #Run DB Model Patch when User Logged in.
        DBPatcher.chk_dbmodel_update(AppliedUser)
        self.write('DONE with USERID' + RequestUserID)
        #self.redirect('/')

class render(tarsusaRequestHandler):
    @userloggedin_or_403
    def get(self):
        func = self.request.get("func")
        
        try:
            maxitems = int(self.request.get("maxitems"))
        except:
            maxitems = 15
        
        template_name = "calit2"

        user = self.get_user_db()
        user_id = user.key().id()

        template_values = {
            'UserNickName': cgi.escape(user.dispname),
            'UserID': user_id,
            'func': func,
        }

        user = get_user(user_id)
        if func == "done":
            self.response.headers.add_header('Content-Type', "application/json")
            done_items = user.get_done_items(maxitems)
            self.write(json.dumps(format_items(done_items)))
            return 

        elif func == "undone":
            self.response.headers.add_header('Content-Type', "application/json")
            before_item_id = self.request.get("before_item_id",None)
            if before_item_id:
                undone_items = tarsusaCore.get_more_undone_items(user_id, maxitems, before_item_id)
            else:
                undone_items = tarsusaUser.get_user(user_id).get_undone_items(maxitems)
            self.write(json.dumps(format_items(undone_items)))
            return 

        elif func == "dailyroutine":
            dailyroutine_items = tarsusaUser.get_user(user_id).get_items_duetoday()
            self.write(json.dumps(format_items(dailyroutine_items)))
            return 

        elif func == "friends":
            UserFriendsItem_List = tarsusaCore.get_UserFriendStats(user_id)
            template_values['UserFriendsActivities'] = UserFriendsItem_List
            template_kind = "friends_list"
        
        elif func == "logs":
            done_items = user.get_donelog()
            formatted_done_items = format_done_logs(done_items)
            self.response.headers.add_header('Content-Type', "application/json")
            self.write(json.dumps(formatted_done_items))
            return 
 
        path = 'pages/%s/ajax_content_%s.html' % (template_name, template_kind)
        self.write(template.render(path, template_values))


class sidebar(tarsusaRequestHandler):
    @userloggedin_or_403
    def get(self):
        ''' Ajax Functions suites for multiple usage for Calit2 template in sidebar.'''
        current_user = self.get_user_db()
        template_values = {}

        operation_name = self.request.get("obj")
        template_name = self.request.get("template")

        if operation_name == 'user':
            #Cache is a MUST!
            template_values['UserInTemplate'] = current_user
            cached_useritem_stats = current_user.get_itemstats()
            template_values['tarsusaItemCollection_Statstics'] = cached_useritem_stats

        elif operation_name == 'item':
            itemid = self.request.get("id")
            item_in_template = tarsusaItem.get_item(itemid)
            if item_in_template and item_in_template.user == current_user.user:
                pass

            elif item_in_template:
                #user's friend's item
                operation_name = 'friends' #switched to another template
                user_friend_in_template = item_in_template.usermodel
                template_values['ItemInTemplate'] = item_in_template
                template_values['UserFriendInTemplate'] = user_friend_in_template

        template_values['UserNickName'] = cgi.escape(current_user.dispname)
        template_values['UserID'] = current_user.key().id()
        template_values['htmltag_today'] = datetime.date.today() 
        path = os.path.join(os.path.dirname(__file__), 'pages/%s/ajax_sidebar_%s.html' % (template_name, operation_name))
        try:
            self.write(template.render(path, template_values))
        except:
            ''' Get a unknown func by malicious user.'''
            self.write("")



def main():
    application = webapp.WSGIApplication([
                                        (r'/ajax/allpage_edititem.+', edititem),
                                        (r'/ajax/render/.*', render),
                                        (r'/ajax/sidebar/.*', sidebar),
                                        ('/ajax/admin_runpatch/.+', admin_runpatch),
                                      ('/ajax/.+',ajax_error)],
                                       debug=True)


    run_wsgi_app(application)

if __name__ == "__main__":
      main()
