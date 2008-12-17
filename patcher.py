# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 0.7, codename Nevada
# - patcher.py
# Copyright (C) CNBorn, 2008
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn
#
# 
#
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


class patch_empty_dispname(tarsusaRequestHandler):
	def get(self):
				
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



class patch_error(tarsusaRequestHandler):
	def get(self):
		self.redirect('/')
		

def main():
	application = webapp.WSGIApplication([('/patch/empty_dispname/.+', patch_empty_dispname),
									   ('/patch/.+',patch_error)],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
