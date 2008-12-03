# -*- coding: utf-8 -*-


# CheckNerds 
# - friends.py
# Cpoyright (C) CNBorn, 2008
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn


#from django.conf import settings
#settings._target = None
import os
import sys
#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db

import datetime
import string
from google.appengine.ext.webapp import template
from google.appengine.api import images

from modules import *
from base import *
import logging

import memcache
class FindFriendPage(tarsusaRequestHandler):
	def get(self):
	
		## Get Current User.
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()
		
		##if users.get_current_user() is None 
		if CurrentUser == None:
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

		else:


			tarsusaPeopleCollection = db.GqlQuery("SELECT * FROM tarsusaUser LIMIT 500")

			tarsusaUserFriendCollection = CurrentUser.friends

			UserFriends = ''
			if tarsusaUserFriendCollection: 
				for each_FriendKey in tarsusaUserFriendCollection:
					UsersFriend =  db.get(each_FriendKey)
					if UsersFriend.avatar:
						UserFriends += '<dl class="obu"><dt>' + '<a href="/user/' + cgi.escape(str(UsersFriend.key().id())) +  '"><img src=/img?img_user=' + str(UsersFriend.key()) + " width=32 height=32></dt>"

					else:
						## Show Default Avatar
						UserFriends += '<dl class="obu"><dt>' + '<a href="/user/' + cgi.escape(str(UsersFriend.key().id())) +  '">' + "<img src='/img/default_avatar.jpg' width=32 height=32>" + '</dt>'

					UserFriends += '<dd>' + cgi.escape(UsersFriend.user.nickname()) + '</a><br /><a href="#;" onclick="if (confirm(' + "'Are you sure to remove " + cgi.escape(UsersFriend.user.nickname()) + "')) {location.href = '/RemoveFriend/" + str(UsersFriend.key().id()) + "';}" + '" class="x">x</a></dd></dl>'



			else:
				UserFriends = '当前没有添加朋友'

			
			template_values = {
					'UserLoggedIn': 'Logged In',
					
					'UserNickName': cgi.escape(self.login_user.nickname()),
					'UserID': CurrentUser.key().id(),
					'UserFriends': UserFriends,	
					'singlePageTitle': "查找朋友.",
					'singlePageContent': "",

					'tarsusaPeopleCollection': tarsusaPeopleCollection,
			}

		
			path = os.path.join(os.path.dirname(__file__), 'pages/addfriend.html')
			self.response.out.write(template.render(path, template_values))


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

		## Get Current User.
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()

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
		
		self.redirect('/FindFriend')


def main():
	application = webapp.WSGIApplication([('/AddFriend/\\d+', AddFriendProcess),
									   ('/RemoveFriend/\\d+', RemoveFriendProcess),
									   ('/FindFriend', FindFriendPage)],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()

