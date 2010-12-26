# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename Nevada->California
# - patcher.py
# Copyright (C) CNBorn, 2008
# http://cnborn.net/blog, http://twitter.com/CNBorn
#
# A Patcher for Updating existing Data Models.
#
# **************************************************************** 

import urllib
import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from modules import *
from base import *

import datetime

def chk_dbmodel_update(ThisUser):
	
	# Patch No.1 
	#      Added usermodel property in tarsusaItem since Rev.75
	#	
	# This update needs to browse all the tarsusaItem and add this field to them.
	# Besure that the total item is under 1000.
	#NewestItem =  db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC", ThisUser.user).get()
	#OldestItem =  db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date", ThisUser.user).get()
	#NewestItem = 

	#try:
	#Both NewestItem and OldestItem will be None when User do not have any items!
	
	#if NewestItem.usermodel == None or OldestItem.usermodel == None:
	tarsusaItemCollection = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1", ThisUser.user)	
	for each_tarsusaItem in tarsusaItemCollection:
		if each_tarsusaItem.usermodel == None:
			each_tarsusaItem.usermodel == ThisUser
			each_tarsusaItem.put()
	#else:
	#	pass
	
	#except:
	#	pass
	
	#####################################################


def patch_empty_dispname():
	if not self.chk_login():
		self.redirect('/')
	
	userid = urllib.unquote(cgi.escape(self.request.path[len('/patch/empty_dispname/'):]))
	##Get the username in the url of /patch/empty_dispname/1234
	
	PatchedUser = tarsusaUser.get_by_id(int(userid))
	if PatchedUser != None:
		PatchedUser.dispname = PatchedUser.user.nickname()
		if PatchedUser.user.nickname() == '':
			PatchedUser.dispname = str(PatchedUser.mail)
		PatchedUser.put()


def patch_notification_daily_and_friends(userid):
	# Patch No.2 
	#      Added serveral properties in tarsusaUser since Rev.136+
	#			 For the Usage of Notification feature.
	
	ThisUser = tarsusaUser.get_by_id(int(userid))	
	
	if ThisUser.notify_dailybriefing == None:
		ThisUser.notify_dailybriefing = True 
	
	if ThisUser.notify_dailybriefing_time == None:
		ThisUser.notify_dailybriefing_time = datetime.time(0)
	
	if ThisUser.notify_addedasfriend == None:
		ThisUser.notify_addedasfriend = True

	ThisUser.put()
