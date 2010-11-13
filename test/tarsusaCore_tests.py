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
        self.user = modules.tarsusaUser(urlname='Bar')
        self.user.put()
        self.item1 = modules.tarsusaItem(name="Item1", done=False, routine="none", usermodel=self.user)
        self.item1.put()
        self.item2 = modules.tarsusaItem(name="Item2", done=False, routine="none", usermodel=self.user)
        self.item2.put()

    def tearDown(self):
        self.item1.delete()
        self.item2.delete()
        self.user.delete()
   
    def test_tarsusaCore_gettarsusaItemCollection(self):
        todo_items = tarsusaCore.get_tarsusaItemCollection(userid=self.user.key().id(), done=False)
        self.assertEqual(len(todo_items), 2)
    
    def test_tarsusaCore_countUserItemStats(self):
        UserItemStats = tarsusaCore.get_count_UserItemStats(userid=self.user.key().id())
        self.assertEqual(UserItemStats, {'UserTotalItems': 2, 'UserToDoItems': 2, 'UserDoneItems': 0, 'UserDonePercentage': 0})

    def test_tarsusaCore_doneItem(self):
        DoneItem = tarsusaCore.DoneItem(ItemId=self.item1.key().id(), UserId=self.user.key().id(), Misc='')
        self.assertEqual(DoneItem, True)

    def test_tarsusaCore_undone_item(self):
        undone_item = self.item1
        tarsusaCore.DoneItem(ItemId=undone_item.key().id(), UserId=self.user.key().id(), Misc='')
        tarsusaCore.UndoneItem(ItemId=undone_item.key().id(), UserId=self.user.key().id(), Misc='')
        self.assertEqual(False, undone_item.done)

    def test_tarsusaCore_AddItem(self):
        #AddItem = tarsusaCore.AddItem(UserId="1", rawName="Test Item Name", rawComment = "Test Item Comment", rawRoutine='', rawPublic="private", rawInputDate="2009-07-19", rawTags=None)
        #tarsusaCore.AddItem(1, "Test Item Name", "Test Item Comment", '', "private", "2009-07-19", None)
        #AddItem(UserId, rawName, rawComment='', rawRoutine='', rawPublic='private', rawInputDate='', rawTags=None):
        pass

