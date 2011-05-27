import unittest
import sys
sys.path.append("../")

import datetime
from datetime import timedelta

from models import tarsusaItem, tarsusaUser
from tarsusaCore import AddItem
import modules
import memcache

class tarsusaItemTest(unittest.TestCase):

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
        query = [x.delete() for x in modules.tarsusaRoutineLogItem.all()]


    def test_item_set_duetoday(self):
        today = datetime.date.today()
        end_of_today = datetime.datetime(today.year, today.month, today.day, 23,59,59)
        self.item1.set_duetoday()
        self.assertEqual(end_of_today, self.item1.expectdate)

    def test_item_set_duetomorrow(self):
        tomorrow = datetime.date.today() + timedelta(days=1)
        end_of_tomorrow = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23,59,59)
        self.item1.set_duetomorrow()
        self.assertEqual(end_of_tomorrow, self.item1.expectdate)

    def test_items_duetoday(self):
        self.item1.set_duetoday()
        items_duetoday = self.user.get_items_duetoday()
        ids_items_duetoday = [x['id'] for x in items_duetoday]
        self.assertEqual(set([str(self.item1.key().id()), str(self.routine_item.key().id())]), set(ids_items_duetoday))
        self.assertEqual(True, self.item1.is_duetoday)

    def test_items_duetomorrow(self):
        self.item1.set_duetomorrow()
        self.assertEqual(True, self.item1.is_duetomorrow)

    def test_item_done_today(self):
        self.assertEqual(False, self.routine_item.has_done_today)
        self.routine_item.done_item(self.routine_item.usermodel)
        self.assertEqual(True, self.routine_item.has_done_today)

    def test_normal_item_undone(self):
        self.item1.done_item(self.user, "")
        self.item1.undone_item(self.user, "")
        self.assertEqual(self.item1.done, False)

    def test_daily_item_undone(self):
        self.routine_item.done_item(self.user, "")
        self.assertTrue(self.routine_item.has_done_today)
        self.routine_item.undone_item(self.user, "")
        self.assertFalse(self.routine_item.has_done_today)
    
    def test_last_daily_item_undone(self):
        self.routine_item.done_item(self.user, "y")
        self.assertTrue(self.routine_item.has_done_yesterday)
        self.routine_item.undone_item(self.user, "y")
        self.assertFalse(self.routine_item.has_done_yesterday)

