# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 0.7, codename Nevada
# - userpage.py
# Copyright (C) CNBorn, 2008
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn
#
#
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

from modules import *
from base import *
import logging

class DoneLogPage(tarsusaRequestHandler):
	def get(self):
		
		#Have to add this limit for GAE's CPU limitation.
		MaxDisplayedDonelogDays = 7
		DisplayedDonelogDays = 1 

		# New CheckLogin code built in tarsusaRequestHandler 
		if not self.chk_login():
			self.redirect('/')

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
			
			outputStringRoutineLog = "目前由于GAE的限制，只能显示7天内的完成记录<br />".decode('utf-8')
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


			template_values = {
					'PrefixCSSdir': "/",
					
					'UserLoggedIn': 'Logged In',
					'UserID': CurrentUser.key().id(),
					'UserNickName': cgi.escape(CurrentUser.dispname),
					'singlePageTitle': "",
					
					'StringRoutineLog': outputStringRoutineLog,
			}
		
			path = os.path.join(os.path.dirname(__file__), 'pages/donelog.html')
			strCachedDonelogPage = template.render(path, template_values)
			memcache.set_item("donelog", strCachedDonelogPage, CurrentUser.key().id())
		
		self.response.out.write(strCachedDonelogPage)

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

def main():
	application = webapp.WSGIApplication([
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
