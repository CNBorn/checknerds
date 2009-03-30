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
from modules import *
from base import *

import time, datetime

import memcache

## Caution!
## These funtions here won't check permission for login!

def get_tarsusaItemCollection(userid, done, routine='none', startdate='', enddate='', startdonedate='', enddonedate='', sort='asc', maxitems=9, omittopbottom=False):
	
	ThisUser = tarsusaUser.get_by_id(int(userid))
	Item_List = []
	
	#Get tarsusaItemCollection
	
	query = tarsusaItem.all()
	query.filter('user =', ThisUser.user)
	query.filter('routine =', routine)
	query.filter('done =', done)

	

	if startdate != '':
		print startdate
		query.filter('date >', startdate)
		query.order('date')
	if enddate != '':
		print enddate
		query.filter('date <', enddate)
		#query.order('-date')

	if startdonedate != '':
		query.filter('donedate >', startdonedate)
		query.order('donedate')
		#Above will cause that weird error.(Got nothing.)
	if enddonedate != '':
		query.filter('donedate <', enddonedate)
		#query.order('-donedate')
		
	if done == True:
		strOrderSort = 'donedate'
		if startdate == '':	
			#Default order by date DESC.	
			query.order('-donedate')
	else:
		strOrderSort = 'date'
		#Default order by date DESC.	
		query.order('-date')
	
	#If it doesn't run, run this line
	print strOrderSort


	tarsusaItemCollection_queryResults = query.fetch(limit=maxitems)
	for each_tarsusaItem in tarsusaItemCollection_queryResults:
		
		this_item = {'id' : str(each_tarsusaItem.key().id()), 'name' : each_tarsusaItem.name, 'date' : each_tarsusaItem.date, 'donedate': each_tarsusaItem.donedate, 'comment' : each_tarsusaItem.comment, 'routine' : each_tarsusaItem.routine, 'category' : each_tarsusaItem.done}
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
				Each_UserFriends['avatarpath'] =  '/img?avatar=' + str(UsersFriend.key().id())
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
							UserAvatar = '/img?avatar=' + str(tarsusaItem_UserFriendsRecentItems.usermodel.key().id())
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

def get_count_UserItemStats(CurrentUser):	
	#tarsusaCore.get_count_UserItemStats returns a dictionarty with the following properties(all int):
	#'UserTotalItems', 'UserToDoItems', 'UserDoneItems', 'UserDonePercentage'

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

def get_count_tarsusaUser():
	#Due to the limitation of GAE.
	#To handle results more than 1000.	
	UserCount1kMilestones = [] # has to be userid, int

	if len(UserCount1kMilestones) == 0:
		TotalUserCount = db.GqlQuery("SELECT * FROM tarsusaUser").count()
	else:
		TotalUserCount = 1000 * len(UserCount1kMilestones) + db.GqlQuery("SELECT * FROM tarsusaUser WHERE userid > :1", UserCount1kMilestones[len(UserCount1kMilestones) - 1]).count()
	
	return TotalUserCount

def get_count_tarsusaItem():
	#Due to the limitation of GAE.
	#To handle results more than 1000.
	tarsusaItem1kMilestones = [] # has to be create date of an item, str, like '2008-09-02'
	
	if len(tarsusaItem1kMilestones) == 0:
		TotaltarsusaItem = db.GqlQuery("SELECT * FROM tarsusaItem").count()
	else:
		TotaltarsusaItem = 1000 * len(tarsusaItem1kMilestones) + db.GqlQuery("SELECT * FROM tarsusaItem WHERE date > :1", datetime.datetime.strptime(tarsusaItem1kMilestones[len(tarsusaItem1kMilestones) - 1], "%Y-%m-%d")).count()
	
	return TotaltarsusaItem
