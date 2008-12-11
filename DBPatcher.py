# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 0.7, codename Nevada
# - DBPatcher.py
# Copyright (C) CNBorn, 2008
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn
#
# 
#
#
# **************************************************************** 

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from modules import *
from base import *

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


