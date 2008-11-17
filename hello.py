# -*- coding: utf-8 -*-

#from django.conf import settings
#settings._target = None
import os
#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import urllib
import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db

import time
import datetime
import string
from google.appengine.ext.webapp import template
from google.appengine.api import images
from google.appengine.api import memcache

from modules import *
from base import *
import logging


class MainPage(tarsusaRequestHandler):
	def get(self):
		
		#if self.chk_login() == True:
		if users.get_current_user() != None:

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()
			
			if not CurrentUser:
				# Create a User
				# Actully I thought this would be useless when I have an signin page.
				
				#Give vreated user a default avatar image.
				#avatar_image = images.resize('/img/default_avatar.jpg',64,64)
				#do not support read from file 
				#CurrentUser.avatar=db.Blob(avatar_image)
				#CurrentUser.put()  	


				CurrentUser = tarsusaUser(user=users.get_current_user(), urlname=users.get_current_user().nickname())
				#self.write(CurrentUser.user.nickname())


				## Should automatically give the user a proper urlname
				## otherwise a lot of user's name will be their email address.
				## the email address's urlname will cause seriouse problems when 
				## the people are entering their own Mainpage or UserSetting page.
				CurrentUser.put()

				## Added userid property.
				CurrentUser.userid = CurrentUser.key().id()
				CurrentUser.dispname = CurrentUser.user.nickname()
				CurrentUser.put()
			
			else:
				## These code for registered user whose information are not fitted into the new model setting.
				## Added them here.
				if CurrentUser.userid == None:
					CurrentUser.userid = CurrentUser.key().id()


			
			## Check usedtags as the evaluation for Tags Model
			## TEMP CODE!
			##UserTags = cgi.escape('<a href=/tag/>未分类项目</a>&nbsp;')
			UserTags = '<a href=/tag/>未分类项目</a>&nbsp;'.decode('utf-8')

			if CurrentUser.usedtags:
				CheckUsedTags = []
				for each_cate in CurrentUser.usedtags:
					## After adding code with avoiding add duplicated tag model, it runs error on live since there are some items are depending on the duplicated ones.
					
					try:
							
						## Caution! Massive CPU consumption.
						## Due to former BUG, there might be duplicated tags in usertags.
						## TO Solve this.

						DuplicatedTags = False
						for each_cate_vaild in CheckUsedTags:
							if each_cate.name == each_cate_vaild:
								DuplicatedTags = True

						CheckUsedTags.append(each_cate.name)

						if DuplicatedTags != True:
							try:
								## Since I have deleted some tags in CheckNerds manually, 
								## so there will be raise such kind of errors, in which the tag will not be found.
								each_tag =  db.get(each_cate)
								UserTags += '<a href="/tag/' + cgi.escape(each_tag.name) +  '">' + cgi.escape(each_tag.name) + '</a>&nbsp;'
							except:
								## Tag model can not be found.
								pass

					except:
						pass
						UserTags += 'Error, On MainPage Tags Section.'


			template_values = {
				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(self.login_user.nickname()),
				'UserID': CurrentUser.key().id(),
				
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 

				'UserTags': UserTags,


			}


			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'index.html')
			self.response.out.write(template.render(path, template_values))
			
		else:
		
			TotalUserCount = db.GqlQuery("SELECT * FROM tarsusaUser").count()
			TotaltarsusaItem = db.GqlQuery("SELECT * FROM tarsusaItem").count()

			## Homepage for Non-Registered Users.

			## the not equal != is not supported!
			tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE public = 'public' and routine = 'none' ORDER BY date DESC LIMIT 6")

			tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE public = 'public' and routine = 'none' and done = True ORDER BY date DESC LIMIT 6")
			
			template_values = {
				
				'UserNickName': "访客",
				'AnonymousVisitor': "Yes",
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
				'tarsusaItemCollection_UserDoneItems': tarsusaItemCollection_UserDoneItems,
				'htmltag_TotalUser': TotalUserCount,
				'htmltag_TotaltarsusaItem': TotaltarsusaItem,

			}


			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/welcome.html')
			self.response.out.write(template.render(path, template_values))

class AddItemProcess(tarsusaRequestHandler):
	def post(self):
		
		if self.request.get('cancel') != "取消":
		
			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()

			try:
				# The following code works on GAE platform.
			
				# it is weird that under GAE, it should be without .decode, but on localhost, it should add them!

				#first_tarsusa_item = tarsusaItem(user=users.get_current_user(),name=cgi.escape(self.request.get('name').decode('utf-8').encode('utf-8')), comment=cgi.escape(self.request.get('comment').decode('utf-8').encode('utf-8')),routine=cgi.escape(self.request.get('routine').decode('utf-8').encode('utf-8')))
				#first_tarsusa_item = tarsusaItem(user=users.get_current_user(),name=cgi.escape(self.request.get('name').decode('utf-8')), comment=cgi.escape(self.request.get('comment').decode('utf-8')),routine=cgi.escape(self.request.get('routine').decode('utf-8')))
				first_tarsusa_item = tarsusaItem(user=users.get_current_user(),name=cgi.escape(self.request.get('name')), comment=cgi.escape(self.request.get('comment')),routine=cgi.escape(self.request.get('routine')))
				
				# for changed tags from String to List:
				#first_tarsusa_item.tags = cgi.escape(self.request.get('tags')).split(",")

				#tarsusaItem_Tags = cgi.escape(self.request.get('tags').decode('utf-8')).split(",")
				tarsusaItem_Tags = cgi.escape(self.request.get('tags')).split(",")
				
				#first_tarsusa_item.public = self.request.get('public').decode('utf-8')
				first_tarsusa_item.public = self.request.get('public')

				first_tarsusa_item.done = False
		
		
				# DATETIME CONVERTION TRICKS from http://hi.baidu.com/huazai_net/blog/item/8acb142a13bf879f023bf613.html
				# The easiest way to convert this to a datetime seems to be;
				#datetime.date(*time.strptime("8/8/2008", "%d/%m/%Y")[:3])
				# the '*' operator unpacks the tuple, producing the argument list.	
				# also learned sth from: http://bytes.com/forum/thread603681.html

				# Logic: If the expectdate is the same day as today, It is none.
				expectdatetime = None
				expectdate = datetime.date(*time.strptime(self.request.get('inputDate'),"%Y-%m-%d")[:3])
				if expectdate == datetime.datetime.date(datetime.datetime.today()):
					expectdatetime == None
				else:
					currenttime = datetime.datetime.time(datetime.datetime.now())
					expectdatetime = datetime.datetime(expectdate.year, expectdate.month, expectdate.day, currenttime.hour, currenttime.minute, currenttime.second, currenttime.microsecond)
				first_tarsusa_item.expectdate =  expectdatetime


				## the creation date will be added automatically by GAE datastore
				first_tarsusa_item.put()
				
				# http://blog.ericsk.org/archives/1009
				# This part of tag process inspired by ericsk.
				# many to many

			except:
				## the following code works on the localhost GAE runtimes.
				try:
					first_tarsusa_item = tarsusaItem(user=users.get_current_user(),name=cgi.escape(self.request.get('name').decode('utf-8')), comment=cgi.escape(self.request.get('comment').decode('utf-8')),routine=cgi.escape(self.request.get('routine').decode('utf-8')))
					tarsusaItem_Tags = cgi.escape(self.request.get('tags').decode('utf-8')).split(",")
					first_tarsusa_item.public = self.request.get('public').decode('utf-8')
									
					expectdatetime = None
					expectdate = datetime.date(*time.strptime(self.request.get('inputDate').decode('utf-8'),"%Y-%m-%d")[:3])
					if expectdate == datetime.datetime.date(datetime.datetime.today()):
						expectdatetime == None
					else:
						currenttime = datetime.datetime.time(datetime.datetime.now())
						expectdatetime = datetime.datetime(expectdate.year, expectdate.month, expectdate.day, currenttime.hour, currenttime.minute, currenttime.second, currenttime.microsecond)
					first_tarsusa_item.expectdate =  expectdatetime
					
					first_tarsusa_item.done = False
					first_tarsusa_item.put()

				except:
					## SOMETHING WRONG
						self.write('something is wrong.') 

			
			#memcache related. Clear ajax_DailyroutineTodayCache after add a daily routine item
			if cgi.escape(self.request.get('routine')) == 'daily':
				cachedUserDailyroutineToday = memcache.get("%s_dailyroutinetoday" % (str(CurrentUser.key().id())))
				if cachedUserDailyroutineToday:
					if not memcache.delete("%s_dailyroutinetoday" % (str(CurrentUser.key().id()))):
						logging.error('Memcache delete failed: Adding Daily RoutineItem')
			else:
				pass


		
			for each_tag_in_tarsusaitem in tarsusaItem_Tags:
				
				#each_cat = Tag(name=each_tag_in_tarsusaitem)
				#each_cat.count += 1
				#each_cat.put()
				
				## It seems that these code above will create duplicated tag model.
				## TODO: I am a little bit worried when the global tags are exceed 1000 items. 
				catlist = db.GqlQuery("SELECT * FROM Tag WHERE name = :1 LIMIT 1", each_tag_in_tarsusaitem)
				try:
					each_cat = catlist[0]
				
				except:				
					try:
						#added this line for Localhost GAE runtime...
						each_cat = Tag(name=each_tag_in_tarsusaitem.decode('utf-8'))			
						each_cat.put()
					except:
						each_cat = Tag(name=each_tag_in_tarsusaitem)
						each_cat.put()

				first_tarsusa_item.tags.append(each_cat.key())
				# To Check whether this user is using this tag before.
				tag_AlreadyUsed = False
				for check_whether_used_tag in CurrentUser.usedtags:
					item_check_whether_used_tag = db.get(check_whether_used_tag)
					if item_check_whether_used_tag != None:
						if each_cat.key() == check_whether_used_tag or each_cat.name == item_check_whether_used_tag.name:
							tag_AlreadyUsed = True
					else:
						if each_cat.key() == check_whether_used_tag:
							tag_AlreadyUsed = True
					
				if tag_AlreadyUsed == False:
					CurrentUser.usedtags.append(each_cat.key())		

			first_tarsusa_item.put()
			CurrentUser.put()

class EditItemProcess(tarsusaRequestHandler):
	def post(self):
		
		# Permission check is very important.

		tItemId = self.request.path[10:]
		## Please be awared that tItemId here is a string!
		tItem = tarsusaItem.get_by_id(int(tItemId))

		## Get Current User.
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()

		
		if tItem.user == users.get_current_user():
			
			#Update Expectdate.
			if self.request.get('inputDate') == 'None':
				expectdatetime = None
			else:
				expectdate = datetime.date(*time.strptime(self.request.get('inputDate'),"%Y-%m-%d")[:3])
				currenttime = datetime.datetime.time(datetime.datetime.now())
				expectdatetime = datetime.datetime(expectdate.year, expectdate.month, expectdate.day, currenttime.hour, currenttime.minute, currenttime.second, currenttime.microsecond)
			tItem.expectdate =  expectdatetime

			tItem.name = cgi.escape(self.request.get('name'))
			tItem.comment = cgi.escape(self.request.get('comment'))
			tItem.routine = cgi.escape(self.request.get('routine'))
			tItem.public = cgi.escape(self.request.get('public'))
			
			tItem.put()

			#memcache related. Clear ajax_DailyroutineTodayCache after add a daily routine item
			if cgi.escape(self.request.get('routine')) == 'daily':
				cachedUserDailyroutineToday = memcache.get("%s_dailyroutinetoday" % (str(CurrentUser.key().id())))
				if cachedUserDailyroutineToday:
					if not memcache.delete("%s_dailyroutinetoday" % (str(CurrentUser.key().id()))):
						logging.error('Memcache delete failed: Edit an item into daily RoutineItem')
			else:
				pass

	
			## Deal with Tags.			
			tarsusaItem_Tags = cgi.escape(self.request.get('tags')).split(",")

			# Hard to find a way to clear this list.
			tItem.tags = []
			tItem.put()
			
			for each_tag_in_tarsusaitem in tarsusaItem_Tags:
		
				## TODO: I am a little bit worried when the global tags are exceed 1000 items. 
				catlist = db.GqlQuery("SELECT * FROM Tag WHERE name = :1 LIMIT 1", each_tag_in_tarsusaitem)
				try:
					each_cat = catlist[0]				
				except:				
					each_cat = Tag(name=each_tag_in_tarsusaitem)
					each_cat.put()
				
				tItem.tags.append(each_cat.key())
				
				# To Check whether this user is using this tag before.
				tag_AlreadyUsed = False
				for check_whether_used_tag in CurrentUser.usedtags:
					item_check_whether_used_tag = db.get(check_whether_used_tag)
					if item_check_whether_used_tag != None:
						if each_cat.key() == check_whether_used_tag or each_cat.name == item_check_whether_used_tag.name:
							tag_AlreadyUsed = True
					else:
						if each_cat.key() == check_whether_used_tag:
							tag_AlreadyUsed = True
					
				if tag_AlreadyUsed == False:
					CurrentUser.usedtags.append(each_cat.key())		

			tItem.put()
			CurrentUser.put()

		else:
			self.write('Sorry, Your session is out of time.')


class ViewItem(tarsusaRequestHandler):
	def get(self):
		#self.current_page = "home"
		postid = self.request.path[3:]
		tItem = tarsusaItem.get_by_id(int(postid))

		if tItem != None:  ## If this Item existed in Database.

			## Unregistered Guest may ViewItem too,
			## Check Their nickname here.
			if users.get_current_user() == None:
				UserNickName = "访客"
				AnonymousVisitor = True 
			else:
				UserNickName = users.get_current_user().nickname()


			# Check if this item is expired.
			if tItem.expectdate != None:
				if datetime.datetime.now() > tItem.expectdate:
					tItem.expired = 1
					tItem.put()
				else:
					pass

			elif tItem.expectdate != tItem.expectdate:
				if tItem.expired:
					del tItem.expired
					tItem.put()
			else:
				pass

			

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()


			logictag_OtherpeopleViewThisItem = None
			CurrentUserIsOneofAuthorsFriends = False
			if tItem.user != users.get_current_user():
			
				## Check if the viewing user is a friend of the ItemAuthor.
			
				# code below are comming from GAE example
				q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", tItem.user)
				ItemAuthorUser = q.get()

				CurrentUserIsOneofAuthorsFriends = False

				try:
					## may get anonymous user here.
					for each_Friend_key in ItemAuthorUser.friends:
						if each_Friend_key == CurrentUser.key():
							CurrentUserIsOneofAuthorsFriends = True
				except:
					CurrentUserIsOneofAuthorsFriends = False

				if tItem.public == 'publicOnlyforFriends':
					logictag_OtherpeopleViewThisItem = True

				elif tItem.public == 'public':
					logictag_OtherpeopleViewThisItem = True
					
				else:
					self.redirect('/')
			else:
				## Viewing User is the Owner of this Item.
				UserNickName = users.get_current_user().nickname()
				logictag_OtherpeopleViewThisItem = False


			# for modified Tags (db.key)
			ItemTags = ''
			
			try:
				if logictag_OtherpeopleViewThisItem == True:
					for each_tag in db.get(tItem.tags):
						ItemTags += cgi.escape(each_tag.name) + '&nbsp;'
				else:
					for each_tag in db.get(tItem.tags):
						ItemTags += '<a href=/tag/' + cgi.escape(each_tag.name) +  '>' + cgi.escape(each_tag.name) + '</a>&nbsp;'
			except:
				# There is some chances that ThisItem do not have any tags.
				pass



			# process html_tag_tarsusaRoutineItem
			if tItem.routine != 'none':
				html_tag_tarsusaRoutineItem = 'True'

				## If this routine Item's public == public or showntoFriends,
				## All these done routine log will be shown!
	
				tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routineid = :2 ORDER BY donedate DESC LIMIT 10", users.get_current_user(), tItem.key().id())
			else:
				tarsusaItemCollection_DoneDailyRoutine = None
				html_tag_tarsusaRoutineItem = None


			## Since Rev.7x Since GqlQuery can not filter, this function is disabled.	
			
			#Show Undone items in the same category, just like in tarsusa r6
			#Since Nevada allows mutiple tags, It finds item that with any one tags of this showing items.

			#/code# tarsusaItemCollection_SameCategoryUndone = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and done = False and id != :2 ORDER BY id DESC LIMIT 5", users.get_current_user(), tItem.key().id())

			# filter current viewing Item from the related items!
			# GqlQuery doesn't have the filter function!
			#tarsusaItemCollection_SameCategoryUndone.filter("id=", tItem.id)

			#/code# for eachItem in tarsusaItemCollection_SameCategoryUndone:
				#THIS IS A LOT CPU CONSUMPTIONS
				#/code# tfor eachTag in eachItem.tags:
					#/code# ttry:
						#/code# tIsSameCategory = False
						#/code# tfor each_tag in db.get(tItem.tags):
							#Find any tags are the same:
							#/code# tif db.get(eachTag).name == each_tag.name:							
								#/code# tIsSameCategory = True
						#/code# tif IsSameCategory == True:
							
							# GqlQuery doesn't have the filter function! and the filter function also doesn't support !=
							# TODO SO THERE IS BUG HERE! HERE! HERE!
							#tarsusaItemCollection_SameCategoryUndone.filter("id=", eachItem.id)					
							
							#/code# thtml_tag_SameCategory_ItemList += '<a href=/i/' + str(eachItem.key().id()) + '>' + cgi.escape(eachItem.name) + "</a><br/>"
							#	CountUndoneItems += 1
							
					#/code# texcept:
						#/code# tpass


			# -----
			#Show the items that are created in the same day, just like in tarsusa r6.

			TheDay = tItem.date
				
			one_day = datetime.timedelta(days=1)
			yesterday_ofTheDay = TheDay - one_day
			nextday_ofTheDay = TheDay + one_day

			#if the viewedUser is not the currentuser, first have to determine whether he is or is not a friend of currentuser.
			# and then display the sameday items of that user.
			outputStringRoutineLog = ""

			if logictag_OtherpeopleViewThisItem == True and CurrentUserIsOneofAuthorsFriends == True:
				## Display public items and friendvisible items.
				## BUG HERE! Because of the stupid GAE != issue, friends can only see friendpublic items. :(
				tarsusaItemCollection_SameDayCreated = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND date > :2 AND date <:3 ORDER BY date DESC LIMIT 20", tItem.user, yesterday_ofTheDay, nextday_ofTheDay)
				
				## Code from UserMainPage class.
				for each_Item in tarsusaItemCollection_SameDayCreated:
				## Added Item public permission check.
		
					if each_Item.public == 'publicOnlyforFriends':
						if each_Item.done == True:
							outputStringRoutineLog += "<img src='/img/accept16.png'>" 
						outputStringRoutineLog += '<a href="/i/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
					elif each_Item.public == 'public':
						if each_Item.done == True:
							outputStringRoutineLog += "<img src='/img/accept16.png'>" 
						outputStringRoutineLog += '<a href="/i/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
					else:
						pass


			elif logictag_OtherpeopleViewThisItem == True and CurrentUserIsOneofAuthorsFriends == False:
				## Display on public items.
				tarsusaItemCollection_SameDayCreated = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND date > :2 AND date <:3 AND public = 'public' ORDER BY date DESC LIMIT 10", tItem.user, yesterday_ofTheDay, nextday_ofTheDay)

			elif logictag_OtherpeopleViewThisItem == False:
				## if the viewedUser is the currentuser, just display the sameday items of currentuser.
							
				# SOME how bug is here, there is no way to determine the same date within the gql query.
				tarsusaItemCollection_SameDayCreated = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND date > :2 AND date <:3 ORDER BY date DESC LIMIT 10", users.get_current_user(), yesterday_ofTheDay, nextday_ofTheDay)
				# filter current viewing Item from the related items!			


			if UserNickName != "访客":
				UserNickName = users.get_current_user().nickname()
				## or dispname?

				template_values = {
						'PrefixCSSdir': "../",
						'UserLoggedIn': 'Logged In',

						'UserID': CurrentUser.key().id(),
						'UserNickName': UserNickName, 
						'ItemBelongsToUser': tItem.user,
						'singlePageTitle': "项目详细信息",
						'singlePageContent': "",

						'logictag_OtherpeopleViewThisItem': logictag_OtherpeopleViewThisItem,
						'logictag_CurrentUserIsOneofAuthorsFriends': CurrentUserIsOneofAuthorsFriends,

						'tarsusaItem': tItem,
						'tarsusaItemDone': tItem.done,
						'tarsusaItemTags': ItemTags,
						'tarsusaRoutineItem': html_tag_tarsusaRoutineItem,
						'tarsusaRoutineLogItem': tarsusaItemCollection_DoneDailyRoutine,

						#'tarsusaItemCollection_SameCategoryUndone': tarsusaItemCollection_SameCategoryUndone,

						'TheDayCreated': TheDay,
						'tarsusaItemCollection_SameDayCreated': tarsusaItemCollection_SameDayCreated,
						'htmlstring_outputStringRoutineLog': outputStringRoutineLog,
				}

			else:
						template_values = {
						'PrefixCSSdir': "../",
						'singlePageTitle': "项目详细信息",
						'singlePageContent': "",

						'logictag_OtherpeopleViewThisItem': logictag_OtherpeopleViewThisItem,

						'tarsusaItem': tItem,
						'tarsusaItemDone': tItem.done,
						'tarsusaItemTags': ItemTags,
						'tarsusaRoutineItem': html_tag_tarsusaRoutineItem,
						'tarsusaRoutineLogItem': tarsusaItemCollection_DoneDailyRoutine,
				}


		
			path = os.path.join(os.path.dirname(__file__), 'pages/viewitem.html')
			self.response.out.write(template.render(path, template_values))


		else:
			## Can't find this Item by this id.
			self.redirect('/')


class DoneItem(tarsusaRequestHandler):
	def get(self):
		ItemId = self.request.path[10:]
		DoneYesterdaysDailyRoutine = False
		if ItemId[-2:] == '/y':
			ItemId = self.request.path[10:-2]			
			DoneYesterdaysDailyRoutine = True

		tItem = tarsusaItem.get_by_id(int(ItemId))
		
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()
		
		if tItem.user == users.get_current_user():
			## Check User Permission to done this Item

			if tItem.routine == 'none':
				## if this item is not a routine item.
				tItem.donedate = datetime.datetime.now()
				tItem.done = True
				tItem.put()
			
			else:
				## if this item is a routine item.
				NewlyDoneRoutineItem = tarsusaRoutineLogItem(routine=tItem.routine)
				NewlyDoneRoutineItem.user = users.get_current_user()
				NewlyDoneRoutineItem.routineid = int(ItemId)
				if DoneYesterdaysDailyRoutine == True:
					NewlyDoneRoutineItem.donedate = datetime.datetime.now() - datetime.timedelta(days=1)
				
				#NewlyDoneRoutineItem.routine = tItem.routine
				# The done date will be automatically added by GAE datastore.			
				NewlyDoneRoutineItem.put()
					
				#memcache related. Clear ajax_DailyroutineTodayCache after add a daily routine item
				cachedUserDailyroutineToday = memcache.get("%s_dailyroutinetoday" % (str(CurrentUser.key().id())))
				if cachedUserDailyroutineToday:
					if not memcache.delete("%s_dailyroutinetoday" % (str(CurrentUser.key().id()))):
						logging.error('Memcache delete failed: Done a Daily RoutineItem')
				else:
					pass


		
		#self.redirect(self.request.uri)
		#self.redirect('/')


class UnDoneItem(tarsusaRequestHandler):
	def get(self):

		# Permission check is very important.

		ItemId = self.request.path[12:]
		UndoneYesterdaysDailyRoutine = False
		if ItemId[-2:] == '/y':
			ItemId = self.request.path[12:-2]			
			UndoneYesterdaysDailyRoutine = True
		
		## Please be awared that ItemId here is a string!
		tItem = tarsusaItem.get_by_id(int(ItemId))
		
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()
		

		if tItem.user == users.get_current_user():
			## Check User Permission to undone this Item

			if tItem.routine == 'none':
				## if this item is not a routine item.
				tItem.donedate = ""
				tItem.done = False

				tItem.put()
			else:
				if tItem.routine == 'daily':
					
					#memcache related. Clear ajax_DailyroutineTodayCache after add a daily routine item
					cachedUserDailyroutineToday = memcache.get("%s_dailyroutinetoday" % (str(CurrentUser.key().id())))
					if cachedUserDailyroutineToday:
						if not memcache.delete("%s_dailyroutinetoday" % (str(CurrentUser.key().id()))):
							logging.error('Memcache delete failed: delete Daily RoutinelogItem')
					else:
						pass
					
					if UndoneYesterdaysDailyRoutine != True:

						del tItem.donetoday
						tItem.put()
						## Please Do not forget to .put()!

						## This is a daily routine, and we are going to undone it.
						## For DailyRoutine, now I just count the matter of deleting today's record.
						## the code for handling the whole deleting routine( delete all concerning routine log ) will be added in future
						
						# GAE can not make dateProperty as query now! There is a BUG for GAE!
						# http://blog.csdn.net/kernelspirit/archive/2008/07/17/2668223.aspx
						
						tarsusaRoutineLogItemCollection_ToBeDeleted = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate < :2", int(ItemId), datetime.datetime.now())
					
						#It has been fixed. For just deleting TODAY's routinelog.
						one_day = datetime.timedelta(hours=24)
						yesterday = datetime.datetime.now() - one_day

						for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
							if result.donedate < datetime.datetime.now() and result.donedate.date() != yesterday.date() and result.donedate > yesterday:
								result.delete()
					else:
						# Undone Yesterday's daily routine item.	
						del tItem.doneyesterday
						tItem.put()
						
						tarsusaRoutineLogItemCollection_ToBeDeleted = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate < :2", int(ItemId), datetime.datetime.now() - datetime.timedelta(days=1))
					
						one_day = datetime.timedelta(days=1)
						yesterday = datetime.datetime.now() - one_day

						for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
							if result.donedate < datetime.datetime.now() and result.donedate.date() == yesterday.date() and result.donedate > datetime.datetime.now() - datetime.timedelta(days=2):
								result.delete()

		#self.redirect('/')

class RemoveItem(tarsusaRequestHandler):
	def get(self):
		#self.write('this is remove page')

		# Permission check is very important.

		ItemId = self.request.path[12:]
		## Please be awared that ItemId here is a string!
		tItem = tarsusaItem.get_by_id(int(ItemId))
			
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()

		if tItem.user == users.get_current_user():
			## Check User Permission to done this Item

			if tItem.routine == 'none':
				## if this item is not a routine item.
				tItem.delete()

			else:
				## Del a RoutineLog item!
				## All its doneRoutineLogWillBeDeleted!

				## wether there will be another log for this? :-) for record nerd?

				## This is a daily routine, and we are going to delete it.
				## For DailyRoutine, now I just count the matter of deleting today's record.
				## the code for handling the whole deleting routine( delete all concerning routine log ) will be added in future
				
				# GAE can not make dateProperty as query now! There is a BUG for GAE!
				# http://blog.csdn.net/kernelspirit/archive/2008/07/17/2668223.aspx
				tarsusaRoutineLogItemCollection_ToBeDeleted = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1", int(ItemId))
				for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
					result.delete()

				tItem.delete()

				#memcache related. Clear ajax_DailyroutineTodayCache after remove a routine item
				cachedUserDailyroutineToday = memcache.get("%s_dailyroutinetoday" % (str(CurrentUser.key().id())))
				if cachedUserDailyroutineToday:
					if not memcache.delete("%s_dailyroutinetoday" % (str(CurrentUser.key().id()))):
						logging.error('Memcache delete failed: Deleteing RoutineItem')


		self.redirect('/')

class UserToDoPage(tarsusaRequestHandler):
	def get(self):
		
		if users.get_current_user() != None:

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()	

			CountTotalItems = 0


			## SPEED KILLER!
			## MULTIPLE DB QUERIES!
			## CAUTION! MODIFY THESE LATER!
			tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC LIMIT 50", users.get_current_user())

			CountTotalItems = tarsusaItemCollection_UserToDoItems.count()
			strTodoStatus = "共有" + str(CountTotalItems) + "个未完成项目"

			template_values = {
				'PrefixCSSdir': "/",

				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(self.login_user.nickname()),
				'UserID': CurrentUser.key().id(),
				
				#'tarsusaItemCollection_DailyRoutine': tarsusaItemCollection_DailyRoutine,
				#'htmltag_DoneAllDailyRoutine': template_tag_donealldailyroutine,

				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
				'TodoStatus': strTodoStatus,
				#'UserTags': UserTags,

				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,

				#'UserTotalItems': UserTotalItems,
				#'UserToDoItems': UserToDoItems,
				#'UserDoneItems': UserDoneItems,
				#'UserDonePercentage': UserDonePercentage,
			}


			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/usertodopage.html')
			self.response.out.write(template.render(path, template_values))

class UserDonePage(tarsusaRequestHandler):
	def get(self):
		if users.get_current_user() != None:

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()	

			template_values = {
				'PrefixCSSdir': "/",

				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(self.login_user.nickname()),
				'UserID': CurrentUser.key().id(),
			}

			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/userdonepage.html')
			self.response.out.write(template.render(path, template_values))
		else:
			self.redirect('/')

class Showtag(tarsusaRequestHandler):
	def get(self):
		
		RequestCatName = urllib.unquote(self.request.path[5:])
		
		catlll = db.GqlQuery("SELECT * FROM Tag WHERE name = :1", RequestCatName.decode('utf-8'))

		#catlist = db.GqlQuery("SELECT * FROM Tag WHERE name = :1", RequestCatName)
		
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()	
		
		if self.request.path[5:] <> '':
			
			try:

				each_cat = catlll[0]
				UserNickName = users.get_current_user().nickname()
				
				CountDoneItems = 0
				CountTotalItems = 0

				
				#html_tag_DeleteThisTag = '<a href="/deleteTag/"' + str(each_cat.key().id()) + '>X</a>'
				html_tag_DeleteThisTag = ''
				## NOTICE that the /deleteTag should del the usertags in User model.

				#browser_Items = tarsusaItem(user=users.get_current_user(), routine="none")
				browser_Items = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY done, date DESC", users.get_current_user())

				html_tag_ItemList = ""
				for eachItem in browser_Items:
					for eachTag in eachItem.tags:
						try:

							if db.get(eachTag).name == RequestCatName.decode('utf-8'):								
								CountTotalItems += 1
								#self.write(eachItem.name)
								#html_tag_ItemList += eachItem.name + "<br />"
								if eachItem.done == False:
									html_tag_ItemList += '<a href=/i/' + str(eachItem.key().id()) + '>' + cgi.escape(eachItem.name) + "</a><br/>"
								else:
									html_tag_ItemList += '<img src="/img/accept16.png"><a href=/i/' + str(eachItem.key().id()) + '>' + cgi.escape(eachItem.name) + "</a><br/>"
									CountDoneItems += 1
								
						except:
							pass

				strTagStatus = "共有项目" + str(CountTotalItems) + "&nbsp;完成项目" + str(CountDoneItems) + "&nbsp;未完成项目" + str(CountTotalItems - CountDoneItems)

				template_values = {
						'PrefixCSSdir': "/",
						
						'UserLoggedIn': 'Logged In',
						'UserID': CurrentUser.key().id(),

						'UserNickName': users.get_current_user().nickname(),
						'DeleteThisTag': html_tag_DeleteThisTag,
						'TagName': each_cat.name,
						'TagStatus': strTagStatus,
						'ItemList': html_tag_ItemList,


				}

			
				path = os.path.join(os.path.dirname(__file__), 'pages/viewtag.html')
				self.response.out.write(template.render(path, template_values))

			except:
				## There is no this tag!
				## There is something wrong with Showtag!
				self.redirect("/")
				#pass


		else:
			
			if self.request.path[5:] == '':
				## Show Items with no tag.

				#browser_Items = tarsusaItem(user=users.get_current_user(), routine="none")
				browser_Items = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC", users.get_current_user())

				html_tag_DeleteThisTag = '无标签项目'

				CountDoneItems = 0
				CountTotalItems = 0

				html_tag_ItemList = ""
				for eachItem in browser_Items:
					if len(eachItem.tags) == 0:
						CountTotalItems += 1
						if eachItem.done == False:
							html_tag_ItemList += '<a href=/i/' + str(eachItem.key().id()) + '>' + cgi.escape(eachItem.name) + "</a><br/>"
						else:
							html_tag_ItemList += '<img src="/img/accept16.png"><a href=/i/' + str(eachItem.key().id()) + '>' + cgi.escape(eachItem.name) + "</a><br/>"
							CountDoneItems += 1
				
				strTagStatus = "共有项目" + str(CountTotalItems) + "&nbsp;完成项目" + str(CountDoneItems) + "&nbsp;未完成项目" + str(CountTotalItems - CountDoneItems)

				template_values = {
						'PrefixCSSdir': "/",
						
						'UserLoggedIn': 'Logged In',

						'UserNickName': users.get_current_user().nickname(),
						'DeleteThisTag': html_tag_DeleteThisTag,
						'TagName': "未分类项目",
						'TagStatus': strTagStatus,
						'ItemList': html_tag_ItemList,
				}
				
				path = os.path.join(os.path.dirname(__file__), 'pages/viewtag.html')
				self.response.out.write(template.render(path, template_values))

			else:
				## There is no this tag!
				self.redirect("/")



class LoginPage(tarsusaRequestHandler):
	def get(self):
		#Handle the URL like /Login/m/1
		try:
			destURL = urllib.unquote(cgi.escape(self.request.path[7:])) 
		except:
			pass
		
		self.redirect(users.create_login_url('/' + destURL))

class SignInPage(webapp.RequestHandler):
	def get(self):
		print "this is signinpage"

class SignOutPage(tarsusaRequestHandler):
	def get(self):
		#Handle the URL like /Logout/m/1
		try:
			destURL = urllib.unquote(cgi.escape(self.request.path[8:])) 
		except:
			pass
		
		self.redirect(users.create_logout_url('/' + destURL))

class UserSettingPage(tarsusaRequestHandler):
	def get(self):
		username = urllib.unquote(cgi.escape(self.request.path[6:-8])) ## Get the username in the middle of /user/CNBorn/setting

		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE urlname = :1", username)
		EditedUser = q.get()

		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()

		if EditedUser == None:
			## try another way
			## Get this user.
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE userid = :1 LIMIT 1", int(username))
			EditedUser = q.get()
		
		if EditedUser == None:
			## try another way
			## Get this user.
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE dispname = :1 LIMIT 1", username)
			EditedUser = q.get()



		if EditedUser is not None and CurrentUser is not None:			
			
			if CurrentUser.key().id() == EditedUser.key().id():

				from google.appengine.ext.db import djangoforms
				from django import newforms as forms 
				
				class ItemForm(djangoforms.ModelForm):
					
					## Custom djangoforms.ModelForm,
					## http://groups.google.com/group/google-appengine/browse_thread/thread/d3673d0ec7ead0e2
					
					#category = forms.CharField(widget=forms.HiddenInput())
					#description =	forms.CharField(widget=forms.Textarea(attrs={'rows':'10','cols':'70'})) 
					mail = 	forms.CharField(label='您的邮箱',widget=forms.TextInput(attrs={'size':'30','maxlength':'30','value':EditedUser.user.email()})) 
					#urlname =forms.CharField(label='URL显示地址',widget=forms.TextInput(attrs={'size':'30','maxlength':'30','value':CurrentUser.urlname}))
					dispname = forms.CharField(label='显示名称',widget=forms.TextInput(attrs={'size':'30','maxlength':'30','value':EditedUser.dispname}))
					website = forms.CharField(label='您的网址(请加http://)',widget=forms.TextInput(attrs={'size':'36','maxlength':'36','value':EditedUser.website}))	
					##Please reference more from the URL

					class Meta:
						model = tarsusaUser
						exclude =['user','userid','usedtags','urlname','friends','datejoinin']


				
				outputStringUserSettingForms = ItemForm().as_p() #also got as_table(), as_ul()

				

				## The Avatar part is inspired by 
				## http://blog.liangent.cn/2008/07/google-app-engine_28.html

			

				outputStringUserAvatarSetting = ""
				
				if EditedUser.avatar:
					outputStringUserAvatarImage = "<img src=/img?img_user=" + str(EditedUser.key()) + " width=64 height=64><br />" + cgi.escape(EditedUser.user.nickname()) + '&nbsp;<br />'
				else:
					outputStringUserAvatarImage = "<img src=/img/default_avatar.jpg width=64 height=64><br />" + cgi.escape(EditedUser.user.nickname()) + '&nbsp;<br />'

				
				outputStringUserAvatarSetting += '''
							 <form method="post" enctype="multipart/form-data"> 
							 选择图像文件(<1M): <input type="file" name="avatar"/ size=15>
							 <input type="submit" value="更新头像"/></form> '''.decode('utf-8')





				template_values = {
						'PrefixCSSdir': "/",
						
						'UserLoggedIn': 'Logged In',

						'EditedUserNickName': EditedUser.user.nickname(), 
						'UserNickName': CurrentUser.user.nickname(), #used for base template. Actully right here, shoudl be the same.
						
						'UserID': CurrentUser.key().id(), #This one used for base.html to identified setting URL.
						'EditedUserID': EditedUser.key().id(),

						'UserJoinInDate': datetime.datetime.date(EditedUser.datejoinin),

						'UserSettingForms': outputStringUserSettingForms,
						'UserAvatarImage': outputStringUserAvatarImage,
						'UserAvatarSetting': outputStringUserAvatarSetting,


						
				}

			
				path = os.path.join(os.path.dirname(__file__), 'pages/usersettingpage.html')
				self.response.out.write(template.render(path, template_values))

			else:
				# the editedUser is not CurrentUser.
				self.redirect("/")


		else:
			## can not find this user.
			self.redirect("/")


	def post(self):  
		
		#checkauth(self)  
		
		url_mime = 'image/'

		avatar = self.request.get('avatar') 
		mail = self.request.get('mail')
		dispname = self.request.get('dispname')
		website = self.request.get('website')
		
		if url_mime:  
			if avatar:
				
				# code below are comming from GAE example
				q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
				CurrentUser = q.get()

				avatar_image = images.resize(avatar,128,128)

				CurrentUser.avatar=db.Blob(avatar_image)
				CurrentUser.put()  
				
				if not memcache.set(str(CurrentUser.key()), db.Blob(avatar_image), 1800):
					logging.error("Memcache set failed: When uploading avatar_image")

				self.redirect("/user/" + CurrentUser.user.nickname() + "/setting")


			else:  
				
				# code below are comming from GAE example
				q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
				CurrentUser = q.get()	
				
				CurrentUser.mail = mail
				CurrentUser.dispname = dispname
				try:
					CurrentUser.website = website
				except:
					CurrentUser.website = "http://" + website
				CurrentUser.put()


				self.redirect("/user/" + str(CurrentUser.key().id()) + "/setting")




				if self.request.get('fetch') == 'yes':  
					try:
						fc = urlfetch.fetch(url_mime)  
						if fc.status_code == 200:  
							avatar = fc.content  
				 			if 'Content-Type' in fc.headers:  
								url_mime = fc.headers['Content-Type']  
							
								q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
								CurrentUser = q.get()
					
								
								self.write('noneok')
							else:
								#sendmsg(self, 'no content-type sent from remote server')
								self.write('ac')
						else:  
							#sendmsg(self, 'cannot fetch avatar: http status ' + str(fc.status_code))  
							self.write('avcx')
					except:  
						#sendmsg(self, 'cannot fetch avatar')  
						self.write('avcx')

				else:  
					try:
						avatar = Avatar(url_mime=url_mime)  
						avatar.put() 
						if not memcache.set(str(CurrentUser.key()), db.Blob(avatar_image), 1800):
							logging.error("Memcache set failed: When uploading(2) avatar_image")
						##if not memcache.add(self.request.get("img_user"), greeting.avatar, 1800):
						##	logging.error("Memcache set failed: When Loading avatar_image")


					except:
						pass
						self.redirect("/user/" + str(CurrentUser.key().id()) + "/setting")
					#sendmsg(self, 'added')  
		else:
			 #sendmsg(self, 'fill in the form!')  
			 self.write('please write')


class UserMainPage(tarsusaRequestHandler):
	def get(self):

		username = urllib.unquote(cgi.escape(self.request.path[6:]))  ## Get the username in the middle of /user/CNBorn/

		## Get this user.
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE urlname = :1 LIMIT 1", username)
		ViewUser = q.get()

		if ViewUser == None:
			try:
				## try another way
				## Get this user.
				q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE userid = :1 LIMIT 1", int(username))
				ViewUser = q.get()
			except:
				pass		
				
		if ViewUser == None:
			## try another way
			## Get this user.
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE dispname = :1 LIMIT 1", username)
			ViewUser = q.get()


		UserNickName = '访客'
		outputStringUserAvatar = ''

		if ViewUser != None:
				
			#self.write(ViewUser.avatar)
			#self.response.headers['Content-Type'] = 'image/'  #str(avatar.url_mime) 
			if ViewUser.avatar:
				outputStringUserAvatar = "<img src='/img?img_user=" + str(ViewUser.key()) + "' width=64 height=64>"
			else:
				#self.write('none image')
				#self.response.out.write(' %s</div>' % cgi.escape(greeting.content))
				#tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND public = True ORDER BY date DESC LIMIT 15", ViewUser)
				outputStringUserAvatar = "<img src='/img/default_avatar.jpg' width=64 height=64>"
			
			outputStringUserMainPageTitle = ViewUser.user.nickname() + "公开的项目".decode("utf-8")

				
				

			tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC", ViewUser.user)
			outputStringRoutineLog = ""
			
			if users.get_current_user() == None:
				UserNickName = "访客"
				logictag_OneoftheFriendsViewThisPage = False
				CurrentUserIsOneofViewUsersFriends = False
				UserFriends = '请登录查看此用户的朋友信息'
			else:
				UserNickName = ViewUser.user.nickname()

				## Check whether the currentuser is a friend of this User.
				## Made preparation for the following public permission check.

				# code below are comming from GAE example
				q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
				CurrentUser = q.get()

				CurrentUserIsOneofViewUsersFriends = False

				for each_Friend_key in ViewUser.friends:
					if each_Friend_key == CurrentUser.key():
						CurrentUserIsOneofViewUsersFriends = True
						logictag_OneoftheFriendsViewThisPage = True


				## Check whether the ViewedUser is a friend of CurrentUser.
				## For AddUserAsFriend button.
				ViewedUserIsOneofCurrentUsersFriends = False

				for each_Friend_key in CurrentUser.friends:
					if each_Friend_key == ViewUser.key():
						ViewedUserIsOneofCurrentUsersFriends = True

			
			for each_Item in tarsusaItemCollection_UserRecentPublicItems:
				## Added Item public permission check.
		
				if each_Item.public == 'publicOnlyforFriends' and CurrentUserIsOneofViewUsersFriends == True:
					if each_Item.done == True:
						outputStringRoutineLog += "<img src='/img/accept16.png'>" 
					outputStringRoutineLog += '<a href="/i/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
				elif each_Item.public == 'public':
					if each_Item.done == True:
						outputStringRoutineLog += "<img src='/img/accept16.png'>" 
					outputStringRoutineLog += '<a href="/i/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
				else:
					pass


			#Check This Users Friends.
			tarsusaUserFriendCollection = ViewUser.friends
			UserFriends = ''
			if tarsusaUserFriendCollection: 
				for each_FriendKey in tarsusaUserFriendCollection:
					UsersFriend =  db.get(each_FriendKey)
					if UsersFriend.avatar:
						UserFriends += '<dl class="obu2"><dt>' + '<a href="/user/' + cgi.escape(str(UsersFriend.key().id())) +  '">' + "<img src=/img?img_user=" + str(UsersFriend.key()) + " width=32 height=32>" + '</dt>'
					else:
						## Show Default Avatar
						UserFriends += '<dl class="obu2"><dt>' + '<a href="/user/' + cgi.escape(str(UsersFriend.key().id())) +  '">' + "<img src='/img/default_avatar.jpg' width=32 height=32>" + '</dt>'

					UserFriends += '<dd>' + cgi.escape(UsersFriend.user.nickname()) + '</a></dd></dl>'



			else:
				UserFriends = '当前没有添加朋友'




		else:
			#self.write('not found this user and any items')
			outputStringUserMainPageTitle = 'not found this user and any items'
			outputStringRoutineLog = 'None'
			self.error(404)

		if UserNickName != "访客":
			template_values = {
					'PrefixCSSdir': "../",
					
					'UserLoggedIn': 'Logged In',

					'UserID': CurrentUser.key().id(), #This indicates the UserSettingPage Link on the topright of the Page, so it should be CurrentUser

					'ViewedUserNickName': UserNickName,
					'UserNickName': CurrentUser.user.nickname(),
					'ViewedUser': ViewUser,

					'ViewedUserFriends': UserFriends,	

					'UserAvatarImage': outputStringUserAvatar,
					
					'UserJoinInDate': datetime.datetime.date(ViewUser.datejoinin),
					'UserWebsite': ViewUser.website,
					'UserMainPageUserTitle': outputStringUserMainPageTitle,
				
					'ViewedUserIsOneofCurrentUsersFriends': ViewedUserIsOneofCurrentUsersFriends,
					'StringRoutineLog': outputStringRoutineLog,
			}

		else:
				template_values = {
					'PrefixCSSdir': "../",
					
					'ViewedUserNickName': ViewUser.user.nickname(),

					'UserAvatarImage': outputStringUserAvatar,
					
					'ViewedUserFriends': UserFriends,	
					'UserJoinInDate': datetime.datetime.date(ViewUser.datejoinin),
					'UserWebsite': ViewUser.website,
					'UserMainPageUserTitle': outputStringUserMainPageTitle,
					'StringRoutineLog': outputStringRoutineLog,
			}



		path = os.path.join(os.path.dirname(__file__), 'pages/usermainpage.html')
		self.response.out.write(template.render(path, template_values))


class Image (webapp.RequestHandler):
	def get(self):
		#Add memcached here to improve the performence.
		usravatardata = memcache.get(self.request.get("img_user"))
  		
		if usravatardata is not None:
			self.response.headers['Content-Type'] = "image/"
			self.response.out.write(usravatardata)
  		else:
			
			# Request it from BigTable
			greeting = db.get(self.request.get("img_user"))
			
			if greeting.avatar:
				self.response.headers['Content-Type'] = "image/"
				self.response.out.write(greeting.avatar)
				
				if not memcache.set(self.request.get("img_user"), greeting.avatar, 7200):
					logging.error("Memcache set failed: When Loading avatar_image")
			else:
				self.error(404)

	

		


class DoneLogPage(tarsusaRequestHandler):
	def get(self):
		
		## TODO added permission check, anonymous user should not see any private donelog 
		
		#Donelog should shows User's Done Routine Log
		
		#Donelog page shows User Done's Log.
		
		username = urllib.unquote(cgi.escape(self.request.path[9:])) ## Get the username in the middle of /donelog/CNBorn
		
		if username == "": ## if the url are not directed to specific user.

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()

		else:
			
			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE urlname = :1", username)
			CurrentUser = q.get()
			if CurrentUser == None:
				## Can not find this user.
				self.redirect("/")


		tarsusaRoutineLogItemCollection = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 ORDER BY donedate DESC", CurrentUser.user)
		
		outputStringRoutineLog = ""
		Donedate_of_previousRoutineLogItem = None  ## To display the routine item log by Daily.

		for each_RoutineLogItem in tarsusaRoutineLogItemCollection:
			
			DoneDateOfThisItem = datetime.datetime.date(each_RoutineLogItem.donedate)

			if DoneDateOfThisItem != Donedate_of_previousRoutineLogItem:
				outputStringRoutineLog += ('<br /><h2 class="posttitle" style="font-weight:normal;">' + str(DoneDateOfThisItem) + '完成</h2><br />').decode('utf-8')
			
			## TODO
			## NOTICE! SPEED KILLER!
			#tarsusaItemCollection = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND "
			
			#tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC ", users.get_current_user(), each_tarsusaItemCollection_DailyRoutine.key().id())

			## Get what the name of this tarsusaItem is.
			ThisRoutineBelongingstarsusaItem = tarsusaItem.get_by_id(each_RoutineLogItem.routineid)
			
			if each_RoutineLogItem.routine != 'none':
				strRoutineLogItemPrompt = ''
				if each_RoutineLogItem.routine == 'daily':
					strRoutineLogItemPrompt = '每日'
				elif each_RoutineLogItem.routine == 'weekly':
					strRoutineLogItemPrompt = '每周'
				elif each_RoutineLogItem.routine == 'monthly':
					strRoutineLogItemPrompt = '每月'
				elif each_RoutineLogItem.routine == 'seasonly':
					strRoutineLogItemPrompt = '每季'
				elif each_RoutineLogItem.routine == 'yearly':
					strRoutineLogItemPrompt = '每年'

				outputStringRoutineLog += ('<img src="/img/accept16.png">' + strRoutineLogItemPrompt + '任务 - ').decode('utf-8')
			
				
			outputStringRoutineLog += '<a href=/i/' + str(ThisRoutineBelongingstarsusaItem.key().id()) + '>' + ThisRoutineBelongingstarsusaItem.name + "</a><br/>"

			Donedate_of_previousRoutineLogItem = DoneDateOfThisItem 

		## AT THIS PAgE
		## There should be also displaying ordinary items that done.
		## but since there will be a performance killer when selecting almost all doneitems
		## and a major con is that the date property in Datastore model can not be queried as a condition.
		## Thus made this thing more difficult.





		#tarsusaItemCollection = db.GqlQuery("SELECT * FROM tarsusaItem WHERE done = 1 ORDER BY date DESC")

		template_values = {
				'PrefixCSSdir': "../",
				
				'UserLoggedIn': 'Logged In',
				'UserID': CurrentUser.key().id(),
				'UserNickName': CurrentUser.user.nickname(), 
				'singlePageTitle': "",
				
				'StringRoutineLog': outputStringRoutineLog,
		}

	
		path = os.path.join(os.path.dirname(__file__), 'pages/donelog.html')
		self.response.out.write(template.render(path, template_values))





class StatsticsPage(tarsusaRequestHandler):
	def get(self):
	
		# Show statstics information.

		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()
		
		TotalUserCount = db.GqlQuery("SELECT * FROM tarsusaUser").count()
		TotaltarsusaItem = db.GqlQuery("SELECT * FROM tarsusaItem").count()
		
		htmltag = ''
		htmltag += 'Uptime: ' + str(datetime.datetime.now() - datetime.datetime(2008,8,26,20,0,0))
		htmltag += '<br />Project Started Since: ' + str(datetime.date.today() - datetime.date(2008, 7, 19)) + ' ago.'
		htmltag += '<br />User Account: ' + str(TotalUserCount)
		htmltag += '<br />Total Items: ' + str(TotaltarsusaItem)

		try:
			htmltag += '<br /><br /><b>memcached stats:</b>'
			stats = memcache.get_stats()    
			htmltag += "<br /><b>Cache Hits:</b>" + str(stats['hits'])
			htmltag += "<br /><b>Cache Misses:</b>" +str(stats['misses'])
					
			htmltag += "<br /><b>Total Requested Cache bytes:</b>" +str(stats['byte_hits'])
			htmltag += "<br /><b>Total Cache items:</b>" +str(stats['items'])
			htmltag += "<br /><b>Total Cache bytes:</b>" +str(stats['bytes'])
			htmltag += "<br /><b>Oldest Cache items:</b>" +str(stats['oldest_item_age'])
		except:
			pass

		if users.get_current_user() != None:

			template_values = {
				'UserLoggedIn': 'Logged In',				
				'UserNickName': cgi.escape(self.login_user.nickname()),
				'UserID': CurrentUser.key().id(),	
				
				'singlePageTitle': 'Statstics',
				'singlePageContent': htmltag,

				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
				'htmltag_TotalUser': TotalUserCount,
				'htmltag_TotaltarsusaItem': TotaltarsusaItem,

			}
		else:
			template_values = {				
				'UserNickName': "访客",
				'AnonymousVisitor': "Yes",

				'SinglePageTitle': 'Statstics',
				'SinglePageContent': htmltag,

				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
				'htmltag_TotalUser': TotalUserCount,
				'htmltag_TotaltarsusaItem': TotaltarsusaItem,
			}

		#Manupilating Templates	
		path = os.path.join(os.path.dirname(__file__), 'pages/simple_page.html')
		self.response.out.write(template.render(path, template_values))

class DashboardPage(tarsusaRequestHandler):
	def get(self):
		print 'dashboard page'


class NotFoundPage(tarsusaRequestHandler):
	def get(self):
		
		self.redirect('/page/404.html')

def main():
	application = webapp.WSGIApplication([('/', MainPage),
								       ('/additem',AddItemProcess),
									   ('/edititem/\\d+', EditItemProcess), 
									   ('/i/\\d+',ViewItem),
									   ('/doneItem/\\d+.+',DoneItem),
									   ('/undoneItem/\\d+.+',UnDoneItem),
									   ('/removeItem/\\d+', RemoveItem),
									   ('/tag/.+',Showtag),
									   ('/tag/', Showtag),
									   ('/user/.+/setting',UserSettingPage),
									   ('/user/.+/todo',UserToDoPage),
									   ('/user/.+/done',UserDonePage),
									   ('/user/.+', UserMainPage),
									   ('/img', Image),
									   ('/Login.+',LoginPage),
								       ('/SignIn',SignInPage),
									   ('/SignOut.+',SignOutPage),
								       ('/donelog/.+',DoneLogPage),
								       ('/statstics',StatsticsPage),
									   ('/dashboard', DashboardPage),
									   ('.*',NotFoundPage)],
                                       debug=True)


	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
