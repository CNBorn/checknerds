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

import datetime,time
import string
from google.appengine.ext.webapp import template
from google.appengine.api import images


from modules import *
from base import *

import memcache

import utilities

class mMainPage(tarsusaRequestHandler):
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
			
			#self.response.out.write(strcachedUserItemStats)

			template_values = {
				'UserLoggedIn': 'Logged In',
				'UserNickName': cgi.escape(CurrentUser.dispname),
				'UserID': CurrentUser.key().id(),
				'tarsusaItemCollection_Statstics': strcachedUserItemStats,
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
			}
		
			#Manupilating Templates	
			if utilities.get_UserAgent(os.environ['HTTP_USER_AGENT']) == 'iPod':
				path = os.path.join(os.path.dirname(__file__), 'pages/mobile_imainpage.html')
				self.response.out.write(template.render(path, template_values))
			else:			
				path = os.path.join(os.path.dirname(__file__), 'pages/mobile_mainpage.html')
				self.response.out.write(template.render(path, template_values))


		else:
			##Show Mobile Welcome page
			template_values = {
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
			}
			
			#Manupilating Templates	
			if utilities.get_UserAgent(os.environ['HTTP_USER_AGENT']) == 'iPod':
				path = os.path.join(os.path.dirname(__file__), 'pages/mobile_iwelcomepage.html')
				self.response.out.write(template.render(path, template_values))
			else:
				path = os.path.join(os.path.dirname(__file__), 'pages/mobile_welcomepage.html')
				self.response.out.write(template.render(path, template_values))

class mToDoPage(tarsusaRequestHandler):
	def get(self):
			
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()					
					
			try:
				pageid = self.request.path[len('/m/todo/'):]
				if pageid[:2] == 'p/':
					tag_ViewPreviousPage = True
					pageid = pageid[2:]
				else:
					tag_ViewPreviousPage = False
			except:
				pass

			if pageid != None and len(self.request.path) > 8:
				this_timestamp = datetime.datetime.fromtimestamp(int(pageid))
				
				if tag_ViewPreviousPage == True:
					tarsusaItemCollection_UserTodoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False and date > :2 ORDER BY date DESC LIMIT 9", CurrentUser.user, this_timestamp)
				else:
					tarsusaItemCollection_UserTodoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False and date <= :2 ORDER BY date DESC LIMIT 9", CurrentUser.user, this_timestamp)


			else:
				## Below begins user todo items. for MOBILE page.
				tarsusaItemCollection_UserTodoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC LIMIT 9", CurrentUser.user)
			
			#Determine next page			
			Find_Last_Index = 0
			previous_timestamp = 0
			next_timestamp = 0
			for each_item in tarsusaItemCollection_UserTodoItems:
				if Find_Last_Index == 0:
					previous_timestamp = int(time.mktime(each_item.date.timetuple()))
				next_timestamp = int(time.mktime(each_item.date.timetuple()))
				Find_Last_Index += 1	
			
			if Find_Last_Index == 1 and tag_ViewPreviousPage == True:
				self.redirect("/m/todo")
				
			if next_timestamp == 0 and previous_timestamp == 0:
				self.redirect("/m/todo")

			template_values = {
				'UserLoggedIn': 'Logged In',
				'UserNickName': cgi.escape(CurrentUser.dispname),
				'UserID': CurrentUser.key().id(),
				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserTodoItems,
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
			}
			
			if previous_timestamp != 0:
				template_values['previouspagestamp'] = previous_timestamp
			
			if next_timestamp != 0:
				template_values['nextpagestamp'] = next_timestamp
		
			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/mobile_todopage.html')
			self.response.out.write(template.render(path, template_values))
		
		else:
			self.redirect("/m/")

class mDonePage(tarsusaRequestHandler):
	def get(self):
			
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()
			
			try:
				pageid = self.request.path[len('/m/done/'):]
				if pageid[:2] == 'p/':
					tag_ViewPreviousPage = True
					pageid = pageid[2:]
				else:
					tag_ViewPreviousPage = False
			except:
				pass

			if pageid != None and len(self.request.path) > 8:
				this_timestamp = datetime.datetime.fromtimestamp(int(pageid))
				if tag_ViewPreviousPage == True:
					tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True and donedate > :2 ORDER BY donedate DESC LIMIT 9", CurrentUser.user, this_timestamp)
				else:
					tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True and donedate <= :2 ORDER BY donedate DESC LIMIT 9", CurrentUser.user, this_timestamp)


			else:
				## Below begins user todo items. for MOBILE page.
				tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True ORDER BY donedate DESC LIMIT 9", CurrentUser.user)					
					
			#Determine next page			
			Find_Last_Index = 0
			previous_timestamp = 0
			next_timestamp = 0
			for each_item in tarsusaItemCollection_UserDoneItems:
				if Find_Last_Index == 0:
					previous_timestamp = int(time.mktime(each_item.donedate.timetuple()))
				next_timestamp = int(time.mktime(each_item.donedate.timetuple()))
				Find_Last_Index += 1	
			
			if Find_Last_Index == 1 and tag_ViewPreviousPage == True:
				self.redirect("/m/done")
			
			
			
			template_values = {
				'UserLoggedIn': 'Logged In',
				'UserNickName': cgi.escape(CurrentUser.dispname),
				'UserID': CurrentUser.key().id(),
				'tarsusaItemCollection_UserDoneItems': tarsusaItemCollection_UserDoneItems,
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()),
			}
			
			if previous_timestamp != 0:
				template_values['previouspagestamp'] = previous_timestamp
			
			if next_timestamp != 0:
				template_values['nextpagestamp'] = next_timestamp
		
			if next_timestamp == 0 and previous_timestamp == 0:
				self.redirect("/m/done")


			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/mobile_donepage.html')
			self.response.out.write(template.render(path, template_values))
		
		else:
			self.redirect("/m/")

class mDoneLogPage(tarsusaRequestHandler):
	def get(self):
		pass

class mDailyRoutinePage(tarsusaRequestHandler):
	def get(self):
		
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()		
			
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
				'template_tag_donealldailyroutine': template_tag_donealldailyroutine,
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
			}
			#Manupilating Templates	
			if utilities.get_UserAgent(os.environ['HTTP_USER_AGENT']) == 'iPod':
				path = os.path.join(os.path.dirname(__file__), 'pages/mobile_idailyroutinepage.html')
				self.response.out.write(template.render(path, template_values))
			else:
				path = os.path.join(os.path.dirname(__file__), 'pages/mobile_dailyroutinepage.html')
				self.response.out.write(template.render(path, template_values))
		else:
			self.redirect("/m/")

class mViewItemPage(tarsusaRequestHandler):
	def get(self):
		
		postid = self.request.path[3:]
		tItem = tarsusaItem.get_by_id(int(postid))

		if tItem != None:  ## If this Item existed in Database.

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", tItem.user)
			ItemAuthorUser = q.get()

			#Patch since Rev.76
			try:
				if tItem.usermodel == None:
					tItem.usermodel = ItemAuthorUser
					tItem.put()
			except:
				tItem.usermodel = ItemAuthorUser
				tItem.put()
			#-------------------


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

			

			# New CheckLogin code built in tarsusaRequestHandler 
			if self.chk_login():
				CurrentUser = self.get_user_db()


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
						#Will be implemented a better way to show tag in Mobile Page.
						#ItemTags += '<a href=/tag/' + cgi.escape(each_tag.name) +  '>' + cgi.escape(each_tag.name) + '</a>&nbsp;'
						ItemTags += cgi.escape(each_tag.name) + '&nbsp;'
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

			
			if UserNickName != "访客":
				UserNickName = CurrentUser.dispname 

				template_values = {
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
		
						'UserNickName': cgi.escape(CurrentUser.dispname),
						'UserID': CurrentUser.key().id(),
						'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
						'RefererURL': self.referer,
				}
			else:
						template_values = {
						'singlePageTitle': "项目详细信息",
						'singlePageContent': "",
						'logictag_OtherpeopleViewThisItem': logictag_OtherpeopleViewThisItem,
						'tarsusaItem': tItem,
						'tarsusaItemDone': tItem.done,
						'tarsusaItemTags': ItemTags,
						'tarsusaRoutineItem': html_tag_tarsusaRoutineItem,
						'tarsusaRoutineLogItem': tarsusaItemCollection_DoneDailyRoutine,
						'UserNickName': cgi.escape(CurrentUser.dispname),
						'UserID': CurrentUser.key().id(),
						'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
						'RefererURL': self.referer,
				}
			path = os.path.join(os.path.dirname(__file__), 'pages/mobile_viewitempage.html')
			self.response.out.write(template.render(path, template_values))

		else:
			## Can't find this Item by this id.
			self.redirect('/m')

class mAddItemPage(tarsusaRequestHandler):
	def get(self):
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()
			strAddItemToday = str(datetime.datetime.date(datetime.datetime.now()))
			
			template_values = {'RefererURL': self.referer,
							'UserNickName': cgi.escape(CurrentUser.dispname),
							'UserID': CurrentUser.key().id(),
							'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
							'addItemToday': strAddItemToday.decode("utf-8"),
							}
			path = os.path.join(os.path.dirname(__file__), 'pages/mobile_additempage.html')
			self.response.out.write(template.render(path, template_values))
		else:
			self.redirect("/m")

class mErrorPage(tarsusaRequestHandler):
	def get(self):
		self.redirect("/m")

def main():
	application = webapp.WSGIApplication([('/m/donelog',mDoneLogPage),
									   ('/m/dailyroutine',mDailyRoutinePage),
									   ('/m/todo.*',mToDoPage),
									   ('/m/done.*',mDonePage),
									   ('/m/add',mAddItemPage),
									   ('/m/', mMainPage),
									   ('/m', mMainPage),
									   ('/i/.*', mViewItemPage),
									   #('/m.*',mMainPage)],
									   ('/m.*',mErrorPage)],
                                       debug=True)
	wsgiref.handlers.CGIHandler().run(application)
if __name__ == "__main__":
      main()
