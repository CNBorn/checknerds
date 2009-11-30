import unittest

from modules import tarsusaUser, tarsusaItem 
import modules
import memcache


class tarsusaCoreTest(unittest.TestCase):

    def setUp(self):
        # Populate test entities.
        entity = tarsusaUser(name='Bar')
        self.setup_key = entity.put()

        NewtarsusaItem = tarsusaItem(name="Item", done=False, routine="none", usermodel=entity)
        NewtarsusaItem.put()
        
        #logging.info("user:" + str(entity.key().id()))

    def tearDown(self):
        # There is no need to delete test entities.
        pass

    def test_memcache_set_item(self):
        #entity = model.MyEntity(name='Foo')
        #self.assertEqual('Foo', entity.name)
        CurrentUserID = self.setup_key.id() #setup_key is already a key
        self.assertEqual(True, memcache.set_item("testkey","testvalue",CurrentUserID,3600))
