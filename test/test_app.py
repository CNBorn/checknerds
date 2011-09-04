import unittest

from base import tarsusaRequestHandler as tHandler
from models import tarsusaItem, tarsusaUser, AppModel

class AppTest(unittest.TestCase):

    def setUp(self):
        self.user = tarsusaUser(urlname='Bar')
        self.user.put()
        self.app = AppModel(name="Foo", description="", usermodel=self.user, servicekey="abcdef", api_limit=400,enable=True)
        self.app.put()

        self.t = tHandler()
        self.t.request = {}
        self.t.request['apiappid'] = self.app.key().id()
        self.t.request['servicekey']= self.app.servicekey

    def tearDown(self):
        self.app.delete()
        self.user.delete()
   
    def test_verify_apilimit(self):
        self.assertEqual(True, self.t.verify_api_limit())
