# -*- coding: utf-8 -*-
# CheckNerds 
# - tarsusaItemCore.py
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
from google.appengine.api import memcache


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
		if self.chk_login:
			CurrentUser = self.get_user_db()
		else:
			self.redirect('/')
		
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
		
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login:
			CurrentUser = self.get_user_db()
		else:
			self.redirect('/')

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
						one_day = datetime.timedelta(days=1)
						yesterday = datetime.datetime.now() - one_day

						for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
							if result.donedate < datetime.datetime.now() and result.donedate.date() != yesterday.date() and result.donedate > yesterday:
								result.delete()
					else:
						# Undone Yesterday's daily routine item.	
						try:
							del tItem.doneyesterday
							tItem.put()
						except:
							pass
						
						one_day = datetime.timedelta(days=1)
						#yesterday = datetime.date.today() - one_day
						yesterday = datetime.datetime.combine(datetime.date.today() - one_day,datetime.time(0))
						#self.write('y' + str(yesterday))
						tarsusaRoutineLogItemCollection_ToBeDeleted = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate > :2 and donedate < :3", int(ItemId), yesterday, datetime.datetime.today())
						## CAUTION: SOME ITEM MAY BE DONE IN THE NEXT DAY, SO THE DONEDATE WILL BE IN NEXT DAY
						## THEREFORE donedate>:2 and donedate<datetime.datetime.today() <--today() is datetime

						for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
							#self.write(str(result.donedate)+'#')
							if result.donedate < datetime.datetime.now() and result.donedate.date() == yesterday.date(): #and result.donedate.date() > datetime.datetime.date(datetime.datetime.now() - datetime.timedelta(days=2)):
								#self.write('got')
								result.delete()
							else:
								pass

class RemoveItem(tarsusaRequestHandler):
	def get(self):
		#self.write('this is remove page')

		# Permission check is very important.

		ItemId = self.request.path[12:]
		## Please be awared that ItemId here is a string!
		tItem = tarsusaItem.get_by_id(int(ItemId))
			
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login:
			CurrentUser = self.get_user_db()
		else:
			self.redirect('/')

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



def main():
	application = webapp.WSGIApplication([('/doneItem/\\d+.+',DoneItem),
									   ('/undoneItem/\\d+.+',UnDoneItem),
									   ('/removeItem/\\d+', RemoveItem),
									   ],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
