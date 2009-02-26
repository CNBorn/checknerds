# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename Nevada
# - ajax.py
# Author: CNBorn, 2008-2009
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn
#
# Ajax Pages & Functions Complex
#
# **************************************************************** 


#from django.conf import settings
#settings._target = None
import os
#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db

import datetime, time
import string
from google.appengine.ext.webapp import template
from google.appengine.api import images

from modules import *
from base import *
import logging


import urllib
import random
from django.utils import simplejson

import tarsusaCore
import memcache

class getdailyroutine(tarsusaRequestHandler):

	def post(self):
		if self.chk_login():
			CurrentUser = self.get_user_db()
		else:
			self.redirect('/')

		cachedUserDailyroutineToday = memcache.get_item("dailyroutine_today", CurrentUser.key().id())
		#if cachedUserDailyroutineToday is not None:
		if cachedUserDailyroutineToday == True:
			strcachedUserDailyroutineToday = cachedUserDailyroutineToday
		else:			
			# Show His Daily Routine.
			tarsusaItemCollection_DailyRoutine = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'daily' ORDER BY date DESC", users.get_current_user())
			tarsusaItemCollection_DoneDailyRoutine = tarsusaRoutineLogItem 

			# GAE datastore has a gqlquery.count limitation. So right here solve this manully.
			tarsusaItemCollection_DailyRoutine_count = 0
			for each_tarsusaItemCollection_DailyRoutine in tarsusaItemCollection_DailyRoutine:
				tarsusaItemCollection_DailyRoutine_count += 1

			Today_DoneRoutine = 0

			for each_tarsusaItemCollection_DailyRoutine in tarsusaItemCollection_DailyRoutine:
				
				#This query should effectively read out all dailyroutine done by today.
				#for the result will be traversed below, therefore it should be as short as possible.
				#MARK FOR FUTURE IMPROVMENT
				
				# GAE datastore has a gqlquery.count limitation. So right here solve this manully.
				#tarsusaItemCollection_DailyRoutine_count
				# Refer to code above.
				
				# LIMIT and OFFSET don't currently support bound parameters.
				# http://code.google.com/p/googleappengine/issues/detail?id=179
				# if this is realized, the code below next line will be used.

				tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC ", users.get_current_user(), each_tarsusaItemCollection_DailyRoutine.key().id())
				
				#tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC LIMIT :3", users.get_current_user(), each_tarsusaItemCollection_DailyRoutine.key().id(), int(tarsusaItemCollection_DailyRoutine_count))

				
				## traversed RoutineDaily
				
				## Check whether this single item is done.
				DoneThisItemToday = False
				
				for tarsusaItem_DoneDailyRoutine in tarsusaItemCollection_DoneDailyRoutine:
					if datetime.datetime.date(tarsusaItem_DoneDailyRoutine.donedate) == datetime.datetime.date(datetime.datetime.now()):
						#Check if the user had done all his routine today.
						Today_DoneRoutine += 1
						DoneThisItemToday = True

						# This routine have been done today.
						
						# Due to solve this part, I have to change tarsusaItemModel to db.Expando
						# I hope there is not so much harm for performance.
						each_tarsusaItemCollection_DailyRoutine.donetoday = 1
						each_tarsusaItemCollection_DailyRoutine.put()

					else:
						## The Date from RoutineLogItem isn't the same of Today's date
						pass
				
				if DoneThisItemToday == False:
					## Problem solved by Added this tag. DoneThisItemToday
					try:
						del each_tarsusaItemCollection_DailyRoutine.donetoday
						each_tarsusaItemCollection_DailyRoutine.put()
					except:
						pass

			
			## Output the message for DailyRoutine
			template_tag_donealldailyroutine = ''				
			if Today_DoneRoutine == int(tarsusaItemCollection_DailyRoutine_count) and Today_DoneRoutine != 0:
				template_tag_donealldailyroutine = '<img src="img/favb16.png">恭喜，你完成了今天要做的所有事情！'
			elif Today_DoneRoutine == int(tarsusaItemCollection_DailyRoutine_count) - 1:
				template_tag_donealldailyroutine = '只差一项，加油！'
			elif int(tarsusaItemCollection_DailyRoutine_count) == 0:
				template_tag_donealldailyroutine = '还没有添加每日计划？赶快添加吧！<br />只要在添加项目时，将“性质”设置为“每天要做的”就可以了！'


			template_values = {
			'UserLoggedIn': 'Logged In',				
			'UserNickName': cgi.escape(CurrentUser.dispname),
			'UserID': CurrentUser.key().id(),					
			'tarsusaItemCollection_DailyRoutine': tarsusaItemCollection_DailyRoutine,
			'htmltag_DoneAllDailyRoutine': template_tag_donealldailyroutine,
			'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
			}

			#Manupilating Templates 
			path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_dailyroutine.html')
			strcachedUserDailyroutineToday = template.render(path, template_values)
			if not memcache.set_item("dailyroutinetoday", strcachedUserDailyroutineToday, CurrentUser.key().id()):
				logging.error('Cache set failed: ajax_ShowUserDailyRoutineToday')

		self.write(strcachedUserDailyroutineToday)
		


class getdailyroutine_yesterday(tarsusaRequestHandler):
	def post(self):
		
		if self.chk_login():
			CurrentUser = self.get_user_db()
		else:
			self.redirect('/')

		cachedUserDailyroutineYesterday = memcache.get_item("dailyroutine_yesterday", CurrentUser.key().id())
		if cachedUserDailyroutineYesterday is not None:
			strcachedUserDailyroutineYesterday = cachedUserDailyroutineYesterday
		else:	
			# Show His Daily Routine.
			tarsusaItemCollection_DailyRoutine = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'daily' ORDER BY date DESC", users.get_current_user())
			tarsusaItemCollection_DoneDailyRoutine = tarsusaRoutineLogItem 

			# GAE datastore has a gqlquery.count limitation. So right here solve this manully.
			tarsusaItemCollection_DailyRoutine_count = 0
			for each_tarsusaItemCollection_DailyRoutine in tarsusaItemCollection_DailyRoutine:
				tarsusaItemCollection_DailyRoutine_count += 1

			Yesterday_DoneRoutine = 0

			for each_tarsusaItemCollection_DailyRoutine in tarsusaItemCollection_DailyRoutine:
				
				#This query should effectively read out all dailyroutine done by today.
				#for the result will be traversed below, therefore it should be as short as possible.
				#MARK FOR FUTURE IMPROVMENT
				
				# GAE datastore has a gqlquery.count limitation. So right here solve this manully.
				#tarsusaItemCollection_DailyRoutine_count
				# Refer to code above.
				
				# LIMIT and OFFSET don't currently support bound parameters.
				# http://code.google.com/p/googleappengine/issues/detail?id=179
				# if this is realized, the code below next line will be used.

				tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC ", users.get_current_user(), each_tarsusaItemCollection_DailyRoutine.key().id())
				
				## traversed RoutineDaily
				
				## Check whether this single item is done.
				DoneThisItemYesterday = False
				
				for tarsusaItem_DoneDailyRoutine in tarsusaItemCollection_DoneDailyRoutine:
					if datetime.datetime.date(tarsusaItem_DoneDailyRoutine.donedate) == datetime.datetime.date(datetime.datetime.now() - datetime.timedelta(days=1)):
						
						#Check if the user had done all his routine today.
						Yesterday_DoneRoutine += 1
						DoneThisItemYesterday = True

						# This routine have been done today.
						
						# Due to solve this part, I have to change tarsusaItemModel to db.Expando
						# I hope there is not so much harm for performance.
						each_tarsusaItemCollection_DailyRoutine.doneyesterday = 1
						each_tarsusaItemCollection_DailyRoutine.put()

					else:
						## The Date from RoutineLogItem isn't the same of Today's date
						## That means this tarsusaItem(as routine).donetoday should be removed.
							
						pass
				
				if DoneThisItemYesterday == False:
						## Problem solved by Added this tag. DoneThisItemYesterday
						try:
							del each_tarsusaItemCollection_DailyRoutine.doneyesterday
							each_tarsusaItemCollection_DailyRoutine.put()
						except:
							pass

			## Output the message for DailyRoutine
			template_tag_donealldailyroutine = ''
			
			if Yesterday_DoneRoutine == int(tarsusaItemCollection_DailyRoutine_count) and Yesterday_DoneRoutine != 0:
				template_tag_donealldailyroutine = '<img src="img/favb16.png">恭喜，你完成了昨天要做的所有事情！'
			elif Yesterday_DoneRoutine == int(tarsusaItemCollection_DailyRoutine_count) - 1:
				template_tag_donealldailyroutine = '只差一项，加油！'
			elif int(tarsusaItemCollection_DailyRoutine_count) == 0:
				template_tag_donealldailyroutine = '还没有添加每日计划？赶快添加吧！<br />只要在添加项目时，将“性质”设置为“每天要做的”就可以了！'

			template_values = {
			'UserLoggedIn': 'Logged In',
			'UserNickName': cgi.escape(CurrentUser.dispname),
			'UserID': CurrentUser.key().id(),
			'tarsusaItemCollection_DailyRoutine': tarsusaItemCollection_DailyRoutine,
			'htmltag_DoneAllDailyRoutine': template_tag_donealldailyroutine,
			'htmltag_today': datetime.datetime.date(datetime.datetime.now() - datetime.timedelta(days=1)), 
			}

			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_dailyroutine_yesterday.html')
			strcachedUserDailyroutineYesterday = template.render(path, template_values)
			memcache.set_item("dailyroutineyesterday", strcachedUserDailyroutineYesterday, CurrentUser.key().id())
		
		self.response.out.write(strcachedUserDailyroutineYesterday)



class get_fp_bottomcontents(tarsusaRequestHandler):
	##Constantly Encountering 405 Error:
	##Thanks for BenBen's solution: http://www.119797.com/program/gae-405/
	def head(self, *args):
		return self.get(*args)
		
	def get(self):
		if self.chk_login():
			CurrentUser = self.get_user_db()
		
		cachedUserItemlist = memcache.get_item("itemlist", CurrentUser.key().id())
		if cachedUserItemlist is not None:
			strcachedUserItemlist = cachedUserItemlist
		else:	
			tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC LIMIT 6", users.get_current_user())
			tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True ORDER BY donedate DESC LIMIT 6", users.get_current_user())									

			template_values = {
				'UserLoggedIn': 'Logged In',
				'UserNickName': cgi.escape(CurrentUser.dispname),
				'UserID': CurrentUser.key().id(),
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
				'tarsusaItemCollection_UserDoneItems': tarsusaItemCollection_UserDoneItems,
			}

			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_bottomcontents.html')
			strcachedUserItemlist = template.render(path, template_values)	
			memcache.set_item("itemlist", strcachedUserItemlist, CurrentUser.key().id())
			
		self.response.out.write(strcachedUserItemlist)


class get_fp_itemstats(tarsusaRequestHandler):
	def get(self):
		
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()

			cachedUserItemStats = memcache.get_item("itemstats", CurrentUser.key().id())
			if cachedUserItemStats is not None:
				strcachedUserItemStats = cachedUserItemStats
			else:
				# Count User's Todos and Dones
				tarsusaItemCollection_UserItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' ORDER BY date DESC", users.get_current_user())

				# For Count number, It is said that COUNT in GAE is not satisfied and accuracy.
				# SO there is implemented a stupid way.
				UserTotalItems = 0
				UserToDoItems = 0
				UserDoneItems = 0

				UserDonePercentage = 0.00

				for eachItem in tarsusaItemCollection_UserItems:
					UserTotalItems += 1
					if eachItem.done == True:
						UserDoneItems += 1
					else:
						UserToDoItems += 1
				
				if UserTotalItems != 0:
					UserDonePercentage = UserDoneItems *100 / UserTotalItems 
				else:
					UserDonePercentage = 0.00

				template_values = {
					'UserLoggedIn': 'Logged In',
					'UserTotalItems': UserTotalItems,
					'UserToDoItems': UserToDoItems,
					'UserDoneItems': UserDoneItems,
					'UserDonePercentage': UserDonePercentage,
				}

				#Manupilating Templates	
				path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_itemstats.html')
				
				strcachedUserItemStats = template.render(path, template_values)
				memcache.set_item("itemstats", strcachedUserItemStats, CurrentUser.key().id())
			
			self.response.out.write(strcachedUserItemStats)


class get_fp_friendstats(tarsusaRequestHandler):
	def get(self):

		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()
		#else:
			#self.redirect('/')		
			
			cachedUserFriendsActivities = memcache.get_item("friendstats", CurrentUser.key().id())
			if cachedUserFriendsActivities is not None:
				template_values = {
								'UserLoggedIn': 'Logged In',
								'UserFriendsActivities': cachedUserFriendsActivities,
				}
			else:
				
				## SHOW YOUR FRIENDs Recent Activities
				## Show only 9 items because we don't want to see a very long frontpage.
				UserFriendsItem_List = tarsusaCore.get_UserFriendStats(CurrentUser.key().id(),"","",9)
				#---
				UserFriendsActivities = ''
					
				if len(UserFriendsItem_List) > 0:
					#Output raw html
					for each_friend_item in UserFriendsItem_List:
						if each_friend_item['category'] == 'done':
							
							#Due to usermodel is applied in a later patch, some tarsusaItem may not have that property.
							#Otherwise I would like to user ['user'].key().id()
							UserFriendsActivities += '<li><a href="/user/' + str(each_friend_item['userid']) + '">' +  each_friend_item['userdispname'] + '</a> 完成了 <a href="/item/'.decode('utf-8') + str(each_friend_item['id']) + '">' + each_friend_item['name'] + '</a></li>'
						else:
							UserFriendsActivities += '<li><a href="/user/' + str(each_friend_item['userid']) + '">' +  each_friend_item['userdispname'] + '</a> 要做 <a href="/item/'.decode('utf-8') + str(each_friend_item['id']) + '">' + each_friend_item['name'] + '</a></li>'


					if len(UserFriendsItem_List) == 0:
						UserFriendsActivities = '<li>暂无友邻公开项目</li>'							
				
				else:
					#CurrentUser does not have any friends.
					UserFriendsActivities = '<li>当前没有添加朋友</li>'

				template_values = {
					'UserLoggedIn': 'Logged In',
					'UserFriendsActivities': UserFriendsActivities,
				}
				
				if not memcache.set_item("friendstats" ,UserFriendsActivities, CurrentUser.key().id()):
					logging.error('Cache set failed: Users_FriendStats')

			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_friendstats.html')
			self.response.out.write(template.render(path, template_values))


class additem(tarsusaRequestHandler):
	def get(self):

		urllen = len('/ajax/allpage_additem/')
		RequestCatName = urllib.unquote(self.request.path[urllen:])
		user = users.get_current_user()	
		
		if user:
			if RequestCatName != '':
				strAddItemCatName = str(RequestCatName)
			else:
				strAddItemCatName = ''

			strAddItemToday = str(datetime.datetime.date(datetime.datetime.now()))

		
			template_values = {
				'addItemCatName': strAddItemCatName.decode("utf-8"),
				'addItemToday': strAddItemToday.decode("utf-8"),
			}

			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_additem.html')
			self.response.out.write(template.render(path, template_values))
	
		else:
			self.write("您必须登录才可以添加条目，利用Google帐户登录，十分方便快捷，立即开始吧")


class edititem(tarsusaRequestHandler):
	def get(self):

		urllen = len('/ajax/allpage_edititem/')
		RequestItemId = urllib.unquote(self.request.path[urllen:])
		user = users.get_current_user()	
	
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()
		
		tItem = tarsusaItem.get_by_id(int(RequestItemId))
	
		if tItem.user == users.get_current_user():
			
			## Handle Tags
			# for modified Tags (db.key)
			tItemTags = ''
			try:
				for each_tag in db.get(tItem.tags):
					if tItemTags == '':
						tItemTags += cgi.escape(each_tag.name)
					else:
						tItemTags += ',' + cgi.escape(each_tag.name)
			except:
				# There is some chances that ThisItem do not have any tags.
				pass	
			
			try:
				tItemExpectdate = datetime.datetime.date(tItem.expectdate)
			except:
				tItemExpectdate = None
			
			try:

				template_values = {
					'tItemId': tItem.key().id(),
					'tItemName': cgi.escape(tItem.name),
					'tItemComment': cgi.escape(tItem.comment),
					'tItemTag': tItemTags,
					'tItemRoutine': tItem.routine,
					'tItemExpectdate': tItemExpectdate, 
					'tItemPublic': tItem.public,
					}			

				#Manupilating Templates	
				path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_edititem.html')
				self.response.out.write(template.render(path, template_values))

			except:
				## GAE Localhost Environment
				template_values = {
					'tItemId': tItem.key().id(),
					'tItemName': cgi.escape(tItem.name.encode('utf-8')),
					'tItemComment': cgi.escape(tItem.comment.encode('utf-8')),
					'tItemTag': tItemTags.encode('utf-8'),
					'tItemRoutine': tItem.routine,
					'tItemExpectdate': tItemExpectdate,
					'tItemPublic': tItem.public,
					}			

				#Manupilating Templates	
				path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_edititem.html')
				self.response.out.write(template.render(path, template_values))	

		else:
			self.write("您没有登录或没有权限编辑该项目")


class getjson_userdoneitems(tarsusaRequestHandler):
	### JSON Referrences: http://code.google.com/apis/opensocial/articles/appengine-0.8.html
	#					  http://www.ibm.com/developerworks/cn/opensource/os-eclipse-mashup-google-pt2/
	#					  http://www.cnblogs.com/leleroyn/archive/2008/06/17/1224039.html
	def get(self):
		if users.get_current_user() != None:

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()	

			CountTotalItems = 0
			tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True ORDER BY date DESC", users.get_current_user())
			UserDoneItems = []
    		for UserDoneItem in tarsusaItemCollection_UserDoneItems:
      			item = {'id' : str(UserDoneItem.key().id()), 'name' : UserDoneItem.name, 'date' : str(UserDoneItem.date), 'comment' : UserDoneItem.comment}
			UserDoneItems.append(item)
			
		self.response.out.write(simplejson.dumps(UserDoneItems))


class getjson_usertodoitems(tarsusaRequestHandler):
	
	def get(self):
		if users.get_current_user() != None:

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()	

			CountTotalItems = 0
			tarsusaItemCollection_UserTodoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC", users.get_current_user())
			UserTodoItems = []
    		for UserTodoItem in tarsusaItemCollection_UserTodoItems:
      			item = {'id' : str(UserTodoItem.key().id()), 'name' : UserTodoItem.name, 'date' : str(UserTodoItem.date), 'comment' : UserTodoItem.comment}
			UserTodoItems.append(item)
			
		self.response.out.write(simplejson.dumps(UserTodoItems))
			
class jsonpage(tarsusaRequestHandler):
	def get(self):
		if users.get_current_user() != None:

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()	

			CountTotalItems = 0
			
			## SPEED KILLER!
			## MULTIPLE DB QUERIES!
			## CAUTION! MODIFY THESE LATER!
			tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True ORDER BY date DESC", users.get_current_user())

			CountTotalItems = tarsusaItemCollection_UserDoneItems.count()
			strDoneStatus = "共有" + str(CountTotalItems) + "个已完成项目"

			template_values = {
				'PrefixCSSdir': "/",

				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(CurrentUser.dispname),
				'UserID': CurrentUser.key().id(),
				
				#'tarsusaItemCollection_DailyRoutine': tarsusaItemCollection_DailyRoutine,
				#'htmltag_DoneAllDailyRoutine': template_tag_donealldailyroutine,

				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
				'DoneStatus': memcache.notify_update('addfriend', self.get_user_db().key().id())
			}



			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_jsontest.html')
			self.response.out.write(template.render(path, template_values))
		else:
			self.redirect('/')

class ajax_error(tarsusaRequestHandler):
	def post(self):
		self.write("载入出错，请刷新重试")
	def get(self):
		self.write("载入出错，请刷新重试")

class get_fp_IntroductionBottomForAnonymous(tarsusaRequestHandler):
	
	def get(self):
		## Homepage for Non-Registered Users.
		## Since this page will be shown often to the anonymous visitors, and the information can be shown in not actully real-time.
		## Therefore Memcache implemented.
		## I can't figure out how to use get_multi so I just cache the whole ajaxpage output. 
		
		## Thinking of to have an implementation of such Global memcache items
		IsCachedAnonymousWelcomePage = memcache.get_item('strCachedAnonymousWelcomePage', 'global')
		
		if IsCachedAnonymousWelcomePage:
			
			strCachedAnonymousWelcomePage = IsCachedAnonymousWelcomePage

		else:

			## the not equal != is not supported!
			tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE public = 'public' and routine = 'none' and done = False ORDER BY date DESC LIMIT 9")

			tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE public = 'public' and routine = 'none' and done = True ORDER BY donedate DESC LIMIT 9")

			template_values = {
				'UserNickName': '访客',
				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
				'tarsusaItemCollection_UserDoneItems': tarsusaItemCollection_UserDoneItems,
 		     }
			
			#Manupilating Templates 
			path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_anonymousbottomcontents.html')	
			strCachedAnonymousWelcomePage = template.render(path, template_values)
			
			memcache.set_item("strCachedAnonymousWelcomePage", strCachedAnonymousWelcomePage, 'global')

		self.response.out.write(strCachedAnonymousWelcomePage)
		
class get_fp_RecentRegisteredUserForAnonymous(tarsusaRequestHandler):
	
	def get(self):
		IsCachedRecentRegisteredUsers = memcache.get_item('strCachedRecentRegisteredUsers', 'global')
		
		if IsCachedRecentRegisteredUsers:
			strCachedRecentRegisteredUsers = IsCachedRecentRegisteredUsers
		else:

			tarsusaUserCollection = db.GqlQuery("SELECT * FROM tarsusaUser ORDER BY datejoinin DESC LIMIT 9")
			strRecentUsers = ''
			if tarsusaUserCollection: 
				for each_RecentUser in tarsusaUserCollection:
					if each_RecentUser.avatar:
						strRecentUsers += '<span ' + 'style="line-height: 2em;"><a href="/user/' + cgi.escape(str(each_RecentUser.key().id())) +  '"><img src=/img?avatar=' + str(each_RecentUser.key().id()) + " width=32 height=32>"
					else:
						## Show Default Avatar
						strRecentUsers += '<span ' + 'style="line-height: 2em;"><a href="/user/' + cgi.escape(str(each_RecentUser.key().id())) +  '">' + "<img src='/img/default_avatar.jpg' width=32 height=32>"

					try:
						strRecentUsers += cgi.escape(each_RecentUser.dispname) + '</a></span>'
					except:
						strRecentUsers += cgi.escape(each_RecentUser.user.nickname()) + '</a></span>'

					#Complicatied TimeStamp needs to be done.
					#UserFriends += str(datetime.datetime.now() - each_Friend.datejoinin) 
					strRecentUsers += '<br />'


			template_values = {
				'UserNickName': '访客',
				'tarsusaUser_RecentRegistered': strRecentUsers,
 		     }
			
			#Manupilating Templates 
			path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_anonymousrecentregisteredusers.html')	
			strCachedRecentRegisteredUsers = template.render(path, template_values)
			
			memcache.set_item("strCachedRecentRegisteredUsers", strCachedRecentRegisteredUsers, 'global')

		self.response.out.write(strCachedRecentRegisteredUsers)

class admin_runpatch(tarsusaRequestHandler):
	def get(self):
		urllen = len('/ajax/admin_runpatch/')
		RequestUserID = urllib.unquote(self.request.path[urllen:])
		AppliedUser	= tarsusaUser.get_by_id(int(RequestUserID))
		self.write('dispname: ' +  AppliedUser.dispname)
		import DBPatcher
		#Run DB Model Patch	when User Logged in.
		DBPatcher.chk_dbmodel_update(AppliedUser)
		self.write('DONE with USERID' + RequestUserID)
		#self.redirect('/')

	


def main():
	application = webapp.WSGIApplication([('/ajax/frontpage_getdailyroutine', getdailyroutine),
										('/ajax/frontpage_getdailyroutine_yesterday', getdailyroutine_yesterday),
										('/ajax/frontpage_bottomcontents', get_fp_bottomcontents),
										('/ajax/frontpage_getfriendstats', get_fp_friendstats),
										('/ajax/frontpage_getitemstats', get_fp_itemstats),
										('/ajax/frontpage_introbottomcontentsforanonymous',get_fp_IntroductionBottomForAnonymous),
										('/ajax/frontpage_recentregistereduserforanonymous',get_fp_RecentRegisteredUserForAnonymous),
										(r'/ajax/allpage_additem.+', additem),
										(r'/ajax/allpage_edititem.+', edititem),
										('/ajax/getjson_usertodoitems', getjson_usertodoitems),
										('/ajax/getjson_userdoneitems', getjson_userdoneitems),
										('/ajax/admin_runpatch/.+', admin_runpatch),
										('/ajax/jsonpage', jsonpage),
									   ('/ajax/.+',ajax_error)],
                                       debug=True)


	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
