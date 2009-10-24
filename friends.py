# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename Nevada
# - friends.py
# Copyright (C) CNBorn, 2008
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn
#
# **************************************************************** 

import os
import sys

import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db

import datetime,time
import random
import string
from google.appengine.ext.webapp import template
from google.appengine.api import images

from modules import *
from base import *
import logging

import memcache
import tarsusaCore

class FindFriendPage(tarsusaRequestHandler):
	def get(self):
	
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()

			## SHOW YOUR FRIENDs Recent Activities
			UserFriendsItem_List = tarsusaCore.get_UserFriendStats(CurrentUser.key().id())

			tarsusaLatestPeople = tarsusaCore.get_LatestUser()
			
			tarsusaUserFriendCollection = map(lambda each_FriendKey: db.get(each_FriendKey), CurrentUser.friends)
			
			template_values = {
					'UserLoggedIn': 'Logged In',
					
					'UserNickName': cgi.escape(CurrentUser.dispname),
					'UserID': CurrentUser.key().id(),
					'UserFriends': tarsusaUserFriendCollection,	
					'singlePageTitle': "查找朋友.",
					'singlePageContent': "",
					
					'UserFriendsActivities': UserFriendsItem_List,
					'tarsusaPeopleCollection': tarsusaLatestPeople,
			}
		
			path = os.path.join(os.path.dirname(__file__), 'pages/addfriend.html')
			self.response.out.write(template.render(path, template_values))

		else:
			##if users.get_current_user() is None 
			#TODO	
			template_values = {
					'UserLoggedIn': 'Logged In',
					
					'UserNickName': '', #cgi.escape(self.login_user.nickname()),
					'UserID': '', #CurrentUser.key().id(),
					'UserFriends': '', #UserFriends,	
					'singlePageTitle': "查找朋友.",
					'singlePageContent': "",

					'tarsusaPeopleCollection': '', #tarsusaPeopleCollection,
			}	
			path = os.path.join(os.path.dirname(__file__), 'pages/welcome_friends.html')
			self.response.out.write(template.render(path, template_values))
			
			## Prompt them to register!


class AddFriendProcess(tarsusaRequestHandler):
	def get(self):
		
		# Permission check is very important.

		ToBeAddedUserId = self.request.path[11:]
			## Please be awared that ItemId here is a string!
		ToBeAddedUser = tarsusaUser.get_by_id(int(ToBeAddedUserId))

		## Get Current User.
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login:
			CurrentUser = self.get_user_db()
		else:
			self.redirect('/')

		AlreadyAddedAsFriend = False
		for eachFriend in CurrentUser.friends:
			if eachFriend == ToBeAddedUser.key():
				AlreadyAddedAsFriend = True	


		if ToBeAddedUser.key() != CurrentUser.key() and AlreadyAddedAsFriend == False:
			CurrentUser.friends.append(ToBeAddedUser.key())
			CurrentUser.put()

		else:
			## You can't add your self! and You can add a person twice!
			pass
		
		memcache.event('addfriend', CurrentUser.key().id())
		self.redirect('/FindFriend')


class RemoveFriendProcess(tarsusaRequestHandler):
	def get(self):
		
		# Permission check is very important.

		ToBeRemovedUserId = self.request.path[14:]
			## Please be awared that ItemId here is a string!
		ToBeRemovedUser = tarsusaUser.get_by_id(int(ToBeRemovedUserId))

		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()


		AlreadyAddedAsFriend = False
		for eachFriend in CurrentUser.friends:
			if eachFriend == ToBeRemovedUser.key():
				AlreadyAddedAsFriend = True	


		if ToBeRemovedUser.key() != CurrentUser.key() and AlreadyAddedAsFriend == True:
			CurrentUser.friends.remove(ToBeRemovedUser.key())
			CurrentUser.put()

		else:
			## You can't remove your self! and You can not remove a person that are not your friend!
			pass
		
		memcache.event('removefriend', CurrentUser.key().id())
		self.redirect('/FindFriend')


def main():
	application = webapp.WSGIApplication([('/AddFriend/\\d+', AddFriendProcess),
									   ('/RemoveFriend/\\d+', RemoveFriendProcess),
									   ('/FindFriend', FindFriendPage)],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()

