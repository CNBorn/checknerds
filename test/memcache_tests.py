import unittest

from modules import tarsusaUser, tarsusaItem 
import modules
import memcache

class tarsusaMemcachedTest(unittest.TestCase):
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

    def test_memcache_set_item(self):
        current_id = self.user.key().id()
        self.assertEqual(True, memcache.set_item("testkey","testvalue",current_id,3600))
