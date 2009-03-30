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

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore_file_stub
from google.appengine.api import urlfetch_stub
from google.appengine.api import user_service_stub

class ModelTest(unittest.TestCase):
	def setUp(self):
		# Every test needs a client.
		#self.client = Client()        
		apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
		stub = datastore_file_stub.DatastoreFileStub(u'myTemporaryDataStorage', '/dev/null', '/dev/null')
		apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', stub)       

		apiproxy_stub_map.apiproxy.RegisterStub('user', user_service_stub.UserServiceStub())

		os.environ['AUTH_DOMAIN'] = 'gmail.com'
		os.environ['USER_EMAIL'] = 'CNBorn@gmail.com' # set to '' for no logged in user 
		os.environ['SERVER_NAME'] = 'testserver' 
		os.environ['SERVER_PORT'] = '8080' 
		os.environ['USER_IS_ADMIN'] = '0' 
		os.environ['APPLICATION_ID'] = 'nevada'
		self.user=users.get_current_user()
		
		#self.assertTrue(self.user is not None)        


	def test_tarsusaCore(self):
		tarsusaUsers = tarsusaUser.all()
		#q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", self.user)
		CurrentUser = q.get()

		#CurrentUser = tarsusaUser.get_by_id(42)
		#Item = tarsusaItem.get_by_id(42)
		#self.write(Item.name)


		#this_timestamp = datetime.datetime.fromtimestamp(int(pageid))
		this_timestamp = datetime.datetime.now()
						
		#if tag_ViewPreviousPage == True:
			#Limitation sharding startpoint differed since recent GAE updates.
			#problem arouses around r118.
		#tarsusaItemCollection_UserTodoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False and date > :2 ORDER BY date ASC LIMIT 9", CurrentUser.user, this_timestamp)
		tarsusaItemCollection_UserTodoItems = tarsusaCore.get_tarsusaItemCollection(CurrentUser.key().id(), done=False, startdate=this_timestamp)

		#else:
			#tarsusaItemCollection_UserTodoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False and date <= :2 ORDER BY date DESC LIMIT 9", CurrentUser.user, this_timestamp)
		tarsusaItemCollection_UserTodoItems = tarsusaCore.get_tarsusaItemCollection(userid=35, done=False, enddate=this_timestamp)

		## Below begins user todo items. for MOBILE page.
		#tarsusaItemCollection_UserTodoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC LIMIT 9", CurrentUser.user)
		# r120m test with new function in tarsusaCore.
		#tarsusaItemCollection_UserTodoItems = tarsusaCore.get_tarsusaItemCollection(35, False)


