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

			#---
			## SHOW YOUR FRIENDs Recent Activities
			UserFriendsItem_List = tarsusaCore.get_UserFriendStats(CurrentUser.key().id())
			#---
			UserFriendsActivities = '<ul class="mbt">'
				
			if len(UserFriendsItem_List) > 0:
				#Output raw html
				for each_friend_item in UserFriendsItem_List:
					if each_friend_item['category'] == 'done':
						
						#Due to usermodel is applied in a later patch, some tarsusaItem may not have that property.
						#Otherwise I would like to user ['user'].key().id()
						#UserFriendsActivities += '<li><a href="/user/' + str(each_friend_item['userid']) + '">' +  each_friend_item['userdispname'] + '<img src="' +each_friend_item['avatar'] + '" width=32 height=32>' + '</a> 完成了 <a href="/item/'.decode('utf-8') + str(each_friend_item['id']) + '">' + each_friend_item['name'] + '</a></li>'
						UserFriendsActivities += '<li class="mbtl"><a href="/user/' + str(each_friend_item['userid']) + '">' + '<img src="' + each_friend_item['avatar'] + '" width=48 height=48>' + '</a></li>'
						UserFriendsActivities += '<li class="mbtr"><span class="starb">' + '<a href="/user/' + str(each_friend_item['userid']) + '">' + each_friend_item['userdispname'] + '</a>' + '<span class="pl"> 完成了 <a href="/item/'.decode('utf-8') + str(each_friend_item['id']) + '">' + each_friend_item['name'] + '</a></span>' + 	'</span></li>'					

					else:
						#UserFriendsActivities += '<li><a href="/user/' + str(each_friend_item['userid']) + '">' +  each_friend_item['userdispname'] + '<img src="' +each_friend_item['avatar'] + '" width=32 height=32>' + '</a> 要做 <a href="/item/'.decode('utf-8') + str(each_friend_item['id']) + '">' + each_friend_item['name'] + '</a></li>'
						UserFriendsActivities += '<li class="mbtl"><a href="/user/' + str(each_friend_item['userid']) + '">' + '<img src="' + each_friend_item['avatar'] + '" width=48 height=48>' + '</a></li>'
						UserFriendsActivities += '<li class="mbtr"><span class="starb">' + '<a href="/user/' + str(each_friend_item['userid']) + '">' + each_friend_item['userdispname'] + '</a>' + '<span class="pl"> 要做 <a href="/item/'.decode('utf-8') + str(each_friend_item['id']) + '">' + each_friend_item['name'] + '</a></span>' + 	'</span></li>'					


				if len(UserFriendsItem_List) == 0:
					UserFriendsActivities = '<li>暂无友邻公开项目</li>'							
			
			else:
				#CurrentUser does not have any friends.
				UserFriendsActivities = '<li>当前没有添加朋友</li>'


			#---

			#Changed from Displaying all tarsusaUser (Very Slow performance)
			#	to display just random users.
			#tarsusaPeopleCollection = db.GqlQuery("SELECT * FROM tarsusaUser")
			LastestTime = int(time.mktime(datetime.datetime.now().timetuple()))
			BeginningTime = int(time.mktime(datetime.datetime(2008,10,22).timetuple()))

			ChoosenTime = datetime.datetime.fromtimestamp(random.randint(BeginningTime, LastestTime))
			#ChoosenTime = datetime.datetime(2008,9,15) # For Test in Localhost
			ChoosenTimeMax = ChoosenTime + datetime.timedelta(days=random.randint(1,15)) 
			#self.write(ChoosenTime)
			#self.write(ChoosenTimeMax)
			
			tarssuaLastestPeople = db.GqlQuery("SELECT * FROM tarsusaUser WHERE datejoinin > :1 and datejoinin < :2 ORDER by datejoinin DESC LIMIT 8", ChoosenTime, ChoosenTimeMax)

			tarsusaUserFriendCollection = CurrentUser.friends

			UserFriends = ''
			if tarsusaUserFriendCollection: 
				for each_FriendKey in tarsusaUserFriendCollection:
					UsersFriend =  db.get(each_FriendKey)
					if UsersFriend.avatar:
						UserFriends += '<dl class="obu"><dt>' + '<a href="/user/' + cgi.escape(str(UsersFriend.key().id())) +  '"><img src=/image?avatar=' + str(UsersFriend.key().id()) + " width=32 height=32></dt>"

					else:
						## Show Default Avatar
						UserFriends += '<dl class="obu"><dt>' + '<a href="/user/' + cgi.escape(str(UsersFriend.key().id())) +  '">' + "<img src='/img/default_avatar.jpg' width=32 height=32>" + '</dt>'

					UserFriends += '<dd>' + cgi.escape(UsersFriend.dispname) + '</a><br /><a href="#;" onclick="if (confirm(' + "'Are you sure to remove " + cgi.escape(UsersFriend.user.nickname()) + "')) {location.href = '/RemoveFriend/" + str(UsersFriend.key().id()) + "';}" + '" class="x">x</a></dd></dl>'

			else:
				UserFriends = '当前没有添加朋友'

			
			template_values = {
					'UserLoggedIn': 'Logged In',
					
					'UserNickName': cgi.escape(CurrentUser.dispname),
					'UserID': CurrentUser.key().id(),
					'UserFriends': UserFriends,	
					'singlePageTitle': "查找朋友.",
					'singlePageContent': "",
					
					'UserFriendsActivities': UserFriendsActivities,
					'tarsusaPeopleCollection': tarssuaLastestPeople,
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

