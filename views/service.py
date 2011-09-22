# -*- coding: utf-8 -*-
#
# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename California
# - service.py
# Copyright (C) CNBorn, 2008-2009
# http://cnborn.net, http://twitter.com/CNBorn
#
# Provides API call functions 
#
# **************************************************************** 
import urllib
import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from models import *
from base import * 

import time, datetime
import os

import tarsusaCore
import memcache

import logging

def api_auth_and_limit(function):
    '''
    to check with API Authentication & Limitation
        first py decorator i implemented, learnt from ihere blog.
    '''
    def api_auth_and_limit_wrapper(tRequestHandler, *args, **kw):
        if tRequestHandler.verify_api() == True and tRequestHandler.verify_api_limit() == True:
            return function(tRequestHandler, *args, **kw)
        elif tRequestHandler.verify_api() == False:
            return tRequestHandler.response_status(403,'API Authentication failed.',False)
        else:
            #thus tRequestHandler.verify_api_limit() == True
            return tRequestHandler.response_status(403, 'API Limitation exceed.', False)
    return api_auth_and_limit_wrapper
    
class api_getuser(tarsusaRequestHandler):
    
    #First CheckNerds API: Get User information.

    def get(self):
        self.write('<h1>please use POST</h1>')
    
    @api_auth_and_limit
    def post(self):
        #Should use log to monitor API usage.
        #Also there should be limitation for the apicalls/per hour.
        apiappid = self.request.get('apiappid') 
        apiservicekey = self.request.get('servicekey')
        apiuserid = self.request.get('apiuserid') 
        apikey = self.request.get('apikey')
        userid = self.request.get('userid')

        ThisUser = tarsusaUser.get_by_id(int(userid))
        user_info = {'id' : str(ThisUser.key().id()), 'name' : ThisUser.dispname, 'datejoinin' : str(ThisUser.datejoinin), 'website' : ThisUser.website, 'avatar' : 'http://www.checknerds.com/image?avatar=' + str(ThisUser.key().id())}
        
        self.write(user_info)

class api_getuserfriends(tarsusaRequestHandler):
    
    #CheckNerds API: Get User Friends information.

    def get(self):
        self.write('<h1>please use POST</h1>')
    
    @api_auth_and_limit
    def post(self):
        #Should use log to monitor API usage.
        #Also there should be limitation for the apicalls/per hour.
        apiappid = self.request.get('apiappid') 
        apiservicekey = self.request.get('servicekey')
        apiuserid = self.request.get('apiuserid') 
        apikey = self.request.get('apikey')
        userid = self.request.get('userid')

        ThisUser = tarsusaUser.get_by_id(int(userid))
        if ThisUser:
            ThisUsersFriendsLists = tarsusaCore.get_UserFriends(ThisUser.key().id())
            self.write(ThisUsersFriendsLists)
        else:
            return self.response_status(403,'No Such User',False)

#APIs to be added:
#   AddItem, DoneItem, UndoneItem, GetDailyRoutineItem, GteUserPublicItem, GetUserTodoItem, GetUserDoneItem, GetUserItem

class api_getuseritem(tarsusaRequestHandler):
    
    #CheckNerds API: Get User Items.
    #Parameters: apiuserid, apikey, userid, routine, public, maxitems

    def get(self):
        self.write('<h1>please use POST</h1>')

    @api_auth_and_limit
    def post(self):
        apiappid = self.request.get('apiappid') 
        apiservicekey = self.request.get('servicekey')
        apiuserid = self.request.get('apiuserid') 
        apikey = self.request.get('apikey')
        userid = self.request.get('userid')

        done = self.request.get('done')
        #logging.info(done == True)
        #logging.info(done == 'True')
        #Confirmed it is 'True' in text 
        if done == 'True':
            done = True
        elif done == 'False':
            done = False
        else:
            done = None
        logging.info(done)

        routine = self.request.get('routine')
        if routine == '':
            routine='none'
        
        #logging.info(routine)
        
        #!!!!!
        #Below Settings should be changed 
        #When user can check other users ITEMs!
        #
        public = self.request.get('public')
        if public == '':
            public = 'none'
            #'none' means it doesn't matter, display all items.
        #logging.info(public)
        
        maxitems = self.request.get('maxitems')
        if maxitems == None or maxitems == '':
            count = 10
        else:
            count = int(maxitems)
            if count > 100:
                count = 100
        
        beforedate = self.request.get('beforedate')
        afterdate = self.request.get('afterdate')
        if apiuserid == userid:
            tarsusaItemCollection_UserDoneItems = tarsusaItem.get_collection(userid, done=done, routine=routine, startdate=afterdate, enddate=beforedate, maxitems=count, public=public)
            self.write(tarsusaItemCollection_UserDoneItems) 
        else:
            return self.response_status(403, '<h1>Currently You can\'t get other user\'s items.</h1>', False)
        
class api_doneitem(tarsusaRequestHandler):
    
    #CheckNerds API: DoneItem.
    #Parameters: apiuserid, apikey, itemid

    def get(self):  
        self.write('<h1>please use POST</h1>')

    @api_auth_and_limit
    def post(self):
    
        #Actual function.
        itemid = self.request.get('itemid')
        apiappid = self.request.get('apiappid') 
        apiservicekey = self.request.get('servicekey')
        apiuserid = self.request.get('apiuserid') 
        apikey = self.request.get('apikey')
        userid = self.request.get('userid')

        APIUser = tarsusaUser.get_by_id(int(apiuserid))
        ThisItem = tarsusaItem.get_by_id(int(itemid))
        
        if ThisItem is None:
            return self.response_status(404,"No such Item.", False)

        if int(apiuserid) == ThisItem.usermodel.key().id():
            #Get APIUser's Items
            Misc = ''
            #Misc could be set to 'y' to done a yesterday's routineitem
            self.write(tarsusaCore.DoneItem(itemid, apiuserid, Misc))
            #Should be 200 status in future, currently just 0(success), 1(failed)

        else:
            #Trying to manipulate Other Users Items, very badass.
            return self.response_status(403, '<h1>You can\'t manipulate other user\'s items.</h1>', False)
    
class api_undoneitem(tarsusaRequestHandler):
    
    #CheckNerds API: UndoneItem.
    #Parameters: apiuserid, apikey, itemid

    def get(self):  
        self.write('<h1>please use POST</h1>')

    @api_auth_and_limit
    def post(self):

        #Actual function.
        itemid = self.request.get('itemid')
        apiappid = self.request.get('apiappid') 
        apiservicekey = self.request.get('servicekey')
        apiuserid = self.request.get('apiuserid') 
        apikey = self.request.get('apikey')
        userid = self.request.get('userid')
    
        APIUser = tarsusaUser.get_by_id(int(apiuserid))
        ThisItem = tarsusaItem.get_by_id(int(itemid))
        
        if ThisItem is None:
            return self.response_status(404, "No such Item.", False)

        if int(apiuserid) == ThisItem.usermodel.key().id():
            #Get APIUser's Items
            Misc = ''
            #Misc could be set to 'y' to done a yesterday's routineitem
            self.write(tarsusaCore.UndoneItem(itemid, apiuserid, Misc))
            #Should be 200 status in future, currently just 0(success), 1(failed)

        else:
            #Trying to manipulate Other Users Items, very badass.
            return self.response_status(403, '<h1>You can\'t manipulate other user\'s items.</h1>', False)

#To be added: api_checkAppModel

class api_additem(tarsusaRequestHandler):
    
    #CheckNerds API: AddItem.
    #Parameters: apiappid, apiservicekey, apiuserid, apikey
    #            item_name, item_comment, item_routine, item_public, item_date, item_tags 
    #Return:    Success: 200 status

    def get(self):  
        self.write('<h1>please use POST</h1>')

    @api_auth_and_limit
    def post(self):
        
        apiuserid = self.request.get('apiuserid') 
        apikey = self.request.get('apikey')
        
        #Actual function.
        apiappid = self.request.get('apiappid') 
        apiservicekey = self.request.get('servicekey')
        apiuserid = self.request.get('apiuserid') 
        apikey = self.request.get('apikey')
    
        APIUser = tarsusaUser.get_by_id(int(apiuserid))

        #To Add APIUser's a new Item
        item_name = self.request.get('name')
        item_comment = self.request.get('comment')
        item_routine = self.request.get('routine')
        item_public = self.request.get('public')
        item_date = self.request.get('date')
        item_tags = self.request.get('tags')

        newlyadd = tarsusaCore.AddItem(apiuserid, item_name, item_comment, item_routine, item_public, item_date, item_tags)
        
        #Should be 200 status in future, currently just 0(success), 1(failed)
        self.response.set_status(200)
        return newlyadd
        #return self.response_status(200, '<h1>You can\'t manipulate other user\'s items.</h1>', False)

def main():
    application = webapp.WSGIApplication([
                                       ('/service/user.+', api_getuser),
                                       ('/service/item.+', api_getuseritem),
                                       ('/service/done.+', api_doneitem),
                                       ('/service/undone.+', api_undoneitem),
                                       ('/service/additem.+', api_additem),
                                       ('/service/friends.+', api_getuserfriends)],
                                       debug=True)

    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
