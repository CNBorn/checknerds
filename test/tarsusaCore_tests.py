import unittest
import os
import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
import datetime,time
import string
import urllib
from google.appengine.ext.webapp import template
from google.appengine.api import images

from modules import *
import base
import tarsusaCore
import modules

import logging
class tarsusaCoreTest(unittest.TestCase):

    def setUp(self):

        # Populate test entities.
        entity = modules.tarsusaUser(urlname='Bar')
        self.setup_key = entity.put()

        NewtarsusaItem = modules.tarsusaItem(name="Item1", done=False, routine="none", usermodel=entity)
        NewtarsusaItem.put()
        NewtarsusaItem2 = modules.tarsusaItem(name="Item2", done=False, routine="none", usermodel=entity)
        NewtarsusaItem2.put()

   
    def test_tarsusaCore_gettarsusaItemCollection(self):
        #entity = model.MyEntity(name='Foo')
        tarsusaItemCollection_UserTodoItems = tarsusaCore.get_tarsusaItemCollection(userid=1, done=False)
        self.assertEqual(tarsusaItemCollection_UserTodoItems, "")
    
    def test_tarsusaCore_gettarsusaDailyRoutine(self):
        DailyRoutine = tarsusaCore.get_dailyroutine(userid=1)

    def test_tarsusaCore_getitemsdueToday(self):
        DueToday = tarsusaCore.get_ItemsDueToday(userid=1)

    def test_tarsusaCore_getuserdonelog(self):
        Donelog = tarsusaCore.get_UserDonelog(userid=1)
    
    def test_tarsusaCore_getuserNonPrivateItems(self):
        NonPrivateItems = tarsusaCore.get_UserNonPrivateItems(userid=1)

    def test_tarsusaCore_getUserFriends(self):
        UserFriendList = tarsusaCore.get_UserFriends(userid=1)

    def test_tarsusaCore_getUserFriendStats(self):
        UserFriendStats = tarsusaCore.get_UserFriendStats(userid=1)

    def test_tarsusaCore_countUserItemStats(self):
        UserItemStats = tarsusaCore.get_count_UserItemStats(userid=1)
        #print tarsusaCore.get_count_UserItemStats(userid=1)
        #print UserItemStats
        
        self.assertEqual(UserItemStats, {'UserTotalItems': 6, 'UserToDoItems': 6, 'UserDoneItems': 0, 'UserDonePercentage': 0})

    def test_tarsusaCore_doneItem(self):
        user1 = tarsusaUser(urlname="Bar")
        user1.put()
        self.assertEqual(user1.user, "")
        DoneItem = tarsusaCore.DoneItem(ItemId="20", UserId=1, Misc='')
        self.assertEqual(DoneItem, True)

    def test_tarsusaCore_AddItem(self):
        #AddItem = tarsusaCore.AddItem(UserId="1", rawName="Test Item Name", rawComment = "Test Item Comment", rawRoutine='', rawPublic="private", rawInputDate="2009-07-19", rawTags=None)
        #tarsusaCore.AddItem(1, "Test Item Name", "Test Item Comment", '', "private", "2009-07-19", None)
        #AddItem(UserId, rawName, rawComment='', rawRoutine='', rawPublic='private', rawInputDate='', rawTags=None):
        pass

    def test_tarsusaCore_get_latest_user(self):
        import tarsusaCore
        a = tarsusaCore.get_LatestUser(count=8)
        self.assertEqual(a, "*")

    def test_tarsusaCore_Removeitem(self):
        RemoveItem = tarsusaCore.RemoveItem(ItemId="2", UserId="1", Misc='')
