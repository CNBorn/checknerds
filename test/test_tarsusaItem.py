import unittest
import sys
sys.path.append("../")

import datetime

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
