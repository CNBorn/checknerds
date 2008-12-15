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

from modules import *
from base import *
import logging


class MainPage(tarsusaRequestHandler):
	def get(self):
	
		if users.get_current_user() != None:
			CurrentUser = self.get_user_db()
			
			if CurrentUser == None:
				# Create a User
				# Actully I thought this would be useless when I have an signin page.
				
				#Give vreated user a default avatar image.
				#avatar_image = images.resize('/img/default_avatar.jpg',64,64)
				#do not support read from file 
				#CurrentUser.avatar=db.Blob(avatar_image)
				#CurrentUser.put()  	


				CurrentUser = tarsusaUser(user=users.get_current_user(), urlname=users.get_current_user().nickname())
				#self.write(CurrentUser.dispname)


				## Should automatically give the user a proper urlname
				## otherwise a lot of user's name will be their email address.
				## the email address's urlname will cause seriouse problems when 
				## the people are entering their own Mainpage or UserSetting page.
				CurrentUser.put()

				## Added userid property.
				CurrentUser.userid = CurrentUser.key().id()
				CurrentUser.dispname = users.get_current_user().nickname()
				CurrentUser.put()
			
			else:
				## DB Model Patch
				## These code for registered user whose information are not fitted into the new model setting.
				
				import DBPatcher
				
				## Added them here.
				if CurrentUser.userid == None:
					CurrentUser.userid = CurrentUser.key().id()
					CurrentUser.put()
					
				#Run DB Model Patch	when User Logged in.
				#DBPatcher.chk_dbmodel_update(CurrentUser)
				#Run this at every ViewItem event




			
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
				
				'UserNickName': cgi.escape(CurrentUser.dispname),
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

			template_values = {
				'UserNickName': "访客",
				'AnonymousVisitor': "Yes",
				'htmltag_TotalUser': TotalUserCount,
				'htmltag_TotaltarsusaItem': TotaltarsusaItem,
			}

			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/welcome.html')
			self.response.out.write(template.render(path, template_values))


class ViewItem(tarsusaRequestHandler):
	def get(self):
		#self.current_page = "home"
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

class UserToDoPage(tarsusaRequestHandler):
	def get(self):
		# Permission check is very important.
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()

			CountTotalItems = 0

			## SPEED KILLER!
			## MULTIPLE DB QUERIES!
			## CAUTION! MODIFY THESE LATER!
			tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC LIMIT 50", CurrentUser.user)

			CountTotalItems = tarsusaItemCollection_UserToDoItems.count()
			strTodoStatus = "共有" + str(CountTotalItems) + "个未完成项目"

			template_values = {
				'PrefixCSSdir': "/",
				'UserLoggedIn': 'Logged In',
				'UserNickName': cgi.escape(CurrentUser.dispname),
				'UserID': CurrentUser.key().id(),
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
				'TodoStatus': strTodoStatus,
				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
			}

			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/usertodopage.html')
			self.response.out.write(template.render(path, template_values))
		else:
			self.redirect('/')

class UserDonePage(tarsusaRequestHandler):
	def get(self):
		# Permission check is very important.
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()

			template_values = {
				'PrefixCSSdir': "/",

				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(CurrentUser.dispname),
				'UserID': CurrentUser.key().id(),
			}

			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/userdonepage.html')
			self.response.out.write(template.render(path, template_values))
		else:
			self.redirect('/')

class LoginPage(tarsusaRequestHandler):
	def get(self):
		#self.redirect(self.get_login_url(True))
		#Only / have user registration code right now, but here will lead user to different pages.
		# disabled these code temporily

		self.redirect(users.create_login_url('/'))


class SignOutPage(tarsusaRequestHandler):
	def get(self):
		self.redirect(self.get_logout_url(True))

class UserSettingPage(tarsusaRequestHandler):
	def get(self):
		userid = urllib.unquote(cgi.escape(self.request.path[6:-8])) ## Get the username in the middle of /user/1234/setting

		EditedUser = tarsusaUser.get_by_id(int(userid))
		CurrentUser = self.get_user_db()

		if EditedUser is not None and CurrentUser is not None:			
			
			if CurrentUser.key().id() == EditedUser.key().id():

				from google.appengine.ext.db import djangoforms
				from django import newforms as forms 
				
				class ItemForm(djangoforms.ModelForm):
					
					## Custom djangoforms.ModelForm,
					## http://groups.google.com/group/google-appengine/browse_thread/thread/d3673d0ec7ead0e2
					
					#category = forms.CharField(widget=forms.HiddenInput())
					#description =forms.CharField(widget=forms.Textarea(attrs={'rows':'10','cols':'70'})) 
					mail =	forms.CharField(label='您的邮箱(暂无法更改)',widget=forms.TextInput(attrs={'size':'30','maxlength':'30','value':EditedUser.user.email()})) 
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
					outputStringUserAvatarImage = "<img src=/img?img_user=" + str(EditedUser.key()) + " width=64 height=64><br />" + cgi.escape(EditedUser.dispname) + '&nbsp;<br />'
				else:
					outputStringUserAvatarImage = "<img src=/img/default_avatar.jpg width=64 height=64><br />" + cgi.escape(EditedUser.dispname) + '&nbsp;<br />'

				
				outputStringUserAvatarSetting += '''
							 <form method="post" enctype="multipart/form-data"> 
							 选择图像文件(<1M): <input type="file" name="avatar"/ size=15>
							 <input type="submit" value="更新头像"/></form> '''.decode('utf-8')



				template_values = {
						'PrefixCSSdir': "/",
						
						'UserLoggedIn': 'Logged In',

						'EditedUserNickName': EditedUser.dispname, 
						'UserNickName': CurrentUser.dispname, #used for base template. Actully right here, shoudl be the same.
						
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

				self.redirect("/user/" + str(CurrentUser.key().id()) + "/setting")


			else:  
				
				# code below are comming from GAE example
				q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
				CurrentUser = q.get()	
				
				CurrentUser.mail = mail
				CurrentUser.dispname = dispname
				CurrentUser.user.nickname = dispname
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

		username = urllib.unquote(cgi.escape(self.request.path[6:]))  ## Get the username in the URL string such as /user/1234
		ViewUser = None
		
		try:
			## After URL style changed, Now won't allow username in URL, only accept id in URL.
			
			## Get this user.
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE userid = :1 LIMIT 1", int(username))
			ViewUser = q.get()

			if ViewUser == None:
				q = tarsusaUser.get_by_id(int(username))
				ViewUser = q
		except:
			self.redirect('/')

		UserNickName = '访客'
		outputStringUserAvatar = ''

		if ViewUser != None:
		
			## Preparation
			## Will be useed
			if ViewUser.avatar:
				outputStringUserAvatar = "<img src='/img?img_user=" + str(ViewUser.key()) + "' width=64 height=64>"
			else:
				outputStringUserAvatar = "<img src='/img/default_avatar.jpg' width=64 height=64>"
				
			outputStringUserMainPageTitle = ViewUser.dispname + "公开的项目".decode("utf-8")

			outputStringRoutineLog = ""

			#-------------------------------------
			if users.get_current_user() == None:
				
				UserNickName = "访客"
				logictag_OneoftheFriendsViewThisPage = False
				CurrentUserIsOneofViewUsersFriends = False
				UserFriends = '请登录查看此用户的朋友信息'
				ViewedUserIsOneofCurrentUsersFriends = False

				#Check Whether there is usermainPage_publicitems_anony
				cachedUserMainPagePublicItemsAnony = memcache.get_item("mainpage_publicitems_anony", ViewUser.key().id())
				if cachedUserMainPagePublicItemsAnony is not None:
					outputStringRoutineLog = cachedUserMainPagePublicItemsAnony
				else:
					#no cache public_items_anony, get them
					tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC", ViewUser.user)
					# TODO
					#the code block below is a little bit duplicated, will find a way to make it simple in future. TODO
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


			else:				
				
				#Check Whether CurrerentUser is one of ViewUser's friends

				UserNickName = ViewUser.dispname
				
				CurrentUser = self.get_user_db()

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
			
				# Get user friend list
				cachedUserMainPageFriends = memcache.get_item("mainpage_friends", ViewUser.key().id())
				if cachedUserMainPageFriends is not None:
					UserFriends = cachedUserMainPageFriends
				else:
					# This is shown to all logged in users.
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

							#These code is here due to DB Model change since Rev.76
							try:								
								UserFriends += '<dd>' + cgi.escape(UsersFriend.dispname) + '</a></dd></dl>'
							except:
								UserFriends += '<dd>' + cgi.escape(UsersFriend.user.nickname()) + '</a></dd></dl>'
								
					else:
						UserFriends = '当前没有添加朋友'
					
					#set cache item
					memcache.set_item("mainpage_friends", UserFriends, ViewUser.key().id())
					


				#----------------------------------------				
				if ViewedUserIsOneofCurrentUsersFriends == True:
					#Check Whether there is usermainpage_publicitems
					cachedUserMainPagePublicItems = memcache.get_item("mainpage_publicitems", ViewUser.key().id())
					if cachedUserMainPagePublicItems is not None:
						outputStringRoutineLog = cachedUserMainPagePublicItems
					else:
						#no cache public items, get them
						#Show ViewUser's public items
						tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC", ViewUser.user)

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
						
						#set cache item
						memcache.set_item("mainpage_publicitems", outputStringRoutineLog, ViewUser.key().id())


				else:
					#CurrentUser is not one of ViewUser's friends.

					#Check Whether there is usermainPage_publicitems_anony
					cachedUserMainPagePublicItemsAnony = memcache.get_item("mainpage_publicitems_anony", ViewUser.key().id())
					if cachedUserMainPagePublicItemsAnony is not None:
						outputStringRoutineLog = cachedUserMainPagePublicItemsAnony
					else:
						#no cache public_items_anony, get them
						
						tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC", ViewUser.user)						
						#Show ViewUser's public items
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

						#set cache item
						memcache.set_item("mainpage_publicitems_anony", outputStringRoutineLog, ViewUser.key().id())

			if users.get_current_user() != None:
				template_values = {
					'PrefixCSSdir': "../",
					
					'UserLoggedIn': 'Logged In',

					'UserID': CurrentUser.key().id(), #This indicates the UserSettingPage Link on the topright of the Page, so it should be CurrentUser

					'ViewedUserNickName': UserNickName,
					'UserNickName': CurrentUser.dispname,
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
						
						'ViewedUserNickName': ViewUser.dispname,

						'UserAvatarImage': outputStringUserAvatar,
						
						'ViewedUserFriends': UserFriends,	
						'UserJoinInDate': datetime.datetime.date(ViewUser.datejoinin),
						'UserWebsite': ViewUser.website,
						'UserMainPageUserTitle': outputStringUserMainPageTitle,
						'StringRoutineLog': outputStringRoutineLog,
					}
			
				
			path = os.path.join(os.path.dirname(__file__), 'pages/usermainpage.html')
			
			self.response.out.write(template.render(path, template_values))

		else:
			#self.write('not found this user and any items')
			
			# Prompt 'Can not found this user, URL style have been changed since Dec.X 2008, Some of the old external links are invalid now.
			# But We offer you another options, You may check whether these Users, may be one of them is whom you are looking for.
			# Better UE idea!

			outputStringUserMainPageTitle = 'not found this user and any items'
			outputStringRoutineLog = 'None'
			self.error(404)
			self.redirect('/')	


class Image (webapp.RequestHandler):
	def get(self):
		#Add memcached here to improve the performence.
		usravatardata = memcache.get(self.request.get("img_user")[:250])
  		
		if usravatardata is not None:
			self.response.headers['Content-Type'] = "image/"
			self.response.out.write(usravatardata)
  		else:
			
			# Request it from BigTable
			greeting = db.get(self.request.get("img_user"))
			
			if greeting.avatar:
				self.response.headers['Content-Type'] = "image/"
				self.response.out.write(greeting.avatar)
				
				if not memcache.set(self.request.get("img_user")[:250], greeting.avatar, 7200):
					logging.error("Memcache set failed: When Loading avatar_image")
			else:
				self.error(404)

class DoneLogPage(tarsusaRequestHandler):
	def get(self):
		
		if not self.chk_login():
			self.redirect('/')

		## TODO added permission check, anonymous user should not see any private donelog 
		
		#Donelog should shows User's Done Routine Log
		
		#Donelog page shows User Done's Log.
		
		userid = urllib.unquote(cgi.escape(self.request.path[6:-8])) ## Get the username in the middle of /user/1234/donelog
		
		if userid == "": ## if the url are not directed to specific user.

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()

		else:
			CurrentUser = tarsusaUser.get_by_id(int(userid))
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
				'PrefixCSSdir': "/",
				
				'UserLoggedIn': 'Logged In',
				'UserID': CurrentUser.key().id(),
				'UserNickName': CurrentUser.dispname, 
				'singlePageTitle': "",
				
				'StringRoutineLog': outputStringRoutineLog,
		}

	
		path = os.path.join(os.path.dirname(__file__), 'pages/donelog.html')
		self.response.out.write(template.render(path, template_values))

class DashboardPage(tarsusaRequestHandler):
	def get(self):
		self.write('ok')
	
class NotFoundPage(tarsusaRequestHandler):
	def get(self):
		
		self.redirect('/page/404.html')

def main():
	application = webapp.WSGIApplication([('/', MainPage),
									   ('/i/\\d+',ViewItem),
								       ('/user/.+/donelog',DoneLogPage),
									   ('/user/.+/setting',UserSettingPage),
									   ('/user/.+/todo',UserToDoPage),
									   ('/user/.+/done',UserDonePage),
									   ('/user/.+', UserMainPage),
									   ('/img', Image),
									   ('/Login.+',LoginPage),
									   ('/Logout.+',SignOutPage),
									   ('/dashboard', DashboardPage),
									   ('.*',NotFoundPage)],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
