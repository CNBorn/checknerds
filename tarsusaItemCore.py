#-*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.1, codename California
# - tarsusaItemCore.py
# Author: CNBorn, 2008-2010
# http://cnborn.net, http://twitter.com/CNBorn
#
# **************************************************************** 

import os
import sys

import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db

import time
import datetime
import string
import re

import tarsusaCore
import memcache
import shardingcounter

from modules import *
from base import *
import logging

from utils import login
from django.utils import simplejson as json

class DueToday(tarsusaRequestHandler):
    @login
    def get(self):
        item_id = self.request.path[10:]
        tarsusaItem.get_item(item_id).set_duetoday()
        self.response.headers.add_header('Content-Type', "application/json")
        self.write(json.dumps({"r":"ok"}))

class DoneItem(tarsusaRequestHandler):
    @login
    def get(self):
        ItemId = self.request.path[10:]
        DoneYesterdaysDailyRoutine = False
        if ItemId[-2:] == '/y':
            ItemId = self.request.path[10:-2]           
            DoneYesterdaysDailyRoutine = True

        CurrentUser = self.get_user_db()
        Misc = 'y' if DoneYesterdaysDailyRoutine else ''
        
        item = tarsusaItem.get_item(ItemId) 
        item.done_item(CurrentUser, Misc)
        self.response.headers.add_header('Content-Type', "application/json")
        self.write(json.dumps({"r":"ok"}))

class UnDoneItem(tarsusaRequestHandler):
    def get(self):
        if self.chk_login():
            ItemId = self.request.path[12:]
            UndoneYesterdaysDailyRoutine = False
            if ItemId[-2:] == '/y':
                ItemId = self.request.path[12:-2]           
                UndoneYesterdaysDailyRoutine = True
            CurrentUser = self.get_user_db()
            Misc = ''
            if UndoneYesterdaysDailyRoutine:
                Misc = 'y'
            tarsusaCore.UndoneItem(int(ItemId), CurrentUser.key().id(), Misc)

        self.redirect(self.referer)

class RemoveItem(tarsusaRequestHandler):
    @login
    def get(self):
        item_id = self.request.path[12:]
        current_user = self.get_user_db()
        item = tarsusaItem.get_item(item_id)
        remove_status = item.delete_item(current_user.key().id())
        self.response.headers.add_header('Content-Type', "application/json")
        self.write(json.dumps({"r":remove_status}))

class AddItemProcess(tarsusaRequestHandler):
    @login
    def post(self):
        CurrentUser = self.get_user_db()
        item2beadd_name = cgi.escape(self.request.get('name'))
        item2beadd_comment = cgi.escape(self.request.get('comment'))
        #Error handler to be suit in the lite mobile add page.
        item_id = tarsusaCore.AddItem(CurrentUser.key().id(), item2beadd_name, item2beadd_comment, self.request.get('routine','none'), self.request.get('public', 'private'), self.request.get('inputDate'), self.request.get('tags'))

        #Added mobile redirect
        if self.referer[-6:] == "/m/add":
            self.redirect("/m/todo")

        #Return the newly add item's id
        self.response.headers.add_header('Content-Type', "application/json")
        self.write(json.dumps({"r":item_id}))


class EditItemProcess(tarsusaRequestHandler):
    def post(self): 

        tItemId = self.request.path[10:]
        ## Please be awared that tItemId here is a string!
        tItem = tarsusaItem.get_by_id(int(tItemId))

        #Check if comment property's length is exceed 500
        if len(self.request.get('comment'))>500:
            item_comment = self.request.get('comment')[:500]
        else:
            item_comment = self.request.get('comment')

        # Permission check is very important.
        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login:
            CurrentUser = self.get_user_db()
        else:
            self.redirect('/')

        
        if tItem.user == users.get_current_user():
            
            #Update Expectdate.
            if self.request.get('inputDate') == 'None':
                expectdatetime = None
            else:
                expectdate = datetime.date(*time.strptime(self.request.get('inputDate'),"%Y-%m-%d")[:3])
                currenttime = datetime.datetime.time(datetime.datetime.now())
                expectdatetime = datetime.datetime(expectdate.year, expectdate.month, expectdate.day, currenttime.hour, currenttime.minute, currenttime.second, currenttime.microsecond)
            tItem.expectdate =  expectdatetime

            tItem.name = cgi.escape(self.request.get('name'))
            tItem.comment = cgi.escape(item_comment)
            tItem.routine = cgi.escape(self.request.get('routine'))
            tItem.public = cgi.escape(self.request.get('public'))
            
            tItem.usermodel = CurrentUser
            tItem.put()

            #memcache related. Clear ajax_DailyroutineTodayCache after add a daily routine item
            if cgi.escape(self.request.get('routine')) == 'daily':          
                memcache.event('editroutineitem_daily', CurrentUser.key().id())
            else:
                memcache.event('editroutineitem', CurrentUser.key().id())
            
            if cgi.escape(self.request.get('public')) != 'none':
                memcache.event('editpublicitem', CurrentUser.key().id())
    
            ## Deal with Tags.          
            tarsusaItem_Tags = cgi.escape(self.request.get('tags')).split(",")

            # Hard to find a way to clear this list.
            tItem.tags = []
            tItem.put()
            
            for each_tag_in_tarsusaitem in tarsusaItem_Tags:
        
                ## TODO: I am a little bit worried when the global tags are exceed 1000 items. 
                catlist = db.GqlQuery("SELECT * FROM Tag WHERE name = :1 LIMIT 1", each_tag_in_tarsusaitem)
                try:
                    each_cat = catlist[0]               
                except:             
                    each_cat = Tag(name=each_tag_in_tarsusaitem)
                    each_cat.put()
                
                tItem.tags.append(each_cat.key())
                
                # To Check whether this user is using this tag before.
                tag_AlreadyUsed = False
                for check_whether_used_tag in CurrentUser.usedtags:
                    item_check_whether_used_tag = db.get(check_whether_used_tag)
                    if item_check_whether_used_tag != None:
                        if each_cat.key() == check_whether_used_tag or each_cat.name == item_check_whether_used_tag.name:
                            tag_AlreadyUsed = True
                    else:
                        if each_cat.key() == check_whether_used_tag:
                            tag_AlreadyUsed = True
                    
                if tag_AlreadyUsed == False:
                    CurrentUser.usedtags.append(each_cat.key())     

            tItem.put()
            CurrentUser.put()

            #Redirect specificly for mobile version.
            if re.search('/m/', self.referer):
                #self.write(self.referer)
                self.redirect("/i/" + str(tItem.key().id()))

        else:
            self.write('Sorry, Your session is out of time.')


def main():
    application = webapp.WSGIApplication([('/doneItem/\\d+',DoneItem),
                                       ('/undoneItem/\\d+',UnDoneItem),
                                       ('/duetoday/\\d+',DueToday),
                                       ('/removeItem/\\d+', RemoveItem),
                                       ('/additem',AddItemProcess),
                                       ('/edititem/\\d+', EditItemProcess), 
                                       ],
                                       debug=True)

    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
