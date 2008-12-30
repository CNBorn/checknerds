# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 0.7, codename Nevada
# - tarsusaItemCore.py
# Copyright (C) CNBorn, 2008
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn
#
# **************************************************************** 

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

import time
import datetime
import string

import memcache

from modules import *
from base import *
import logging

class DoneItem(tarsusaRequestHandler):
	def get(self):
		ItemId = self.request.path[10:]
		DoneYesterdaysDailyRoutine = False
		if ItemId[-2:] == '/y':
			ItemId = self.request.path[10:-2]			
			DoneYesterdaysDailyRoutine = True

		tItem = tarsusaItem.get_by_id(int(ItemId))
		
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()
		else:
			#self.redirect('/')
			self.redirect(self.referer)
		
		if tItem.user == users.get_current_user():
			## Check User Permission to done this Item

			if tItem.routine == 'none':
				## if this item is not a routine item.
				tItem.donedate = datetime.datetime.now()
				tItem.done = True
				tItem.put()

				memcache.event('doneitem', CurrentUser.key().id())
			
			else:
				## if this item is a routine item.
				NewlyDoneRoutineItem = tarsusaRoutineLogItem(routine=tItem.routine)
				NewlyDoneRoutineItem.user = users.get_current_user()
				NewlyDoneRoutineItem.routineid = int(ItemId)
				if DoneYesterdaysDailyRoutine == True:
					NewlyDoneRoutineItem.donedate = datetime.datetime.now() - datetime.timedelta(days=1)

					memcache.event('doneroutineitem_daily_yesterday', CurrentUser.key().id())
				else:
					memcache.event('doneroutineitem_daily_today', CurrentUser.key().id())
				
				#NewlyDoneRoutineItem.routine = tItem.routine
				# The done date will be automatically added by GAE datastore.			
				
				NewlyDoneRoutineItem.put()
					
		#self.redirect(self.request.uri)
		#self.redirect('/')
		self.redirect(self.referer)

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
		
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()
		else:
			#self.redirect('/')
			self.redirect(self.referer)

		if tItem.user == users.get_current_user():
			## Check User Permission to undone this Item

			if tItem.routine == 'none':
				## if this item is not a routine item.
				tItem.donedate = ""
				tItem.done = False

				tItem.put()
				
				memcache.event('undoneitem', CurrentUser.key().id())
			else:
				if tItem.routine == 'daily':				

					if UndoneYesterdaysDailyRoutine != True:

						del tItem.donetoday
						tItem.put()
						
						memcache.event('undoneroutineitem_daily_today', CurrentUser.key().id())
						
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
					else:
						# Undone Yesterday's daily routine item.	
						
						memcache.event('undoneroutineitem_daily_yesterday', CurrentUser.key().id())
						
						try:
							del tItem.doneyesterday
							tItem.put()
						except:
							pass
						
						one_day = datetime.timedelta(days=1)
						#yesterday = datetime.date.today() - one_day
						yesterday = datetime.datetime.combine(datetime.date.today() - one_day,datetime.time(0))
						tarsusaRoutineLogItemCollection_ToBeDeleted = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate > :2 and donedate < :3", int(ItemId), yesterday, datetime.datetime.today())
						## CAUTION: SOME ITEM MAY BE DONE IN THE NEXT DAY, SO THE DONEDATE WILL BE IN NEXT DAY
						## THEREFORE donedate>:2 and donedate<datetime.datetime.today() <--today() is datetime

						for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
							if result.donedate < datetime.datetime.now() and result.donedate.date() == yesterday.date(): #and result.donedate.date() > datetime.datetime.date(datetime.datetime.now() - datetime.timedelta(days=2)):
								result.delete()
							else:
								pass
		
		self.redirect(self.referer)

class RemoveItem(tarsusaRequestHandler):
	def get(self):
		ItemId = self.request.path[12:]
		## Please be awared that ItemId here is a string!
		tItem = tarsusaItem.get_by_id(int(ItemId))
			
		# Permission check is very important.
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()
		else:
			self.redirect('/')

		if tItem.user == users.get_current_user():
			## Check User Permission to done this Item
			if tItem.public != 'none':
				memcache.event('deletepublicitem', CurrentUser.key().id())

			if tItem.routine == 'none':
				## if this item is not a routine item.
				tItem.delete()
				
				memcache.event('deleteitem', CurrentUser.key().id())

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
				
				memcache.event('deleteroutineitem_daily', CurrentUser.key().id())

		#if self.referer[:2] == '/m':
		self.redirect(self.referer)
		#else:
		#	self.redirect('/')


class AddItemProcess(tarsusaRequestHandler):
	def post(self):
		
		if self.request.get('cancel') != "取消":
			
			#Check if comment property's length is exceed 500
			if len(self.request.get('comment'))>500:
				item_comment = self.request.get('comment')[:500]
			else:
				item_comment = self.request.get('comment')

			# Permission check is very important.
			# New CheckLogin code built in tarsusaRequestHandler 
			if self.chk_login:
				CurrentUser = self.get_user_db()
			else:
				#self.redirect('/')
				return False

			try:
				# The following code works on GAE platform.
				# it is weird that under GAE, it should be without .decode, but on localhost, it should add them!
				first_tarsusa_item = tarsusaItem(user=users.get_current_user(),name=cgi.escape(self.request.get('name')), comment=cgi.escape(item_comment),routine=cgi.escape(self.request.get('routine')))
				tarsusaItem_Tags = cgi.escape(self.request.get('tags')).split(",")
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
				first_tarsusa_item.usermodel = CurrentUser				
				first_tarsusa_item.put()
				
				# http://blog.ericsk.org/archives/1009
				# This part of tag process inspired by ericsk.
				# many to many

			except:
				## the following code works on the localhost GAE runtimes.
				try:
					first_tarsusa_item = tarsusaItem(user=users.get_current_user(),name=cgi.escape(self.request.get('name').decode('utf-8')), comment=cgi.escape(item_comment.decode('utf-8')),routine=cgi.escape(self.request.get('routine').decode('utf-8')))
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
					first_tarsusa_item.usermodel = CurrentUser
					first_tarsusa_item.put()
					
					tarsusaItem_Tags = cgi.escape(self.request.get('tags')).split(",")

				except:
					## SOMETHING WRONG
						self.write('something is wrong.') 
						return False
						# TODO JS can not catch this!

			
			#memcache related. Clear ajax_DailyroutineTodayCache after add a daily routine item
			if cgi.escape(self.request.get('routine')) == 'daily':
				memcache.event('addroutineitem_daily', CurrentUser.key().id())
			else:
				memcache.event('additem', CurrentUser.key().id())
			
			if cgi.escape(self.request.get('public')) != 'none':
				memcache.event('addpublicitem', CurrentUser.key().id())
		
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
			
			try:
				first_tarsusa_item.put()
			except:
				self.write('BadValueError')
				return False
			
			CurrentUser.put()

			#Added mobile redirect
			if self.referer[-6:] == "/m/add":
				self.redirect("/m/todo")

class EditItemProcess(tarsusaRequestHandler):
	def post(self):	

		tItemId = self.request.path[10:]
		## Please be awared that tItemId here is a string!
		tItem = tarsusaItem.get_by_id(int(tItemId))

		#Check if comment property's length is exceed 500
		if len(self.request.get('comment'))>500:
			item_comment = self.request.get('comment')[:500]
		else:
			item_comment = self.request.get('comment')

		# Permission check is very important.
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login:
			CurrentUser = self.get_user_db()
		else:
			self.redirect('/')

		
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
			tItem.comment = cgi.escape(item_comment)
			tItem.routine = cgi.escape(self.request.get('routine'))
			tItem.public = cgi.escape(self.request.get('public'))
			
			tItem.usermodel = CurrentUser
			tItem.put()

			#memcache related. Clear ajax_DailyroutineTodayCache after add a daily routine item
			if cgi.escape(self.request.get('routine')) == 'daily':			
				memcache.event('editroutineitem_daily', CurrentUser.key().id())
			else:
				memcache.event('editroutineitem', CurrentUser.key().id())
			
			if cgi.escape(self.request.get('public')) != 'none':
				memcache.event('editpublicitem', CurrentUser.key().id())
	
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


def main():
	application = webapp.WSGIApplication([('/doneItem/\\d+.+',DoneItem),
									   ('/undoneItem/\\d+.+',UnDoneItem),
									   ('/removeItem/\\d+', RemoveItem),
								       ('/additem',AddItemProcess),
									   ('/edititem/\\d+', EditItemProcess), 
									   ],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
