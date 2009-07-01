# -*- coding: utf-8 -*-

# ****************************************************************
# CheckNerds - www.checknerds.com
# version 1.0, codename Nevada
# - tarsusaCore.py
# Author: CNBorn, 2008-2009
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn
#
# Provides inner-API functions
#
# ****************************************************************

import urllib
import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext import search
import logging
from modules import *
from base import *

import time, datetime

import memcache

import shardingcounter

import service

## Caution!
## These funtions here won't check permission for login!

def get_tarsusaItemCollection(userid, done, routine='none', startdate='', enddate='', startdonedate='', enddonedate='', sort='asc', maxitems=9, omittopbottom=False, public='none'):
	
	ThisUser = tarsusaUser.get_by_id(int(userid))
	Item_List = []
	
	#Get tarsusaItemCollection
	query = tarsusaItem.all()
	#It seems that when query gets done=True, it returns nothing!
	
	#Newly Add done=None state
	if done != None:
		query.filter('done =', done)

	query.filter('user =', ThisUser.user)
	query.filter('routine =', routine)

	#Caution: Public setting will display all items by default.
	#When calling the function using external API, 
	#The Setting should be filtered first, 
	#In case users will be able to see other's items.
	if public != 'none':
		if public == 'nonprivate':
			query.filter('public !=', 'private')
		elif public == 'public':
			query.filter('public =', 'public')
		elif public == 'private':			
			query.filter('public =', 'private')
	else:
		#No matter what the public is.
		pass

	if startdate != '':
		#print startdate
		query.filter('date >', startdate)
		query.order('date')
	if enddate != '':
		#print enddate
		query.filter('date <', enddate)
		query.order('-date')

	if startdonedate != '':
		#logging.info('startdonedate')
		#logging.info(startdonedate)
		#above line could be used in testing

		query.filter('donedate >', startdonedate)
		query.order('donedate')
		#Above will cause that weird error.(Got nothing.)
	if enddonedate != '':
		#logging.info('enddonedate')
		#logging.info(enddonedate)
		#above line could be used in testing

		query.filter('donedate <', enddonedate)
		query.order('-donedate')
		
	if done == True:
		strOrderSort = 'donedate'
		if startdate == '' and enddonedate == '':	
			#Default order by date DESC.	
			#For example: Done first page.
			#logging.info('donefirstpage')
						
			#query.filter('done =', True)
			#query.filter('donedate !=', datetime.datetime.now())
			#logging.info(query.fetch(limit=9))
			query.order('-donedate')
	else:
		strOrderSort = 'date'
		#Default order by date DESC.	
		query.order('-date')
	
	#If it doesn't run, run this line
	#print strOrderSort


	tarsusaItemCollection_queryResults = query.fetch(limit=maxitems)
	for each_tarsusaItem in tarsusaItemCollection_queryResults:
		
		this_item = {'id' : str(each_tarsusaItem.key().id()), 'name' : each_tarsusaItem.name, 'done': each_tarsusaItem.done, 'date' : each_tarsusaItem.date, 'donedate': each_tarsusaItem.donedate, 'comment' : each_tarsusaItem.comment, 'routine' : each_tarsusaItem.routine}
		Item_List.append(this_item)
	#print Item_List

	#sort the results order by donedate:
	#Sort Algorithms from
	#http://www.lixiaodou.cn/?p=12
	length = len(Item_List)
	
	for i in range(0,length):
		for j in range(length-1,i,-1):
				if Item_List[j][strOrderSort] > Item_List[j-1][strOrderSort]:
					temp = Item_List[j]
					Item_List[j]=Item_List[j-1]
					Item_List[j-1]=temp
	#---

	return Item_List

def get_dailyroutine(userid):

	ThisUser = tarsusaUser.get_by_id(int(userid))
	# Show His Daily Routine.
	
	tarsusaItemCollection_DailyRoutine = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'daily' ORDER BY date DESC", ThisUser.user)
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

		tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC ", ThisUser.user, each_tarsusaItemCollection_DailyRoutine.key().id())
		
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
		elif int(tarsusaItemCollection_DailyRoutine_count) == 0:
			template_tag_donealldailyroutine = '还没有添加每日计划？赶快添加吧！<br />只要在添加项目时，将“性质”设置为“每天要做的”就可以了！'
		
		Item_List = []		
		#'tarsusaItemCollection_DailyRoutine': tarsusaItemCollection_DailyRoutine,
		for each_tarsusaItem in tarsusaItemCollection_DailyRoutine:
			this_item = {'id' : str(each_tarsusaItem.key().id()), 'name' : each_tarsusaItem.name, 'date' : each_tarsusaItem.date, 'donedate': each_tarsusaItem.donedate, 'expectdate': each_tarsusaItem.expectdate, 'comment' : each_tarsusaItem.comment, 'routine' : each_tarsusaItem.routine, 'category' : each_tarsusaItem.done}
			Item_List.append(this_item)

		return Item_List

def get_ItemsDueToday(userid):
	#Get User's Items that are due today.
	
	#This is designed to be a inner-callfunction.
	#Not intended as a API for other users.
	
	ThisUser = tarsusaUser.get_by_id(int(userid))
	Item_List = []

	one_day = datetime.timedelta(days=1)
	#yesterday = datetime.date.today() - one_day
	yesterday = datetime.datetime.combine(datetime.date.today() - one_day,datetime.time(0))
	endday = datetime.datetime.combine(datetime.date.today()+ one_day+ one_day, datetime.time(0))

	tarsusaItemCollection_DueToday = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and expectdate >=:2 and expectdate <=:3 ORDER BY expectdate DESC", ThisUser.user, yesterday, endday)

	try:
		for each_tarsusaItem in tarsusaItemCollection_DueToday:
			if each_tarsusaItem.date != each_tarsusaItem.expectdate:
				this_item = {'id' : str(each_tarsusaItem.key().id()), 'name' : each_tarsusaItem.name, 'date' : each_tarsusaItem.date, 'donedate': each_tarsusaItem.donedate, 'expectdate': each_tarsusaItem.expectdate, 'comment' : each_tarsusaItem.comment, 'routine' : each_tarsusaItem.routine, 'category' : each_tarsusaItem.done}
				Item_List.append(this_item)

		#print Item_List
		return Item_List
	except NameError:
		logging.info("tarsusaCore.get_ItemsDueToday got nothing.")
		return None
	
def get_UserDonelog(userid, startdate='', lookingfor='next', maxdisplaydonelogdays=7):

	#Get user's donelog
	#lookingfor = 'next' to get the records > startdate
	#			  'previous' to get the records <= startdate



	#Have to add this limit for GAE's CPU limitation.
	MaxDisplayedDonelogDays = maxdisplaydonelogdays
	ThisUser = tarsusaUser.get_by_id(int(userid))
	
	#---
	Item_List = []
	DisplayedDonelogDays = 1 

	userid = ThisUser.key().id()
	
	if startdate != '':
		if lookingfor == 'next':
			tarsusaRoutineLogItemCollection = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 AND donedate > :2 ORDER BY donedate DESC", ThisUser.user, startdate)
		else:
			tarsusaRoutineLogItemCollection = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 AND donedate <= :2 ORDER BY donedate DESC", ThisUser.user, startdate)

	else:
		tarsusaRoutineLogItemCollection = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 ORDER BY donedate DESC", ThisUser.user)
			
	Donedate_of_previousRoutineLogItem = None  ## To display the routine item log by Daily.

	for each_RoutineLogItem in tarsusaRoutineLogItemCollection:
		
		DoneDateOfThisItem = datetime.datetime.date(each_RoutineLogItem.donedate)
		if DisplayedDonelogDays > MaxDisplayedDonelogDays:
			break
		
		if DoneDateOfThisItem != Donedate_of_previousRoutineLogItem:
			DisplayedDonelogDays += 1

		## Get what the name of this RoutinetarsusaItem is.
		ThisRoutineBelongingstarsusaItem = tarsusaItem.get_by_id(each_RoutineLogItem.routineid)
	
		this_item = {'id' : str(ThisRoutineBelongingstarsusaItem.key().id()), 'name' : ThisRoutineBelongingstarsusaItem.name, 'date' : str(ThisRoutineBelongingstarsusaItem.date), 'donedate': each_RoutineLogItem.donedate, 'comment' : ThisRoutineBelongingstarsusaItem.comment, 'routine' : ThisRoutineBelongingstarsusaItem.routine, 'category' : 'doneroutine'}
		Item_List.append(this_item)

		
		##TODO
		##CAUTION: OTHER PEOPLE WILL SEE THIS PAGE AND THERE IS NO CODE FOR PUBLIC CHECK.

		#Show ordinary items that are created in that day
		TheDay = DoneDateOfThisItem
		one_day = datetime.timedelta(days=1)
		yesterday_ofTheDay = datetime.datetime.combine(TheDay - one_day, datetime.time(0))
		nextday_ofTheDay = datetime.datetime.combine(TheDay + one_day, datetime.time(0))

		tarsusaItemCollection_ThisDayCreated = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND donedate > :2 AND donedate <:3 AND done = True ORDER BY donedate DESC", ThisUser.user, yesterday_ofTheDay, nextday_ofTheDay)
		for each_doneItem_withinOneday in tarsusaItemCollection_ThisDayCreated:
			
			this_item = {'id' : str(each_doneItem_withinOneday.key().id()), 'name' : each_doneItem_withinOneday.name, 'date' : str(each_doneItem_withinOneday.date), 'donedate': each_doneItem_withinOneday.donedate, 'comment' : each_doneItem_withinOneday.comment, 'routine' : each_doneItem_withinOneday.routine, 'category' : 'done'}
			
			#Prevent to add duplicated tarsusaItem here.
			Duplicated_tarsusaItem_Inlist = False
			for check_for_duplicated_tarsusaItem in Item_List:
				if check_for_duplicated_tarsusaItem['id'] == this_item['id'] and check_for_duplicated_tarsusaItem['donedate'] == this_item['donedate']:
					Duplicated_tarsusaItem_Inlist = True
			if Duplicated_tarsusaItem_Inlist == False:
				Item_List.append(this_item)

		Donedate_of_previousRoutineLogItem = DoneDateOfThisItem 

	#sort the results order by donedate:
	#Sort Algorithms from
	#http://www.lixiaodou.cn/?p=12
	length = len(Item_List)
	for i in range(0,length):
		for j in range(length-1,i,-1):
				if Item_List[j]['donedate'] > Item_List[j-1]['donedate']:
					temp = Item_List[j]
					Item_List[j]=Item_List[j-1]
					Item_List[j-1]=temp
	#---

	return Item_List

def get_UserNonPrivateItems(userid, public='public', maxdisplayitems=30):
	#Get users non-private items.
	ViewUser = tarsusaUser.get_by_id(int(userid))
	
	#---
	Item_List = []
	DisplayedItems = 1 

	#Currently I just make the LIMIT number fixed.
	if public == 'public':
		tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and public = 'public' ORDER BY date DESC LIMIT 30", ViewUser.user)
	elif public == 'publicOnlyforFriends':
		tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and public != 'private' ORDER BY public, date DESC LIMIT 30", ViewUser.user)

	for each_Item in tarsusaItemCollection_UserRecentPublicItems:
		this_item = {'id' : str(each_Item.key().id()), 'name' : each_Item.name, 'date' : str(each_Item.date), 'donedate': each_Item.donedate, 'comment' : each_Item.comment, 'routine' : each_Item.routine, 'done' : each_Item.done}	
		Item_List.append(this_item)
	
	return Item_List

def get_UserFriends(userid):
	#Get user's friend list.

	#Output: Dict in which indicates a friend's id, avatarpath, name

	ViewUser = tarsusaUser.get_by_id(int(userid))	
	tarsusaUserFriendCollection = ViewUser.friends
	
	UserFriends = []

	if tarsusaUserFriendCollection: 
		
		for each_FriendKey in tarsusaUserFriendCollection:
			UsersFriend =  db.get(each_FriendKey)
			Each_UserFriends = {'id': str(UsersFriend.key().id())}
						
			if UsersFriend.avatar:
				Each_UserFriends['avatarpath'] =  '/image?avatar=' + str(UsersFriend.key().id())
			else:
				Each_UserFriends['avatarpath'] =  '/img/default_avatar.jpg'

			#These code is here due to DB Model change since Rev.76
			try:								
				Each_UserFriends['name'] = cgi.escape(UsersFriend.dispname)
			except:
				Each_UserFriends['name'] = cgi.escape(UsersFriend.user.nickname())

			UserFriends.append(Each_UserFriends)

	return UserFriends

def get_UserFriendStats(userid, startdate='', lookingfor='next', maxdisplayitems=15):
	
	#Get user's FriendStats
	#SHOW YOUR FRIENDs Recent Activities
	
	#lookingfor = 'next' to get the records > startdate
	#			  'previous' to get the records <= startdate
	#actully you can not decide how many items will be displayed here. 15 will be a fixed number, maybe less than 15 will be displayed.

	#Have to add this limit for GAE's CPU limitation.
	MaxDisplayedItems = maxdisplayitems
	ThisUser = tarsusaUser.get_by_id(int(userid))
	
	#---
	userid = ThisUser.key().id()

	tarsusaUserFriendCollection = ThisUser.friends
	DisplayedDonelogDays = 1 

	UserFriendsItem_List = []

	if tarsusaUserFriendCollection:
		#first of all, CurrentUser should have some friends

		for each_FriendKey in tarsusaUserFriendCollection:
			UsersFriend =  db.get(each_FriendKey)						
			
			#Due to usermodel and other are applied in a later patch, some tarsusaItem may not have that property.
			#There maybe need to extend if we need more property from tarsusaItem.usermodel
			UsersFriendid = UsersFriend.key().id()
			try:
				UsersFriendDispname = UsersFriend.dispname
			except:
				UsersFriendDispname = UsersFriend.user.nickname()


			tarsusaItemCollection_UserFriendsRecentItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC LIMIT 50", UsersFriend.user)

			for tarsusaItem_UserFriendsRecentItems in tarsusaItemCollection_UserFriendsRecentItems:
				## Check whether should show this item.
				if tarsusaItem_UserFriendsRecentItems.public != 'private':						
					#Output Avatar Information
					UserAvatar = '/img/default_avatar.jpg'
					#Some of the older items may not have the usermodel property
					try:
						if tarsusaItem_UserFriendsRecentItems.usermodel.avatar:
							UserAvatar = '/image?avatar=' + str(tarsusaItem_UserFriendsRecentItems.usermodel.key().id())
					except:
						UserAvatar = '/img/default_avatar.jpg'

					## Check whether this item had done.
					if tarsusaItem_UserFriendsRecentItems.done == True:
							friend_Item = {'id' : str(tarsusaItem_UserFriendsRecentItems.key().id()), 'name' : tarsusaItem_UserFriendsRecentItems.name, 'date' : str(tarsusaItem_UserFriendsRecentItems.donedate), 'comment' : tarsusaItem_UserFriendsRecentItems.comment, 'category' : 'done', 'userdispname': UsersFriendDispname, 'userid': UsersFriendid, 'avatar': UserAvatar}
					else:
						friend_Item = {'id' : str(tarsusaItem_UserFriendsRecentItems.key().id()), 'name' : tarsusaItem_UserFriendsRecentItems.name, 'date' : str(tarsusaItem_UserFriendsRecentItems.date), 'comment' : tarsusaItem_UserFriendsRecentItems.comment, 'category' : 'todo', 'userdispname': UsersFriendDispname, 'userid': UsersFriendid, 'avatar': UserAvatar}

					UserFriendsItem_List.append(friend_Item)

		#sort the results:
		#Sort Algorithms from
		#http://www.lixiaodou.cn/?p=12
		length = len(UserFriendsItem_List)
		for i in range(0,length):
			for j in range(length-1,i,-1):
					#Convert string to datetime.date
					#http://mail.python.org/pipermail/tutor/2006-March/045729.html	
					time_format = "%Y-%m-%d %H:%M:%S"
					if datetime.datetime.fromtimestamp(time.mktime(time.strptime(UserFriendsItem_List[j]['date'][:-7], time_format))) > datetime.datetime.fromtimestamp(time.mktime(time.strptime(UserFriendsItem_List[j-1]['date'][:-7], time_format))):
						temp = UserFriendsItem_List[j]
						UserFriendsItem_List[j]=UserFriendsItem_List[j-1]
						UserFriendsItem_List[j-1]=temp
	#---
	return UserFriendsItem_List[:maxdisplayitems]

def get_count_UserItemStats(userid):	
	#tarsusaCore.get_count_UserItemStats returns a dictionarty with the following properties(all int):
	#'UserTotalItems', 'UserToDoItems', 'UserDoneItems', 'UserDonePercentage'
	CurrentUser = tarsusaUser.get_by_id(int(userid))

	# Count User's Todos and Dones
	cachedUserItemStats = memcache.get_item("itemstats", CurrentUser.key().id())
	if cachedUserItemStats is not None:
		template_values = cachedUserItemStats
	else:
		# Count User's Todos and Dones
		tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True ORDER BY date DESC", users.get_current_user())				
		tarsusaItemCollection_UserTodoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC", users.get_current_user())				

		# For Count number, It is said that COUNT in GAE is not satisfied and accuracy.
		# SO there is implemented a stupid way.
		UserTotalItems = tarsusaItemCollection_UserDoneItems.count() + tarsusaItemCollection_UserTodoItems.count()
		UserToDoItems = 0
		UserDoneItems = 0

		UserDonePercentage = 0.00

		UserDoneItems = tarsusaItemCollection_UserDoneItems.count() 
		UserToDoItems = tarsusaItemCollection_UserTodoItems.count()

		if UserTotalItems != 0:
			UserDonePercentage = UserDoneItems *100 / UserTotalItems 
		else:
			UserDonePercentage = 0.00

		template_values = {
			'UserTotalItems': UserTotalItems,
			'UserToDoItems': UserToDoItems,
			'UserDoneItems': UserDoneItems,
			'UserDonePercentage': UserDonePercentage,
		}
		
		#Changed since r111,
		#Now cache the Results from DB.
		memcache.set_item("itemstats", template_values, CurrentUser.key().id())


	return template_values 

def DoneItem(ItemId, UserId, Misc):
	#DoneItem function specially designed for API calls.	
	#Duplicated Code from tarsusaItemCore, refactor needed in the future.
	
	## This function won't check permission for login, for external API usage.
	#Instead, you need to provide a userid, and the function will check wheather this user have the permission to do so.
	#Which indicates that you definately need a permission check mechanism when you calling this function from outside.

	DoneYesterdaysDailyRoutine = False
	if Misc == 'y':
		DoneYesterdaysDailyRoutine = True

	tItem = tarsusaItem.get_by_id(int(ItemId))
	
	if tItem.usermodel.key().id() == int(UserId):
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

			#To Check whether this routine item was done today.
			#Prevention to add duplicate tarsusaRoutineLogItem.
			one_day = datetime.timedelta(days=1)
			yesterday = datetime.datetime.combine(datetime.date.today() - one_day, datetime.time(0))
			if DoneYesterdaysDailyRoutine == False:
				tarsusaRoutineLogItemCollection_CheckWhetherBeDone = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate > :2 and donedate < :3", int(ItemId), yesterday + one_day ,datetime.datetime.now())
			else:
				tarsusaRoutineLogItemCollection_CheckWhetherBeDone = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate > :2 and donedate < :3", int(ItemId), yesterday - one_day , datetime.datetime.combine(datetime.date.today(), datetime.time(0)) - datetime.timedelta(seconds=1))

			if not tarsusaRoutineLogItemCollection_CheckWhetherBeDone.count() >= 1:
				NewlyDoneRoutineItem.put()
			
			return 0
			#self.write(tarsusaRoutineLogItemCollection_CheckWhetherBeDone.count())

	else:
		return 1

def UndoneItem(ItemId, UserId, Misc):
	#UndoneItem function specially designed for API calls.	
	#Duplicated Code from tarsusaItemCore, refactor needed in the future.
	
	## This function won't check permission for login, for external API usage.
	#Instead, you need to provide a userid, and the function will check wheather this user have the permission to do so.
	#Which indicates that you definately need a permission check mechanism when you calling this function from outside.
	# Permission check is very important.

	UndoneYesterdaysDailyRoutine = False
	if Misc == 'y':
		UndoneYesterdaysDailyRoutine = True

	## Please be awared that ItemId here is a string!
	tItem = tarsusaItem.get_by_id(int(ItemId))

	if tItem.usermodel.key().id() == int(UserId):
		## Check User Permission to undone this Item

		if tItem.routine == 'none':
			## if this item is not a routine item.
			tItem.donedate = ""
			tItem.done = False
			tItem.put()
			#-----	
			memcache.event('undoneitem', int(UserId))
			#return 0 indicates it's ok.
			return 0

		else:
			if tItem.routine == 'daily':				

				if UndoneYesterdaysDailyRoutine != True:

					del tItem.donetoday
					tItem.put()
					
					memcache.event('undoneroutineitem_daily_today', int(UserId))
					
					## Please Do not forget to .put()!

					## This is a daily routine, and we are going to undone it.
					## For DailyRoutine, now I just count the matter of deleting today's record.
					## the code for handling the whole deleting routine( delete all concerning routine log ) will be added in future
					
					# GAE can not make dateProperty as query now! There is a BUG for GAE!
					# http://blog.csdn.net/kernelspirit/archive/2008/07/17/2668223.aspx
					
					tarsusaRoutineLogItemCollection_ToBeDeleted = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate < :2", int(ItemId), datetime.datetime.now())
				
					#It has been fixed. For just deleting TODAY's routinelog.
					one_day = datetime.timedelta(days=1)
					yesterday = datetime.datetime.now() - one_day

					for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
						if result.donedate < datetime.datetime.now() and result.donedate.date() != yesterday.date() and result.donedate > yesterday:
							result.delete()

					#return 0 indicates it's ok.
					return 0

				else:
					# Undone Yesterday's daily routine item.	
					
					memcache.event('undoneroutineitem_daily_yesterday', int(UserId))
					
					try:
						del tItem.doneyesterday
						tItem.put()
					except:
						pass
					
					one_day = datetime.timedelta(days=1)
					yesterday = datetime.datetime.combine(datetime.date.today() - one_day,datetime.time(0))
					tarsusaRoutineLogItemCollection_ToBeDeleted = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate > :2 and donedate < :3", int(ItemId), yesterday, datetime.datetime.today())
					## CAUTION: SOME ITEM MAY BE DONE IN THE NEXT DAY, SO THE DONEDATE WILL BE IN NEXT DAY
					## THEREFORE donedate>:2 and donedate<datetime.datetime.today() <--today() is datetime

					for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
						if result.donedate < datetime.datetime.now() and result.donedate.date() == yesterday.date(): #and result.donedate.date() > datetime.datetime.date(datetime.datetime.now() - datetime.timedelta(days=2)):
							result.delete()
						else:
							pass
					
					return 0
	else:
		#Authentication failed.
		return 1

def AddItem(UserId, rawName, rawComment='', rawRoutine='', rawPublic='private', rawInputDate='', rawTags=None):
	
	CurrentUser = tarsusaUser.get_by_id(int(UserId))

	#Check if comment property's length is exceed 500
	try:
		if len(rawComment)>500:
			item_comment = rawComment[:500]
		else:
			item_comment = rawComment
	except:
		item_comment = ''

	try:
		# The following code works on GAE platform.
		# it is weird that under GAE, it should be without .decode, but on localhost, it should add them!
		item2beadd_name = cgi.escape(rawName)				

		try:
			item2beadd_comment = cgi.escape(item_comment)
		except:
			item2beadd_comment = ''
							
		try:
			tarsusaItem_Tags = cgi.escape(rawTags).split(",")
		except:
			tarsusaItem_Tags = None 

		#routine is a must provided in template, by type=hidden
		item2beadd_routine = cgi.escape(rawRoutine)

		first_tarsusa_item = tarsusaItem(user=users.get_current_user(), name=item2beadd_name, comment=item2beadd_comment, routine=rawRoutine)
		first_tarsusa_item.public = rawPublic
		first_tarsusa_item.done = False

		# DATETIME CONVERTION TRICKS from http://hi.baidu.com/huazai_net/blog/item/8acb142a13bf879f023bf613.html
		# The easiest way to convert this to a datetime seems to be;
		#datetime.date(*time.strptime("8/8/2008", "%d/%m/%Y")[:3])
		# the '*' operator unpacks the tuple, producing the argument list.	
		# also learned sth from: http://bytes.com/forum/thread603681.html

		# Logic: If the expectdate is the same day as today, It is none.
		try:
			expectdatetime = None
			expectdate = datetime.date(*time.strptime(rawInputDate,"%Y-%m-%d")[:3])
			if expectdate == datetime.datetime.date(datetime.datetime.today()):
				expectdatetime == None
			else:
				currenttime = datetime.datetime.time(datetime.datetime.now())
				expectdatetime = datetime.datetime(expectdate.year, expectdate.month, expectdate.day, currenttime.hour, currenttime.minute, currenttime.second, currenttime.microsecond)
		except:
			expectdatetime = None
		first_tarsusa_item.expectdate =  expectdatetime

		## the creation date will be added automatically by GAE datastore				
		first_tarsusa_item.usermodel = CurrentUser				
		#first_tarsusa_item.put()
		try:
			tarsusaItem_Tags = cgi.escape(rawTags).split(",")
		except:
			tarsusaItem_Tags = None

	except:
		#Something is wrong when adding the item.
		self.write("sth is wrong.")

	#memcache related. Clear ajax_DailyroutineTodayCache after add a daily routine item
	if item2beadd_routine == 'daily':
		memcache.event('addroutineitem_daily', CurrentUser.key().id())
	else:
		memcache.event('additem', CurrentUser.key().id())
	
	if cgi.escape(rawPublic) != 'private':
		memcache.event('addpublicitem', CurrentUser.key().id())

	if tarsusaItem_Tags != None:

		for each_tag_in_tarsusaitem in tarsusaItem_Tags:
			
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

	#ShardingCounter
	shardingcounter.increment("tarsusaItem")
	return first_tarsusa_item.key().id()
	
def get_count_tarsusaUser():
	#Added Jun, 18th 2009 's statstics of CheckNerds along with the newly implermented shardingCounter
	return 984 + shardingcounter.get_count("tarsusaUser")

def get_count_tarsusaItem():
	#Added Jun, 18th 2009 's statstics of CheckNerds along with the newly implermented shardingCounter
	return 995 + shardingcounter.get_count("tarsusaItem")

def verify_AppModel(apiappid, apiservicekey):
	import hashlib
	
	if apiappid == None or apiservicekey == None:
		return False
	
	#To Verify AppModel, Applications that uses CheckNerds API.
	ThisApp = AppModel.get_by_id(apiappid)
	if ThisApp == None:
		return False
	
	#At beginning, will not turn this on.
	#if ThisApp.enable == False:
	#	return False

	#Check with API Usage.
	AppApiUsage = memcache.get("appapiusage" + str(apiappid))	
	if AppApiUsage >= ThisApp.api_limit:
		#Api Limitation exceed.
		self.write('<h1>API Limitation exceed.</h1>')		
		logging.info("AppID:" + str(apiappid) + ":" + cgi.escape(ThisApp.name) + " has exceed its API limitation.")
		return False
	else:
		if hashlib.sha256(ThisApp.servicekey).hexdigest() == apiservicekey:
			#Accept this App
			#------------------------
			#Manipulating API calls count.
			if AppApiUsage == None:
				memkey = "appapiuseage" + str(apiappid)
				AppApiUsage = 0
			AppApiUsage += 1
			memcache.set_item("appapiusage", AppApiUsage, int(apiappid))
			#------------------------
			#Below line could be turned off.
			logging.info("AppID:" + str(apiappid) + ":" + cgi.escape(ThisApp.name) + " accessed via API")
			#------------------------
			return True
		else:
			#Authentication Failed.
			#Should return a status number in the future.
			return False


def verify_UserApi(userid, userapikey):
	import hashlib
	import service
	#To Verify UserApi, the Authentication process.
	
	#To check whether this user is existed.
	ThisUser = tarsusaUser.get_by_id(userid)
	if ThisUser == None:
		return False

	#Check with API Usage.
	UserApiUsage = memcache.get_item("userapiusage", int(userid))
	if UserApiUsage >= global_vars['apilimit']:
		#Api Limitation exceed.
		#self.write('<h1>API Limitation exceed.</h1>')
		return False
	else:
		if hashlib.sha256(ThisUser.apikey).hexdigest() == userapikey:
			#Should use log to monitor API usage.
			#Also there should be limitation for the apicalls/per hour.
			if UserApiUsage == None:
				UserApiUsage = 0
			UserApiUsage += 1
			memcache.set_item("userapiusage", UserApiUsage, int(userid))
			return True
		else:
			#Authentication Failed.
			return False





