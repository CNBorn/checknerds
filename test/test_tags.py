import unittest

from tarsusaCore import *
from modules import tarsusaItem, tarsusaUser
from tags import get_tag_list, get_tag_item_ids_list

class TagTest(unittest.TestCase):

    def setUp(self):
        self.key1 = Tag(name="inbox")
        self.key2 = Tag(name="work")
        self.key1.put()
        self.key2.put()

        self.user = tarsusaUser(urlname='Bar')
        self.user.put()
        self.item1 = tarsusaItem.get_item(AddItem(self.user.key().id(), "item1", '', 'none', 'private', '', rawTags="inbox"))
        self.item2 = tarsusaItem.get_item(AddItem(self.user.key().id(), "item2", '', 'none', 'private', '', rawTags="work"))

    def tearDown(self):
        self.item1.delete()
        self.item2.delete()
        self.user.delete()

        self.key1.delete()
        self.key2.delete()
   
    def test_get_tag_list(self):
        self.assertEqual(2, len(get_tag_list(self.user.key().id())))
        self.assertEqual(True, u'inbox' in get_tag_list(self.user.key().id()))
        self.assertEqual(True, u'work' in get_tag_list(self.user.key().id()))

    def test_get_tag_item_ids_list(self):
        self.assertEqual(1, len(get_tag_item_ids_list(self.key1.name, self.user.key().id())))
        self.assertEqual(True, self.item1.key().id() in get_tag_item_ids_list(self.key1.name, self.user.key().id()))
        self.assertEqual(1, len(get_tag_item_ids_list(self.key2.name, self.user.key().id())))
        self.assertEqual(True, self.item2.key().id() in get_tag_item_ids_list(self.key2.name, self.user.key().id()))

