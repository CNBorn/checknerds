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

from models import *
import base
import memcache

import logging
class tarsusaCoreTest(unittest.TestCase):

    def setUp(self):
        self.user = tarsusaUser(urlname='Bar')
        self.user.put()
        self.item1 = tarsusaItem.get_item(tarsusaItem.AddItem(self.user.key().id(), "item1", '', 'none', 'private', ''))
        self.item2 = tarsusaItem.get_item(tarsusaItem.AddItem(self.user.key().id(), "item2", '', 'none', 'private', ''))
        self.routine_item = tarsusaItem.get_item(tarsusaItem.AddItem(self.user.key().id(), "routine_item", '', 'daily', 'private', ''))

    def tearDown(self):
        self.item1.delete()
        self.item2.delete()
        self.routine_item.delete()
        self.user.delete()
        memcache.flush_all()
        query = [x.delete() for x in tarsusaRoutineLogItem.all()]

    def test_get_dailyroutine(self):
        dailyroutine_items = self.user.get_dailyroutine()
        self.assertEqual(1, len(dailyroutine_items))
        self.assertEqual("routine_item", dailyroutine_items[0]['name'])
        self.assertFalse(dailyroutine_items[0]['done'])
        self.routine_item.done_item(user=self.user, misc="")
        dailyroutine_items = self.user.get_dailyroutine()
        self.assertTrue(dailyroutine_items[0]['done'])

    def test_tarsusaCore_gettarsusaItemCollection(self):
        todo_items = tarsusaItem.get_collection(userid=self.user.key().id(), done=False)
        self.assertEqual(len(todo_items), 2)
    
    def disabled_test_tarsusaCore_countUserItemStats(self):
        UserItemStats = tarsusaCore.get_count_UserItemStats(userid=self.user.key().id())
        self.assertEqual(UserItemStats, {'UserTotalItems': 2, 'UserToDoItems': 2, 'UserDoneItems': 0, 'UserDonePercentage': 0})

    def test_tarsusaCore_doneItem(self):
        self.item1.done_item(self.user, misc='')
        self.assertEqual(self.item1.done, True)

    def test_tarsusaCore_done_routine_item(self):
        routine_item = self.routine_item
        self.routine_item.done_item(self.user, misc="")
        self.assertEqual(False, routine_item.done)
        count_routine_log_item = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem").count()
        self.assertEqual(1, count_routine_log_item)
        routine_log_item = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem").get()
        self.assertEqual(datetime.datetime.now().date(), routine_log_item.donedate.date())
        routine_log_item.delete()

    def test_tarsusaCore_done_yesterday_routine_item(self):
        routine_item = self.routine_item
        self.routine_item.done_item(self.user, misc="y")
        self.assertEqual(False, routine_item.done)
        count_routine_log_item = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem").count()
        self.assertEqual(1, count_routine_log_item)
        routine_log_item = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem").get()
        self.assertEqual(datetime.datetime.now().date() - datetime.timedelta(days=1), routine_log_item.donedate.date())
        routine_log_item.delete()

    def test_tarsusaCore_delete_item(self):
        remove_status = self.item1.delete_item(user_id=self.user.key().id())
        self.assertEqual(True, remove_status)
        should_be_none = db.Query(tarsusaItem).filter("name =", "item1").get()
        self.assertEqual(None, should_be_none)

    def test_tarsusaCore_undone_item(self):
        undone_item = self.item1
        undone_item.done_item(self.user, misc='')
        undone_item.undone_item(self.user, misc='')
        self.assertEqual(False, undone_item.done)

    def test_tarsusaItem_AddItem(self):
        add_item_id = tarsusaItem.AddItem(user_id=self.user.key().id(), rawName="Test Item Name", rawComment = "Test Item Comment", rawRoutine='none', rawPublic="private", rawInputDate="2009-07-19", rawTags=None)
        add_item = tarsusaItem.get_item(add_item_id)
        self.assertEqual("Test Item Name", add_item.name)
        self.assertEqual(False, add_item.done)
        self.assertEqual("none", add_item.routine)
        self.assertEqual("private", add_item.public)
        add_item.delete_item(self.user.key().id())

        add_item_failed = tarsusaItem.AddItem(user_id=self.user.key().id(), rawName="xxx", rawComment="xxx", rawRoutine="should_broken", rawPublic="should_broken")
        self.assertEqual(None, add_item_failed)

    def test_tarsusaCore_getlatest_user(self):
        people_list = tarsusaUser.get_latestusers()
        self.assertEqual(1, people_list.count())

