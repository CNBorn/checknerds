# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename Nevada
# - userpage.py
# 
# Author: CNBorn
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn
#
#
# **************************************************************** 

import os

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

import PyRSS2Gen

from modules import *
from base import *
import logging

class DoneLogPage(tarsusaRequestHandler):
	def get(self):
	
		##TODO
		##CAUTION: OTHER PEOPLE WILL SEE THIS PAGE AND THERE IS NO CODE FOR PUBLIC CHECK.

		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():

			#Have to add this limit for GAE's CPU limitation.
			MaxDisplayedDonelogDays = 7
			DisplayedDonelogDays = 1 

			userid = urllib.unquote(cgi.escape(self.request.path[6:-8])) ## Get the username in the middle of /user/1234/donelog
			
			if userid == "": ## if the url are not directed to specific user.

				# New CheckLogin code built in tarsusaRequestHandler 
				if self.chk_login():
					CurrentUser = self.get_user_db()

			else:
				CurrentUser = tarsusaUser.get_by_id(int(userid))
				if CurrentUser == None:
					## Can not find this user.
					self.redirect("/")

			#Memcached Donelog page for better performance.
			IsCachedDonelogPage = memcache.get_item('donelog', CurrentUser.key().id())
			if IsCachedDonelogPage:
				strCachedDonelogPage = IsCachedDonelogPage
			else:
				tarsusaRoutineLogItemCollection = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 ORDER BY donedate DESC", CurrentUser.user)
				
				outputStringRoutineLog = "本页面只显示7天内的完成记录<br />".decode('utf-8')
				Donedate_of_previousRoutineLogItem = None  ## To display the routine item log by Daily.

				for each_RoutineLogItem in tarsusaRoutineLogItemCollection:
					
					DoneDateOfThisItem = datetime.datetime.date(each_RoutineLogItem.donedate)
					if DisplayedDonelogDays > MaxDisplayedDonelogDays:
						break

					if DoneDateOfThisItem != Donedate_of_previousRoutineLogItem:
						outputStringRoutineLog += ('<br /><h2 class="posttitle" style="font-weight:normal;">' + str(DoneDateOfThisItem) + '完成</h2><br />').decode('utf-8')
						DisplayedDonelogDays += 1
					
					## Get what the name of this RoutinetarsusaItem is.
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

					outputStringRoutineLog += ('<img src="/img/accept16.png">')
					outputStringRoutineLog += '<a href=/item/' + str(ThisRoutineBelongingstarsusaItem.key().id()) + '>' + ThisRoutineBelongingstarsusaItem.name + "</a> - <strong>" + (strRoutineLogItemPrompt + '任务</strong>').decode('utf-8') + "<br/>"

					
					#Show ordinary items that are created in that day
					TheDay = DoneDateOfThisItem
					one_day = datetime.timedelta(days=1)
					#yesterday_ofTheDay = TheDay - one_day						
					yesterday_ofTheDay = datetime.datetime.combine(TheDay - one_day,datetime.time(0))
					#nextday_ofTheDay = TheDay + one_day
					nextday_ofTheDay = datetime.datetime.combine(TheDay + one_day, datetime.time(0))

					tarsusaItemCollection_ThisDayCreated = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND donedate > :2 AND donedate <:3 AND done = True ORDER BY donedate DESC", CurrentUser.user, yesterday_ofTheDay, nextday_ofTheDay)
					for each_doneItem_withinOneday in tarsusaItemCollection_ThisDayCreated:
						outputStringRoutineLog += ('<img src="/img/accept16.png">').decode('utf-8')			
						outputStringRoutineLog += '<a href=/item/' + str(each_doneItem_withinOneday.key().id()) + '>' + each_doneItem_withinOneday.name + "</a><br/>"
					
					Donedate_of_previousRoutineLogItem = DoneDateOfThisItem 

				if self.chk_login(): #Trying to get the right id as CurrentLogin user 
									 #To render to link in donelog page correctly!
					CurrentLoginUser = self.get_user_db()

				template_values = {
						'PrefixCSSdir': "/",
						
						'UserLoggedIn': 'Logged In',
						'UserID': CurrentLoginUser.key().id(),
						'UserNickName': cgi.escape(CurrentLoginUser.dispname),
						'UserLoginNickName': cgi.escape(CurrentUser.dispname),
						'singlePageTitle': "",
						
						'StringRoutineLog': outputStringRoutineLog,
				}
			
				path = os.path.join(os.path.dirname(__file__), 'pages/donelog.html')
				strCachedDonelogPage = template.render(path, template_values)
				memcache.set_item("donelog", strCachedDonelogPage, CurrentUser.key().id())
			
			self.response.out.write(strCachedDonelogPage)
		
		else:
			self.redirect("/")

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

class UserDoneLogPage(tarsusaRequestHandler):
	def get(self):
		
		# Permission check is very important.
		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()

			#self.write(tarsusaCore.get_UserDonelog(CurrentUser.key().id()))
			try:
				pageid = self.request.path[len('/donelog/'):]
				if pageid[:2] == 'p/':
					tag_ViewPreviousPage = True
					pageid = pageid[2:]
				else:
					tag_ViewPreviousPage = False
			except:
				pass

			if pageid != None and len(self.request.path) > len('/donelog/'):
				this_timestamp = datetime.datetime.fromtimestamp(int(pageid))
				if tag_ViewPreviousPage == True:
					##the defination of 'previous' and 'next' here is different as other pages.
					
					tarsusaItemCollection = tarsusaCore.get_UserDonelog(CurrentUser.key().id(), this_timestamp, 'next')
					#tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True and donedate > :2 ORDER BY donedate DESC LIMIT 9", CurrentUser.user, this_timestamp)

				else:
					tarsusaItemCollection = tarsusaCore.get_UserDonelog(CurrentUser.key().id(), this_timestamp, 'previous')
					#tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True and donedate <= :2 ORDER BY donedate DESC LIMIT 9", CurrentUser.user, this_timestamp)

			#Memcached Donelog page for better performance.
			#IsCachedDonelogPage = memcache.get_item('userdonelog', CurrentUser.key().id())
			#if IsCachedDonelogPage:
			#	strCachedDonelogPage = IsCachedDonelogPage
			#else:
				
			else:
				tarsusaItemCollection = tarsusaCore.get_UserDonelog(CurrentUser.key().id())
				#returned as dictionary, please refer to tarsusaCore.py

			outputStringRoutineLog = '' #"本页面只显示7天内的完成记录<br />".decode('utf-8')
			Donedate_of_previousRoutineLogItem = None  ## To display the routine item log by Daily.
			DaysInDonelog = 0 #How many days are scaled in all data collection.

			for each_Item in tarsusaItemCollection:
				
				DoneDateOfThisItem = datetime.datetime.date(each_Item['donedate'])

				if DoneDateOfThisItem != Donedate_of_previousRoutineLogItem:
					DaysInDonelog += 1
					outputStringRoutineLog += ('<br /><h2 class="posttitle" style="font-weight:normal;">' + str(DoneDateOfThisItem) + '完成</h2><br />').decode('utf-8')
				
				if each_Item['routine'] != 'none':
					#FOR DONE_ROUTINE item.
					strRoutineLogItemPrompt = ''
					if each_Item['routine'] == 'daily':
						strRoutineLogItemPrompt = '每日'
					elif each_Item['routine'] == 'weekly':
						strRoutineLogItemPrompt = '每周'
					elif each_Item['routine'] == 'monthly':
						strRoutineLogItemPrompt = '每月'
					elif each_Item['routine'] == 'seasonly':
						strRoutineLogItemPrompt = '每季'
					elif each_Item['routine'] == 'yearly':
						strRoutineLogItemPrompt = '每年'

					outputStringRoutineLog += ('&nbsp;&nbsp;<img src="/img/accept16.png">')
					outputStringRoutineLog += '<a href=/item/' + str(each_Item['id']) + '>' + each_Item['name'] + "</a> - <strong>" + (strRoutineLogItemPrompt + '任务</strong>').decode('utf-8') + "<br/>"
					
				else:
					#FOR ORDINARY DONE ITEM
					outputStringRoutineLog += ('&nbsp;&nbsp;<img src="/img/accept16.png">').decode('utf-8')			
					outputStringRoutineLog += '<a href=/item/' + str(each_Item['id']) + '>' + each_Item['name'] + "</a><br/>"
					
				Donedate_of_previousRoutineLogItem = DoneDateOfThisItem 

			
			
			

				
			template_values = {
					'PrefixCSSdir': "/",
					
					'UserLoggedIn': 'Logged In',
					'UserID': CurrentUser.key().id(),
					'UserNickName': cgi.escape(CurrentUser.dispname),
					'UserLoginNickName': cgi.escape(CurrentUser.dispname),
					'singlePageTitle': "",
					
					'StringRoutineLog': outputStringRoutineLog,
			}
			
			#Determine next page
			#if there is an error here, there would be not found any records.
			try:
				previous_timestamp = int(time.mktime(tarsusaItemCollection[0]['donedate'].timetuple()))
				next_timestamp = int(time.mktime(tarsusaItemCollection[len(tarsusaItemCollection) - 1]['donedate'].timetuple()))
				if previous_timestamp != 0:
					template_values['previouspagestamp'] = previous_timestamp		
				if next_timestamp != 0:
					template_values['nextpagestamp'] = next_timestamp			
				if next_timestamp == 0 and previous_timestamp == 0:
					self.redirect("/donelog/")			
				#to be improved, if all these records are created in the same day
				if DaysInDonelog == 1 and tag_ViewPreviousPage == True:
					self.redirect("/donelog/")				
			except:
				self.redirect('/donelog/')
	
			path = os.path.join(os.path.dirname(__file__), 'pages/donelog.html')
			strCachedDonelogPage = template.render(path, template_values)
			#memcache.set_item("userdonelog", strCachedDonelogPage, CurrentUser.key().id())
			self.response.out.write(strCachedDonelogPage)
		else:
			self.redirect('/')

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
					
					mail =	forms.CharField(label='您的邮箱(不会公开，无法更改)',widget=forms.TextInput(attrs={'readonly':'','size':'30','maxlength':'30','value':EditedUser.user.email()})) 
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
					outputStringUserAvatarImage = "<img src=/img?avatar=" + str(EditedUser.key().id()) + " width=64 height=64><br />" + cgi.escape(EditedUser.dispname) + '&nbsp;<br />'
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
				
				# New CheckLogin code built in tarsusaRequestHandler 
				if self.chk_login():
					CurrentUser = self.get_user_db()

				avatar_image = images.resize(avatar,128,128)

				CurrentUser.avatar=db.Blob(avatar_image)
				CurrentUser.put()  
				
				if not memcache.set('img_useravatar' + str(CurrentUser.key().id()), db.Blob(avatar_image), 7200):
					logging.error("Memcache set failed: When uploading avatar_image")

				self.redirect("/user/" + str(CurrentUser.key().id()) + "/setting")


			else:  
				
				# New CheckLogin code built in tarsusaRequestHandler 
				if self.chk_login():
					CurrentUser = self.get_user_db()
				
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
							
								# New CheckLogin code built in tarsusaRequestHandler 
								if self.chk_login():
									CurrentUser = self.get_user_db()
					
								
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
						if not memcache.set('img_useravatar' + str(CurrentUser.key().id()), db.Blob(avatar_image), 7200):
							logging.error("Memcache set failed: When uploading(2) avatar_image")

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
				outputStringUserAvatar = "<img src='/img?avatar=" + str(ViewUser.key().id()) + "' width=64 height=64>"
			else:
				outputStringUserAvatar = "<img src='/img/default_avatar.jpg' width=64 height=64>"
				
			outputStringUserMainPageTitle = ViewUser.dispname + "公开的项目".decode("utf-8")

			outputStringRoutineLog = ""

			#-------------------------------------
			if not self.chk_login():
			#if users.get_current_user() == None:
				
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
							outputStringRoutineLog += '<a href="/item/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
						elif each_Item.public == 'public':
							if each_Item.done == True:
								outputStringRoutineLog += "<img src='/img/accept16.png'>" 
							outputStringRoutineLog += '<a href="/item/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
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
								UserFriends += '<dl class="obu2"><dt>' + '<a href="/user/' + cgi.escape(str(UsersFriend.key().id())) +  '">' + "<img src=/img?avatar=" + str(UsersFriend.key().id()) + " width=32 height=32>" + '</dt>'
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
								outputStringRoutineLog += '<a href="/item/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
							elif each_Item.public == 'public':
								if each_Item.done == True:
									outputStringRoutineLog += "<img src='/img/accept16.png'>" 
								outputStringRoutineLog += '<a href="/item/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
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
								outputStringRoutineLog += '<a href="/item/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
							elif each_Item.public == 'public':
								if each_Item.done == True:
									outputStringRoutineLog += "<img src='/img/accept16.png'>" 
								outputStringRoutineLog += '<a href="/item/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
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

					'outputFeed': True,
					'outputFeedTitle': ViewUser.dispname,
					'outputFeedURL': "/user/" + str(ViewUser.key().id()) + "/feed",
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
						
						'outputFeed': True,
						'outputFeedTitle': ViewUser.dispname,
						'outputFeedURL': "/user/" + str(ViewUser.key().id()) + "/feed",
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

class UserFeedPage(tarsusaRequestHandler):
	def get(self):
		
		#RSS Feed Code, leart from Plog, using PyRSS2Gen Module.

		username = urllib.unquote(cgi.escape(self.request.path[6:-5]))  ## Get the username in the URL string such as /user/1234/feed
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
		
			userfeed_publicitems = []
			
			#There is a force 15 limits for RSS feed.
			#Plog is setting this as an option in setting.
			tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and public = 'public' ORDER BY date DESC LIMIT 15", ViewUser.user)
			#the code block below is a little bit duplicated, will find a way to make it simple in future. TODO
			for each_Item in tarsusaItemCollection_UserRecentPublicItems:
				
				try:
					# some very old items may not have usermodel property 
					str_author = each_Item.usermodel.dispname
				except:
					str_author = each_Item.user.nickname()

				if each_Item.done == True:
					str_title = ViewUser.dispname + " 完成了 ".decode('utf-8') + each_Item.name
				else:
					str_title = ViewUser.dispname + " 要做 ".decode('utf-8') + each_Item.name
								
				item_url = '%s/item/%d' % (self.request.host_url, each_Item.key().id())

				userfeed_publicitems.append(PyRSS2Gen.RSSItem(
					title = str_title,
					author = str_author,
					link = item_url,
					description = each_Item.comment,
					pubDate = each_Item.date,
					guid = PyRSS2Gen.Guid(item_url)
					#categories
					)
				)
			rss = PyRSS2Gen.RSS2(
				title = "CheckNerds - " + ViewUser.dispname,
				link = self.request.host_url + '/user/' + str(ViewUser.key().id()),
				description = ViewUser.dispname + '最新的15条公开事项，在线个人事项管理——欢迎访问http://www.checknerds.com'.decode('utf-8'),
				lastBuildDate = datetime.datetime.utcnow(),
				items = userfeed_publicitems
				)

			self.response.headers['Content-Type'] = 'application/rss+xml; charset=utf-8'
			rss_xml = rss.to_xml(encoding='utf-8')
			self.write(rss_xml)


def main():
	application = webapp.WSGIApplication([
									   ('/user/.+/feed',UserFeedPage),
								       ('/user/.+/donelog',DoneLogPage),
									   ('/user/.+/setting',UserSettingPage),
									   ('/user/.+/todo',UserToDoPage),
									   ('/user/.+/done',UserDonePage),
									   ('/user/.+', UserMainPage),
									   ],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
