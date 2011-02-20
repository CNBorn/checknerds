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
from tarsusaCore import AddItem, get_UserDonelog
import modules
import memcache

import logging
class tarsusaCoreTest(unittest.TestCase):

    def setUp(self):
        self.user = modules.tarsusaUser(urlname='Bar')
        self.user.put()
        self.item1 = tarsusaItem.get_item(AddItem(self.user.key().id(), "item1", '', 'none', 'private', ''))
        self.item2 = tarsusaItem.get_item(AddItem(self.user.key().id(), "item2", '', 'none', 'private', ''))
        self.routine_item = tarsusaItem.get_item(AddItem(self.user.key().id(), "routine_item", '', 'daily', 'private', ''))

    def tearDown(self):
        self.item1.delete()
        self.item2.delete()
        self.routine_item.delete()
        self.user.delete()
        memcache.flush_all()
        query = [x.delete() for x in modules.tarsusaRoutineLogItem.all()]

    def test_get_dailyroutine(self):
        dailyroutine_items = tarsusaCore.get_dailyroutine(self.user.key().id())
        self.assertEqual(1, len(dailyroutine_items))
        self.assertEqual("routine_item", dailyroutine_items[0]['name'])
        self.assertFalse(dailyroutine_items[0]['done'])
        tarsusaCore.DoneItem(ItemId=self.routine_item.key().id(), UserId=self.user.key().id(), Misc="")
        dailyroutine_items = tarsusaCore.get_dailyroutine(self.user.key().id())
        self.assertTrue(dailyroutine_items[0]['done'])

    def test_tarsusaCore_gettarsusaItemCollection(self):
        todo_items = tarsusaCore.get_tarsusaItemCollection(userid=self.user.key().id(), done=False)
        self.assertEqual(len(todo_items), 2)
    
    def disabled_test_tarsusaCore_countUserItemStats(self):
        UserItemStats = tarsusaCore.get_count_UserItemStats(userid=self.user.key().id())
        self.assertEqual(UserItemStats, {'UserTotalItems': 2, 'UserToDoItems': 2, 'UserDoneItems': 0, 'UserDonePercentage': 0})

    def test_tarsusaCore_doneItem(self):
        DoneItem = tarsusaCore.DoneItem(ItemId=self.item1.key().id(), UserId=self.user.key().id(), Misc='')
        self.assertEqual(DoneItem, True)

    def test_tarsusaCore_done_routine_item(self):
        routine_item = self.routine_item
        tarsusaCore.DoneItem(ItemId=self.routine_item.key().id(), UserId=self.user.key().id(), Misc="")
        self.assertEqual(False, routine_item.done)
        count_routine_log_item = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem").count()
        self.assertEqual(1, count_routine_log_item)
        routine_log_item = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem").get()
        self.assertEqual(datetime.datetime.now().date(), routine_log_item.donedate.date())
        routine_log_item.delete()

    def test_tarsusaCore_done_yesterday_routine_item(self):
        routine_item = self.routine_item
        tarsusaCore.DoneItem(ItemId=self.routine_item.key().id(), UserId=self.user.key().id(), Misc="y")
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
        tarsusaCore.DoneItem(ItemId=undone_item.key().id(), UserId=self.user.key().id(), Misc='')
        tarsusaCore.UndoneItem(ItemId=undone_item.key().id(), UserId=self.user.key().id(), Misc='')
        self.assertEqual(False, undone_item.done)

    def test_get_done_items_list(self):
        doneitem_list = tarsusaCore.get_done_items(self.user.key().id())
        self.assertEqual(doneitem_list, [])
        tarsusaCore.DoneItem(ItemId=self.item1.key().id(), UserId=self.user.key().id(), Misc='')
        doneitem_list = tarsusaCore.get_done_items(self.user.key().id())
        self.assertEqual(doneitem_list[0]['name'], 'item1')

    def test_tarsusaCore_AddItem(self):
        add_item_id = tarsusaCore.AddItem(UserId=self.user.key().id(), rawName="Test Item Name", rawComment = "Test Item Comment", rawRoutine='none', rawPublic="private", rawInputDate="2009-07-19", rawTags=None)
        add_item = tarsusaItem.get_item(add_item_id)
        self.assertEqual("Test Item Name", add_item.name)
        self.assertEqual(False, add_item.done)
        self.assertEqual("none", add_item.routine)
        self.assertEqual("private", add_item.public)
        add_item.delete_item(self.user.key().id())

        add_item_success = tarsusaCore.AddItem(UserId=self.user.key().id(), rawName="xxx", rawComment="xxx", rawRoutine="should_not_broken", rawPublic="should_not_broken")
        self.assertNotEqual(False, add_item_success)
        item = tarsusaItem.get_item(add_item_success)
        item.delete_item(self.user.key().id())

    def test_tarsusaCore_getuserdonelog(self):
        tarsusaCore.DoneItem(ItemId=self.routine_item.key().id(), UserId=self.user.key().id(), Misc="")
        DoneItem = tarsusaCore.DoneItem(ItemId=self.item1.key().id(), UserId=self.user.key().id(), Misc='')

        userdonelog = get_UserDonelog(userid=self.user.key().id())
        self.assertEqual(self.item1.name, userdonelog[0]["name"])
        self.assertEqual(self.routine_item.name, userdonelog[1]["name"])

    def test_tarsusaCore_getlatest_user(self):
        people_list = tarsusaUser.get_latestusers()
        self.assertEqual(1, people_list.count())

