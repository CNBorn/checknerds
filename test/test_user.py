import unittest
import sys
sys.path.append("../")

import datetime
from datetime import timedelta, date
import time

from models import tarsusaItem, tarsusaUser, tarsusaRoutineLogItem
from tarsusaCore import AddItem
import memcache

class tarsusaUserTest(unittest.TestCase):

    def setUp(self):
        self.user = tarsusaUser(urlname='Bar')
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
        query = [x.delete() for x in tarsusaRoutineLogItem.all()]


    def test_item_set_duetoday(self):
        today = datetime.date.today()
        end_of_today = datetime.datetime(today.year, today.month, today.day, 23,59,59)
        self.item1.set_duetoday()
        self.assertEqual(end_of_today, self.item1.expectdate)

    def test_get_done_items_list(self):
        doneitem_list = self.user.get_done_items()
        self.assertEqual(doneitem_list, [])
        self.item1.done_item(self.user)
        doneitem_list = self.user.get_done_items()
        self.assertEqual(doneitem_list[0]['name'], 'item1')

    def test_get_inbox_list_dont_have_today_item(self):
        self.item1.set_duetoday()
        inbox_list = self.user.get_inbox_items()
        self.assertFalse("item1" in [item['name'] for item in inbox_list])
        self.assertTrue("item2" in [item['name'] for item in inbox_list])

    def test_get_inbox_list(self):
        inbox_list = self.user.get_inbox_items()
        self.assertTrue("item1" in [item['name'] for item in inbox_list])
        self.assertTrue("item2" in [item['name'] for item in inbox_list])

    def test_get_more_inbox_item(self):
        more_inbox_list = self.user.get_more_inbox_items(1,self.item2.key().id())
        self.assertTrue("item1" in [item['name'] for item in more_inbox_list])
        self.assertFalse("item2" in [item['name'] for item in more_inbox_list])

    def test_get_done_item_list_is_json_format(self):
        self.item1.done_item(self.user)
        doneitem_list = self.user.get_done_items()
        self.assertEqual(doneitem_list[0]['donedate'], time.strftime("%Y-%m-%d", date.today().timetuple()))


    def test_get_more_undone_items(self):
        undone_item = self.user.get_more_undone_items(maxitems=100, before_item_id=self.item2.key().id())
        self.assertEqual(undone_item[0]['id'], self.item1.jsonized()['id'])

    def test_options(self):
        self.user.set_option("init_show_today", True)
        self.assertTrue(self.user.get_option("init_show_today"))
