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

import memcache
import tarsusaCore

from modules import *
from base import *
import logging


class MainPage(tarsusaRequestHandler):
	def get(self):
	
		if users.get_current_user() != None:
			CurrentUser = self.get_user_db()
			
			if CurrentUser == None:
				# Create a User
				CurrentUser = tarsusaUser(user=users.get_current_user(), urlname=cgi.escape(users.get_current_user().nickname()))
				CurrentUser.put()

				## Added userid property.
				CurrentUser.userid = CurrentUser.key().id()
				CurrentUser.dispname = users.get_current_user().nickname()
				CurrentUser.put()
				
				logging.info("New User, id:" + str(CurrentUser.key().id()) + " name:" + CurrentUser.dispname)

				#ShardingCounter
				import shardingcounter
				shardingcounter.increment("tarsusaUser")

			
			else:
				## DB Model Patch
				## These code for registered user whose information are not fitted into the new model setting.
				
				#Run DB Model Patch	when User Logged in.
				#DBPatcher.chk_dbmodel_update(CurrentUser)
				#Run this at every ViewItem event

				## Added userid here.
				if CurrentUser.userid == None:
					CurrentUser.userid = CurrentUser.key().id()
					CurrentUser.put()
					

			
			## Check usedtags as the evaluation for Tags Model
			## TEMP CODE!
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
				
				'UserNickName': cgi.escape(CurrentUser.dispname),
				'UserID': CurrentUser.key().id(),
				
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 

				'UserTags': UserTags,


			}

			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/index.html')
			self.response.out.write(template.render(path, template_values))
			
		else:
			#WelcomePage for Non-registered Users.
			IsCachedWelcomePage = memcache.get_item('strCachedWelcomePage', 'global')
			
			if IsCachedWelcomePage:
				strCachedWelcomePage = IsCachedWelcomePage
			else:
				
				TotalUserCount = tarsusaCore.get_count_tarsusaUser()
				TotaltarsusaItem = tarsusaCore.get_count_tarsusaItem()

				## Homepage for Non-Registered Users.

				template_values = {
					'UserNickName': "访客",
					'AnonymousVisitor': "Yes",
					'htmltag_TotalUser': TotalUserCount,
					'htmltag_TotaltarsusaItem': TotaltarsusaItem,
				}

				#Manupilating Templates	
				path = os.path.join(os.path.dirname(__file__), 'pages/welcome.html')
				strCachedWelcomePage = template.render(path, template_values)
				memcache.set_item("strCachedWelcomePage", strCachedWelcomePage, 'global')

			self.response.out.write(strCachedWelcomePage)

class ViewItem(tarsusaRequestHandler):
	def get(self):
		postid = self.request.path[6:]
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

				#Fixed since r116, Now Anonymuse user can't see PublicToFriends items.
				if tItem.public == 'publicOnlyforFriends' and CurrentUserIsOneofAuthorsFriends == True:
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
				if tItem.public == 'publicOnlyforFriends' and CurrentUserIsOneofAuthorsFriends == True or tItem.public == 'public':
					tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routineid = :2 ORDER BY donedate DESC LIMIT 10", tItem.user, tItem.key().id())
				else:
					tarsusaItemCollection_DoneDailyRoutine = None
			else:
				tarsusaItemCollection_DoneDailyRoutine = None
				html_tag_tarsusaRoutineItem = None


			## Since Rev.7x Since GqlQuery can not filter, this function is disabled.	
			
			#Show Undone items in the same category, just like in tarsusa r6
			#Since Nevada allows mutiple tags, It finds item that with any one tags of this showing items.
			#Deprecated since r116.		

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
				## Fixed, 09.05.06
				tarsusaItemCollection_SameDayCreated = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND date > :2 AND date <:3 ORDER and public != 'none' BY date DESC LIMIT 20", tItem.user, yesterday_ofTheDay, nextday_ofTheDay)

				##TODO I found there is an issue with the permission settings.
				## When the ItemAuthor added CurrentUser as a friend, CurrentUser still can't see Author's friendpublic items
				## After the CurrentUser added AUthor as a friend, the FriendPub item appears.
				## Suspection as a wrong detection of Friends.
				## But later I found this could be useful. Both users should confirm their relationship before sharing the info.
				## Just have to figure out which part of code will cause this. :)
				## 09.05.06
	
				## Code from UserMainPage class.
				for each_Item in tarsusaItemCollection_SameDayCreated:
				## Added Item public permission check.
		
					if each_Item.public == 'publicOnlyforFriends':
						if each_Item.done == True:
							outputStringRoutineLog += "<img src='/img/accept16.png'>" 
						outputStringRoutineLog += '<a href="/item/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
					elif each_Item.public == 'public':
						if each_Item.done == True:
							outputStringRoutineLog += "<img src='/img/accept16.png'>" 
						outputStringRoutineLog += '<a href="/item/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
					else:
						pass


			elif logictag_OtherpeopleViewThisItem == True and CurrentUserIsOneofAuthorsFriends == False:
				## Display only public items.
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

class LoginPage(tarsusaRequestHandler):
	def get(self):
		self.redirect(self.get_login_url(True))
		#Only / have user registration code right now, but here will lead user to different pages.
		# disabled these code temporily

		#self.redirect(users.create_login_url('/'))

class SignOutPage(tarsusaRequestHandler):
	def get(self):
		self.redirect(self.get_logout_url(True))

class Image(webapp.RequestHandler):
	def get(self):
		#Add memcached here to improve the performence.
		usravatardata = memcache.get('img_useravatar' + self.request.get("avatar"))
  		
		if usravatardata is not None:
			self.response.headers['Content-Type'] = "image/png"
			self.response.out.write(usravatardata)
  		else:
			
			# Request it from BigTable
			#greeting = db.get(self.request.get("img_user"))
			AvatarUser = tarsusaUser.get_by_id(int(self.request.get("avatar")))			 
			
			if AvatarUser.avatar:
				self.response.headers['Content-Type'] = "image/png"
				self.response.out.write(AvatarUser.avatar)
				
				if not memcache.set('img_useravatar' + self.request.get("avatar"), AvatarUser.avatar, 7200):
					logging.error("Memcache set failed: When Loading avatar_image")
			else:
				self.error(404)

class DashboardPage(tarsusaRequestHandler):
	def get(self):
		self.write('ok')
	
class NotFoundPage(tarsusaRequestHandler):
	def get(self):
		
		self.redirect('/page/404.html')

def main():
	application = webapp.WSGIApplication([('/', MainPage),
									   ('/item/\\d+',ViewItem),
									   ('/image', Image),
									   ('/Login.+',LoginPage),
									   ('/Logout.+',SignOutPage),
									   ('/dashboard', DashboardPage),
									   ('.*',NotFoundPage)],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
