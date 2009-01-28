# -*- coding: utf-8 -*-

# ****************************************************************
# CheckNerds - www.checknerds.com
# version 0.7, codename Nevada
# - tarsusaCore.py
# Copyright (C) CNBorn, 2008
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

## Caution!
## These funtions here won't check permission for login!

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
		yesterday_ofTheDay = datetime.datetime.combine(TheDay - one_day,datetime.time(0))
		nextday_ofTheDay = datetime.datetime.combine(TheDay + one_day, datetime.time(0))

		tarsusaItemCollection_ThisDayCreated = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND donedate > :2 AND donedate <:3 AND done = True ORDER BY donedate DESC", ThisUser.user, yesterday_ofTheDay, nextday_ofTheDay)
		for each_doneItem_withinOneday in tarsusaItemCollection_ThisDayCreated:
			
			this_item = {'id' : str(each_doneItem_withinOneday.key().id()), 'name' : each_doneItem_withinOneday.name, 'date' : str(each_doneItem_withinOneday.date), 'donedate': each_doneItem_withinOneday.donedate, 'comment' : each_doneItem_withinOneday.comment, 'routine' : each_doneItem_withinOneday.routine, 'category' : 'done'}
			Item_List.append(this_item)

		Donedate_of_previousRoutineLogItem = DoneDateOfThisItem 

	#tobeadded shuffled as donedate

	return Item_List
	
	#TODO
	# to make it desc by donedate!

	# to make it unique!
	# some tarsusaItem will be selected duplicatly because it selects item by the date scale.

