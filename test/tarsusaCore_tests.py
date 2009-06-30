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
import modules

import logging
class tarsusaCoreTest(unittest.TestCase):

	def setUp(self):
    	# Populate test entities.
		entity = modules.tarsusaUser(name='Bar')
		self.setup_key = entity.put()

		NewtarsusaItem = modules.tarsusaItem(name="Item", done=False, routine="none")
		NewtarsusaItem.put()
		NewtarsusaItem2 = modules.tarsusaItem(name="Item", done=False, routine="none", usermodel=entity)
		NewtarsusaItem2.put()
		logging.info(NewtarsusaItem.key().id())
	def tearDown(self):
		# There is no need to delete test entities.
		pass

	def test_tarsusaCore_gettarsusaItemCollection(self):
		#entity = model.MyEntity(name='Foo')
		#self.assertEqual('Foo', entity.name)
		tarsusaItemCollection_UserTodoItems = tarsusaCore.get_tarsusaItemCollection(userid=1, done=False)
	
	def test_tarsusaCore_gettarsusaDailyRoutine(self):
		DailyRoutine = tarsusaCore.get_dailyroutine(userid=1)

	def test_tarsusaCore_getitemsdueToday(self):
		DueToday = tarsusaCore.get_ItemsDueToday(userid=1)

	def test_tarsusaCore_getuserdonelog(self):
		Donelog = tarsusaCore.get_UserDonelog(userid=1)
	
	def test_tarsusaCore_getuserNonPrivateItems(self):
		NonPrivateItems = tarsusaCore.get_UserNonPrivateItems(userid=1)
	
	def test_tarsusaCore_getUserFriendStats(self):
		UserFriendStats = tarsusaCore.get_UserFriendStats(userid=1)

	def test_tarsusaCore_countUserItemStats(self):
		UserItemStats = tarsusaCore.get_count_UserItemStats(userid=1)

	def test_tarsusaCore_doneItem(self):
		DoneItem = tarsusaCore.DoneItem(ItemId="3", UserId="1", Misc='')
