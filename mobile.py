# -*- coding: utf-8 -*-

#from django.conf import settings
#settings._target = None
import os
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



class mMainPage(tarsusaRequestHandler):
	def get(self):
		
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()
		
			#self.redirect("/m/" + str(CurrentUser.key().id()) + "/todo")
			
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
						## That means this tarsusaItem(as routine).donetoday should be removed.
							
						pass
				
				if DoneThisItemToday == False:
						## Problem solved by Added this tag. DoneThisItemToday
						try:
							del each_tarsusaItemCollection_DailyRoutine.donetoday
							each_tarsusaItemCollection_DailyRoutine.put()
						except:
							pass

			
			## Below begins user todo items. for MOBILE page.
			tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC LIMIT 5", users.get_current_user())
			
			
			
			template_values = {
				'UserLoggedIn': 'Logged In',
				'UserNickName': cgi.escape(CurrentUser.dispname),
				'UserID': CurrentUser.key().id(),
				'tarsusaItemCollection_DailyRoutine': tarsusaItemCollection_DailyRoutine,
				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
			}
			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/mobile_mainpage.html')
			self.response.out.write(template.render(path, template_values))


		else:
			##Show Mobile Welcome page
			template_values = {
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
			}
			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/mobile_welcomepage.html')
			self.response.out.write(template.render(path, template_values))


class mToDoPage(tarsusaRequestHandler):
	def get(self):
			
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()
			
			## Below begins user todo items. for MOBILE page.
			tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC LIMIT 9", CurrentUser.user)					
			
			template_values = {
				'UserLoggedIn': 'Logged In',
				'UserNickName': cgi.escape(CurrentUser.dispname),
				'UserID': CurrentUser.key().id(),
				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
			}
			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/mobile_todopage.html')
			self.response.out.write(template.render(path, template_values))
		
		else:
			self.redirect("/m/1")

class mDonePage(tarsusaRequestHandler):
	def get(self):
		pass

class mDoneLogPage(tarsusaRequestHandler):
	def get(self):
		pass
class mDailyRoutinePage(tarsusaRequestHandler):
	def get(self):
		pass
class mErrorPage(tarsusaRequestHandler):
	def get():
		print 'abc'





def main():
	application = webapp.WSGIApplication([('/m/.+/donelog',mDoneLogPage),
									   ('/m/.+/dailyroutine',mDailyRoutinePage),
									   ('/m/.+/todo',mToDoPage),
									   ('/m/.+/done',mDonePage),
									   ('/m/.+', mMainPage),

									   ('.*',mErrorPage)],
                                       debug=True)
	wsgiref.handlers.CGIHandler().run(application)
if __name__ == "__main__":
      main()
