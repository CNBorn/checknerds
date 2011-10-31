import unittest

from models import tarsusaItem, tarsusaUser, Tag

class TagTest(unittest.TestCase):

    def setUp(self):
        self.key1 = Tag(name="inbox")
        self.key2 = Tag(name="work")
        self.key1.put()
        self.key2.put()

        self.user = tarsusaUser(urlname='Bar')
        self.user.put()
        self.item1 = tarsusaItem.get_item(tarsusaItem.AddItem(self.user.key().id(), "item1", '', 'none', 'private', '', rawTags="inbox"))
        self.item2 = tarsusaItem.get_item(tarsusaItem.AddItem(self.user.key().id(), "item2", '', 'none', 'private', '', rawTags="work"))

    def tearDown(self):
        self.item1.delete()
        self.item2.delete()
        self.user.delete()

        self.key1.delete()
        self.key2.delete()
   
    def test_get_tag_list(self):
        self.assertEqual(2, len(self.user.tag_list()))
        self.assertEqual(True, u'inbox' in self.user.tag_list())
        self.assertEqual(True, u'work' in self.user.tag_list())

    def test_get_tag_item_ids_list(self):
        self.assertEqual(1, len(self.user.tag_item_ids_list(self.key1.name)))
        self.assertEqual(True, self.item1.key().id() in self.user.tag_item_ids_list(self.key1.name))
        self.assertEqual(1, len(self.user.tag_item_ids_list(self.key2.name)))
        self.assertEqual(True, self.item2.key().id() in self.user.tag_item_ids_list(self.key2.name))

