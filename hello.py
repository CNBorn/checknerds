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


class MainPage(tarsusaRequestHandler):
	def get(self):
		
		#if self.chk_login() == True:
		if users.get_current_user() != None:

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()
			
			if not CurrentUser:
				# Create a User
				# Actully I thought this would be useless when I have an signin page.
				
				#Give vreated user a default avatar image.
				#avatar_image = images.resize('/img/default_avatar.jpg',64,64)
				#do not support read from file 
				#CurrentUser.avatar=db.Blob(avatar_image)
				#CurrentUser.put()  	


				CurrentUser = tarsusaUser(user=users.get_current_user(), urlname=users.get_current_user().nickname())
				#self.write(CurrentUser.user.nickname())


				## Should automatically give the user a proper urlname
				## otherwise a lot of user's name will be their email address.
				## the email address's urlname will cause seriouse problems when 
				## the people are entering their own Mainpage or UserSetting page.
				CurrentUser.put()

				## Added userid property.
				CurrentUser.userid = CurrentUser.key().id()
				CurrentUser.dispname = CurrentUser.user.nickname()
				CurrentUser.put()
			
			else:
				## These code for registered user whose information are not fitted into the new model setting.
				## Added them here.
				if CurrentUser.userid == None:
					CurrentUser.userid = CurrentUser.key().id()


			
			## Check usedtags as the evaluation for Tags Model
			## TEMP CODE!
			UserTags = '<a href=/tag/>Untagged Items</a>&nbsp;'
			if CurrentUser.usedtags:
				for each_cate in CurrentUser.usedtags:
					## After adding code with avoiding add duplicated tag model, it runs error on live since there are some items are depending on the duplicated ones.
					try:
						each_tag =  db.get(each_cate)
						UserTags += '<a href=/tag/' + cgi.escape(each_tag.name) +  '>' + cgi.escape(each_tag.name) + '</a>&nbsp;'
			
					except:
						pass


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



			## SPEED KILLER!
			## MULTIPLE DB QUERIES!
			## CAUTION! MODIFY THESE LATER!
			tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC LIMIT 5", users.get_current_user())
			tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True ORDER BY date DESC LIMIT 5", users.get_current_user())


			## SHOW YOUR FRIENDs Recent Activities
			## Currently the IN function is not supported, it is an headache.
			
			## first get current user. 
			## THIS LINES OF CODE ARE DUPLICATED.
			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()

			tarsusaUserFriendCollection = CurrentUser.friends
			
			tarsusaItemCollection_UserFriendsRecentItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC LIMIT 15", users.get_current_user)


			UserFriendsActivities = ''
			if tarsusaUserFriendCollection: 
				for each_FriendKey in tarsusaUserFriendCollection:
					UsersFriend =  db.get(each_FriendKey)
					## THE BELOW LINE IS UN SUPPORTED!
					#tarsusaItemCollection_UserFriendsRecentItems += db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC LIMIT 15", UsersFriend)
					## THERE are too many limits in GAE now...
					tarsusaItemCollection_UserFriendsRecentItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC LIMIT 2", UsersFriend.user)

					for tarsusaItem_UserFriendsRecentItems in tarsusaItemCollection_UserFriendsRecentItems:
						## Check whether should show this item.
						if tarsusaItem_UserFriendsRecentItems.public != 'private':
						
							## Check whether this item had done.
							if tarsusaItem_UserFriendsRecentItems.done == True:
								
								UserFriendsActivities += '<a href="/user/' + UsersFriend.user.nickname() + '">' +  UsersFriend.user.nickname() + '</a> Done <a href="/i/' + tarsusaItem_UserFriendsRecentItems.key().id() + '">' + tarsusaItem_UserFriendsRecentItems.name + '</a><br />'
	 
							else:
								UserFriendsActivities += '<a href="/user/' + UsersFriend.user.nickname() + u'">' + UsersFriend.user.nickname() + '</a> ToDO <a href="/i/' + str(tarsusaItem_UserFriendsRecentItems.key().id()) + '">' + tarsusaItem_UserFriendsRecentItems.name + '</a><br />'


			else:
				UserFriendsActivities = '当前没有添加朋友'

								

			template_values = {
				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(self.login_user.nickname()),
				'UserID': CurrentUser.key().id(),
				
				'tarsusaItemCollection_DailyRoutine': tarsusaItemCollection_DailyRoutine,
				'htmltag_DoneAllDailyRoutine': template_tag_donealldailyroutine,

				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 

				'UserTags': UserTags,

				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
				'tarsusaItemCollection_UserDoneItems': tarsusaItemCollection_UserDoneItems,


				'UserFriendsActivities': UserFriendsActivities,

				'UserTotalItems': UserTotalItems,
				'UserToDoItems': UserToDoItems,
				'UserDoneItems': UserDoneItems,
				'UserDonePercentage': UserDonePercentage,
			}


			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'index.html')
			self.response.out.write(template.render(path, template_values))
			
		else:
			
			## Homepage for Non-Registered Users.

			## the not equal != is not supported!
			tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE public = 'public' and routine = 'none' ORDER BY date DESC")

			tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE public = 'public' and routine = 'none' and done = True ORDER BY date DESC")
			
			
			
			
			
			
			
			
			
			template_values = {
				
				'UserNickName': "访客",
				'AnonymousVisitor': "Yes",
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
				'tarsusaItemCollection_UserDoneItems': tarsusaItemCollection_UserDoneItems,

			}


			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'index.html')
			self.response.out.write(template.render(path, template_values))



class AddPage(tarsusaRequestHandler):
	def get(self):
		
		# "this is add page"
		user = users.get_current_user()	

		## TODO
		## An Brainstorming Idea - Made this additem as AJAX!

		
		if user:
	
			html_tag_AddItemForm_OrdinaryForms = '''<form action="/additem" method="post">
									标题  <input type="text" name="name" value="" size="40" class="sl"><br />
									内容  <textarea name="comment" rows="5" cols="28" wrap="PHYSICAL" class="ml"></textarea><br />
									类别  <input type="text" name="tags" size="40" class="sl"><br />
									预计完成于<br />'''

			html_tag_AddItemForm_RoutineForms = '''性质：<select name="routine">
									<option value="none" selected="selected">非坚持性任务</option>
									<option value="daily">每天</option>
									<option value="weekly">每周</option>
									<option value="monthly">每月</option>
									<option value="seasonly">每季度</option>
									<option value="yearly">每年</option>
									</select><br>'''
	
			## TODO 
			## Added proper calendar date select form
			## Tested django form, it doesnt contain that

			html_tag_AddItemForm_PublicForms = '''公开项目：<select name="public"><option value="private" selected="selected">不公开</option>
			<option value="public">公开</option>
			<option value="publicOnlyforFriends">仅对朋友公开</option>
			'''


			html_tag_AddItemForm_SubmitForm = '''<input type="submit" name="submit" value="添加一个任务"></form>'''


			template_values = {
				
			'UserLoggedIn': 'Logged In',
			'UserNickName': cgi.escape(self.login_user.nickname()),

			'OrdinaryForms': html_tag_AddItemForm_OrdinaryForms,
			'RoutineForms': html_tag_AddItemForm_RoutineForms,
			'PublicForms': html_tag_AddItemForm_PublicForms,
			'SubmitForm': html_tag_AddItemForm_SubmitForm,

			}


			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/additem.html')
			self.response.out.write(template.render(path, template_values))

		else:
			
			## self.write ("Your are not logged in!")

			## Prompt a message that ask the user to login.
			## Or, the guest user will not be given with this url's direct visit?
			
			## redirect them to the rootpage.
			self.redirect("/")



class AddItemProcess(tarsusaRequestHandler):
	def post(self):
		
		if self.request.get('cancel') != "取消":
			
			first_tarsusa_item = tarsusaItem(user=users.get_current_user(),name=cgi.escape(self.request.get('name')), comment=cgi.escape(self.request.get('comment')),routine=cgi.escape(self.request.get('routine')))
			
			# for changed tags from String to List:
			#first_tarsusa_item.tags = cgi.escape(self.request.get('tags')).split(",")
			tarsusaItem_Tags = cgi.escape(self.request.get('tags')).split(",")
			
			## TODO
			## If user defines tag is None, Add '为分类项目' in Database?
			## Or Just display it with Database Logical?
			

			first_tarsusa_item.public = self.request.get('public')

			first_tarsusa_item.done = False

			## the creation date will be added automatically by GAE datastore
			first_tarsusa_item.put()
			
			# http://blog.ericsk.org/archives/1009
			# This part of tag process inspired by ericsk.
			# many to many

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()
		
			for each_tag_in_tarsusaitem in tarsusaItem_Tags:
				
				#each_cat = Tag(name=each_tag_in_tarsusaitem)
				#each_cat.count += 1
				#each_cat.put()
				
				## It seems that these code above will create duplicated tag model.
				catlist = db.GqlQuery("SELECT * FROM Tag WHERE name = :1 LIMIT 1", each_tag_in_tarsusaitem)
				try:
					each_cat = catlist[0]
				
				except:
					each_cat = Tag(name=each_tag_in_tarsusaitem)
					each_cat.put()

				first_tarsusa_item.tags.append(each_cat.key())
				# To Check whether this user is using this tag before.
				for check_whether_used_tag in CurrentUser.usedtags:
					tag_AlreadyUsed = False
					if each_cat.key() == check_whether_used_tag:
						tag_AlreadyUsed = True
					
				if tag_AlreadyUsed == False:
					CurrentUser.usedtags.append(each_cat.key())		

			first_tarsusa_item.put()
			CurrentUser.put()



			#UserTags = ''
			#for each_cate in CurrentUser.usedtags:
			#	each_tag =  db.get(each_cate)
			#	UserTags += '<a href=/tag/' + cgi.escape(each_tag.name) +  '>' + cgi.escape(each_tag.name) + '</a>&nbsp;'

			#self.write(UserTags)

			
			## After adding ajax,
			## it should help to close the ajax box. //done, i just remove the &modar=true
			## and ajax reload the routine and bottom-contents
			
			#self.redirect('/')
			self.write('''

	<script type="text/javascript">
									self.parent.tb_remove();
									self.parent.$('#featuredcode-mid').animate({height: 'hide', opacity: 'hide'}, 'slow', function(){
												 	self.parent.$('#featuredcode-mid').load('/ajax/frontpage_getdailyroutine', {nullid: Math.round(Math.random()*1000)}, function(){
												   	self.parent.$('#featuredcode-mid').animate({height: 'show', opacity: 'show'}, 'slow');
												   													 });
																		 });
																									
										self.parent.$('#latestcodes').load('/ajax/frontpage_bottomcontents');									
									}
																									
									</script>



			''')


class ViewItem(tarsusaRequestHandler):
	def get(self):
		#self.current_page = "home"
		postid = self.request.path[3:]
		tItem = tarsusaItem.get_by_id(int(postid))

		if tItem != None:  ## If this Item existed in Database.

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


			# for modified Tags (db.key)
			ItemTags = ''
			for each_tag in db.get(tItem.tags):
				ItemTags += '<a href=/tag/' + cgi.escape(each_tag.name) +  '>' + cgi.escape(each_tag.name) + '</a>&nbsp;'
			

			logictag_OtherpeopleViewThisItem = None
			if tItem.user != users.get_current_user():
				
				if tItem.public == 'publicOnlyforFriends':
					## Check if the viewing user is a friend of the ItemAuthor.
				
					# code below are comming from GAE example
					q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
					CurrentUser = q.get()
					# code below are comming from GAE example
					q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", tItem.user)
					ItemAuthorUser = q.get()

					CurrentUserIsOneofAuthorsFriends = False

					for each_Friend_key in ItemAuthorUser.friends:
						if each_Friend_key == CurrentUser.key():
							CurrentUserIsOneofAuthorsFriends = True

					logictag_OtherpeopleViewThisItem = True

				elif tItem.public == 'public':
					logictag_OtherpeopleViewThisItem = True
					

				else:
					self.redirect('/')
			else:
				## Viewing User is the Owner of this Item.
				UserNickName = users.get_current_user().nickname()

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
				UserNickName = users.get_current_user().nickname()
				## or dispname?

				template_values = {
						'PrefixCSSdir': "../",
						'UserLoggedIn': 'Logged In',

						'UserNickName': UserNickName, 
						'singlePageTitle': "View Item",
						'singlePageContent': "",

						'logictag_OtherpeopleViewThisItem': logictag_OtherpeopleViewThisItem,


						'tarsusaItem': tItem,
						'tarsusaItemDone': tItem.done,
						'tarsusaItemTags': ItemTags,
						'tarsusaRoutineItem': html_tag_tarsusaRoutineItem,
						'tarsusaRoutineLogItem': tarsusaItemCollection_DoneDailyRoutine,
				}

			else:
						template_values = {
						'PrefixCSSdir': "../",
						'singlePageTitle': "View Item",
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


class DoneItem(tarsusaRequestHandler):
	def get(self):
		ItemId = self.request.path[10:]
		tItem = tarsusaItem.get_by_id(int(ItemId))

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
				#NewlyDoneRoutineItem.routine = tItem.routine
				# The done date will be automatically added by GAE datastore.			
				NewlyDoneRoutineItem.put()

		

		#self.redirect(self.request.uri)
		self.redirect('/')


class UnDoneItem(tarsusaRequestHandler):
	def get(self):

		# Permission check is very important.

		ItemId = self.request.path[12:]
		## Please be awared that ItemId here is a string!
		tItem = tarsusaItem.get_by_id(int(ItemId))


		if tItem.user == users.get_current_user():
			## Check User Permission to done this Item

			if tItem.routine == 'none':
				## if this item is not a routine item.
				tItem.donedate = ""
				tItem.done = False

				tItem.put()
			else:
				if tItem.routine == 'daily':
					del tItem.donetoday
					tItem.put()
					## Please Do not forget to .put()!

					## This is a daily routine, and we are going to undone it.
					## For DailyRoutine, now I just count the matter of deleting today's record.
					## the code for handling the whole deleting routine( delete all concerning routine log ) will be added in future
					
					# GAE can not make dateProperty as query now! There is a BUG for GAE!
					# http://blog.csdn.net/kernelspirit/archive/2008/07/17/2668223.aspx
					tarsusaRoutineLogItemCollection_ToBeDeleted = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate < :2", int(ItemId), datetime.datetime.now())
					for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
						result.delete()



		#self.redirect('/')

class RemoveItem(tarsusaRequestHandler):
	def get(self):
		#self.write('this is remove page')

		# Permission check is very important.

		ItemId = self.request.path[12:]
		## Please be awared that ItemId here is a string!
		tItem = tarsusaItem.get_by_id(int(ItemId))


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

		self.redirect('/')

class UserToDoPage(tarsusaRequestHandler):
	def get(self):
		
		if users.get_current_user() != None:

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()	

			## SPEED KILLER!
			## MULTIPLE DB QUERIES!
			## CAUTION! MODIFY THESE LATER!
			tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC LIMIT 50", users.get_current_user())


			template_values = {
				'PrefixCSSdir': "/",

				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(self.login_user.nickname()),
				'UserID': CurrentUser.key().id(),
				
				#'tarsusaItemCollection_DailyRoutine': tarsusaItemCollection_DailyRoutine,
				#'htmltag_DoneAllDailyRoutine': template_tag_donealldailyroutine,

				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 

				#'UserTags': UserTags,

				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,



				#'UserTotalItems': UserTotalItems,
				#'UserToDoItems': UserToDoItems,
				#'UserDoneItems': UserDoneItems,
				#'UserDonePercentage': UserDonePercentage,
			}


			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/usertodopage.html')
			self.response.out.write(template.render(path, template_values))




class UserDonePage(tarsusaRequestHandler):
	def get(self):
		if users.get_current_user() != None:

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()	

			## SPEED KILLER!
			## MULTIPLE DB QUERIES!
			## CAUTION! MODIFY THESE LATER!
			tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True ORDER BY date DESC LIMIT 50", users.get_current_user())


			template_values = {
				'PrefixCSSdir': "/",

				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(self.login_user.nickname()),
				'UserID': CurrentUser.key().id(),
				
				#'tarsusaItemCollection_DailyRoutine': tarsusaItemCollection_DailyRoutine,
				#'htmltag_DoneAllDailyRoutine': template_tag_donealldailyroutine,

				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 

				#'UserTags': UserTags,

				'tarsusaItemCollection_UserDoneItems': tarsusaItemCollection_UserDoneItems,



				#'UserTotalItems': UserTotalItems,
				#'UserToDoItems': UserToDoItems,
				#'UserDoneItems': UserDoneItems,
				#'UserDonePercentage': UserDonePercentage,
			}


			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/userdonepage.html')
			self.response.out.write(template.render(path, template_values))






class Showtag(tarsusaRequestHandler):
	def get(self):
		#each_cat = Tag(name=cgi.escape(self.request.path[5:]))
		catlist = db.GqlQuery("SELECT * FROM Tag WHERE name = :1 LIMIT 1", unicode(self.request.path[5:]))
		
		if self.request.path[5:] <> '':
			
			try:

				each_cat = catlist[0]

				#self.write(each_cat.count)
				
				html_tag_DeleteThisTag = '<a href="/deleteTag/"' + str(each_cat.key().id()) + '>X</a>'
				## NOTICE that the /deleteTag should del the usertags in User model.

				#browser_Items = tarsusaItem(user=users.get_current_user(), routine="none")
				browser_Items = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC LIMIT 100", users.get_current_user())

				html_tag_ItemList = ""
				for eachItem in browser_Items:
					for eachTag in eachItem.tags:
						if db.get(eachTag).name == self.request.path[5:]:
							#self.write(eachItem.name)
							#html_tag_ItemList += eachItem.name + "<br />"
							html_tag_ItemList += '<a href=/i/' + str(eachItem.key().id()) + '>' + cgi.escape(eachItem.name) + "</a><br/>"

				template_values = {
						'PrefixCSSdir': "/",
						
						'UserLoggedIn': 'Logged In',

						'UserNickName': users.get_current_user().nickname(),
						'DeleteThisTag': html_tag_DeleteThisTag,
						'TagName': each_cat.name,
						'ItemList': html_tag_ItemList,


				}

			
				path = os.path.join(os.path.dirname(__file__), 'pages/viewtag.html')
				self.response.out.write(template.render(path, template_values))

			except:
				## There is no this tag!
				self.redirect("/")


		else:
			
			if self.request.path[5:] == '':
				## Show Items with no tag.

				#browser_Items = tarsusaItem(user=users.get_current_user(), routine="none")
				browser_Items = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC LIMIT 100", users.get_current_user())

				html_tag_DeleteThisTag = '无标签项目'

				html_tag_ItemList = ""
				for eachItem in browser_Items:
					if len(eachItem.tags) == 0:
							html_tag_ItemList += '<a href=/i/' + str(eachItem.key().id()) + '>' + cgi.escape(eachItem.name) + "</a><br/>"

				template_values = {
						'PrefixCSSdir': "/",
						
						'UserLoggedIn': 'Logged In',

						'UserNickName': users.get_current_user().nickname(),
						'DeleteThisTag': html_tag_DeleteThisTag,
						'TagName': "未分类项目",
						'ItemList': html_tag_ItemList,
				}
				
				path = os.path.join(os.path.dirname(__file__), 'pages/viewtag.html')
				self.response.out.write(template.render(path, template_values))

			else:
				## There is no this tag!
				self.redirect("/")



class LoginPage(tarsusaRequestHandler):
	def get(self):
		# if seems that self.chk_login can not determine the right status
		
		#if self.chk_login == False:		
			self.redirect(users.create_login_url('/'))

class SignInPage(webapp.RequestHandler):
	def get(self):
		print "this is signinpage"

class SignOutPage(tarsusaRequestHandler):
	def get(self):
		self.redirect(users.create_logout_url('/'))


class UserSettingPage(tarsusaRequestHandler):
	def get(self):
		
		username = cgi.escape(self.request.path[6:-8])  ## Get the username in the middle of /user/CNBorn/setting

		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE urlname = :1", username)
		CurrentUser = q.get()

		if CurrentUser == None:
			## try another way
			## Get this user.
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE userid = :1 LIMIT 1", int(username))
			CurrentUser = q.get()
		
		if CurrentUser == None:
			## try another way
			## Get this user.
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE dispname = :1 LIMIT 1", username)
			CurrentUser = q.get()



		if CurrentUser != None:

			from google.appengine.ext.db import djangoforms
			from django import newforms as forms 
			
			class ItemForm(djangoforms.ModelForm):
				
				## Custom djangoforms.ModelForm,
				## http://groups.google.com/group/google-appengine/browse_thread/thread/d3673d0ec7ead0e2
				
				#category = forms.CharField(widget=forms.HiddenInput())
				#description =	forms.CharField(widget=forms.Textarea(attrs={'rows':'10','cols':'70'})) 
				mail = 	forms.CharField(widget=forms.TextInput(attrs={'size':'10','maxlength':'10','value':CurrentUser.user.email()}))
				urlname =forms.CharField(widget=forms.TextInput(attrs={'size':'10','maxlength':'10','value':CurrentUser.urlname}))
				dispname = forms.CharField(widget=forms.TextInput(attrs={'size':'10','maxlength':'10','value':CurrentUser.dispname}))
				website = forms.CharField(widget=forms.TextInput(attrs={'size':'10','maxlength':'10','value':CurrentUser.website}))	
				##Please reference more from the URL

				class Meta:
					model = tarsusaUser
					exclude =['user','userid','usedtags','friends','datejoinin']


			
			outputStringUserSettingForms = ItemForm()

			

			## The Avatar part is inspired by 
			## http://blog.liangent.cn/2008/07/google-app-engine_28.html

		

			outputStringUserAvatarSetting = ""
			
			if CurrentUser.avatar:
				outputStringUserAvatarSetting += "<img src=/img?img_user=" + str(CurrentUser.key()) + " width=64 height=64><br />" + cgi.escape(CurrentUser.user.nickname()) + '&nbsp;<br />'
			else:
				outputStringUserAvatarSetting += "<img src=/img/default_avatar.jpg width=64 height=64><br />" + cgi.escape(CurrentUser.user.nickname()) + '&nbsp;<br />'

			
			outputStringUserAvatarSetting += '''
						 <form method="post" enctype="multipart/form-data"> 
						 choose file: <input type="file" name="avatar"/>
						 <input type="submit" value="Update Avatar"/></form> '''





			template_values = {
					'PrefixCSSdir': "/",
					
					'UserLoggedIn': 'Logged In',

					'UserNickName': CurrentUser.user.nickname(),
					'UserID': CurrentUser.key().id(),
					'UserJoinInDate': CurrentUser.datejoinin,

					'UserSettingForms': outputStringUserSettingForms,

					'UserAvatarSetting': outputStringUserAvatarSetting,


					
			}

		
			path = os.path.join(os.path.dirname(__file__), 'pages/usersettingpage.html')
			self.response.out.write(template.render(path, template_values))

		else:
			## can not find this user.
			self.redirect("/")


	def post(self):  
		
		#checkauth(self)  
		
		url_mime = 'image/' 
		avatar = self.request.get('avatar')  
		
		if url_mime:  
			if avatar:
				
				# code below are comming from GAE example
				q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
				CurrentUser = q.get()

				avatar_image = images.resize(avatar,128,128)

				CurrentUser.avatar=db.Blob(avatar_image)
				CurrentUser.put()  

				self.redirect("/user/" + CurrentUser.user.nickname() + "/setting")


			else:  
				
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
					avatar = Avatar(url_mime=url_mime)  
					avatar.put()  
					#sendmsg(self, 'added')  
		else:
			 #sendmsg(self, 'fill in the form!')  
			 self.write('please write')


class UserMainPage(tarsusaRequestHandler):
	def get(self):

		username = cgi.escape(self.request.path[6:])  ## Get the username in the middle of /user/CNBorn/

		## Get this user.
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE urlname = :1 LIMIT 1", username)
		ViewUser = q.get()

		if ViewUser == None:
			## try another way
			## Get this user.
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE userid = :1 LIMIT 1", int(username))
			ViewUser = q.get()
		
		if ViewUser == None:
			## try another way
			## Get this user.
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE dispname = :1 LIMIT 1", username)
			ViewUser = q.get()


		if ViewUser != None:
				
			#self.write(ViewUser.avatar)
			#self.response.headers['Content-Type'] = 'image/'  #str(avatar.url_mime) 
			if ViewUser.avatar:
				outputStringUserMainPageTitle = ""
				outputStringUserMainPageTitle = "<img src='/img?img_user=" + str(ViewUser.key()) + "' width=64 height=64>"
				outputStringUserMainPageTitle += ViewUser.user.nickname() + "'s homepage"

			else:
				#self.write('none image')
				#self.response.out.write(' %s</div>' % cgi.escape(greeting.content))
				#tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND public = True ORDER BY date DESC LIMIT 15", ViewUser)
				outputStringUserMainPageTitle = ""
				outputStringUserMainPageTitle = "<img src='/img/default_avatar.jpg' width=64 height=64>"
				outputStringUserMainPageTitle += ViewUser.user.nickname() + "'s homepage"

				
				

			tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC", ViewUser.user)
			outputStringRoutineLog = ""
			
			if users.get_current_user() == None:
				UserNickName = "访客"
				logictag_OneoftheFriendsViewThisPage = False
			else:
				UserNickName = users.get_current_user().nickname()

				## Check whether the currentuser is a friend of this User.
				## Made preparation for the following public permission check.

				# code below are comming from GAE example
				q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
				CurrentUser = q.get()

				CurrentUserIsOneofViewUsersFriends = False

				for each_Friend_key in ViewUser.friends:
					if each_Friend_key == CurrentUser.key():
						CurrentUserIsOneofViewUsersFriends = True

				logictag_OtherpeopleViewThisPage = True
				logictag_OneoftheFriendsViewThisPage = True

			
			for each_Item in tarsusaItemCollection_UserRecentPublicItems:
				## Added Item public permission check.
		
				if each_Item.public == 'publicOnlyforFriends' and logictag_OneoftheFriendsViewThisPage == True:
					outputStringRoutineLog += '<a href="/i/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
				elif each_Item.public == 'public':
					outputStringRoutineLog += '<a href="/i/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
				else:
					pass



		else:
			#self.write('not found this user and any items')
			outputStringUserMainPageTitle = 'not found this user and any items'

			outputStringRoutineLog = 'None'


		if UserNickName != "访客":
			template_values = {
					'PrefixCSSdir': "../",
					
					'UserLoggedIn': 'Logged In',

					'UserNickName': UserNickName, 
					
					'UserMainPageUserTitle': outputStringUserMainPageTitle,
					
					'StringRoutineLog': outputStringRoutineLog,
			}

		else:
				template_values = {
					'PrefixCSSdir': "../",
					'UserMainPageUserTitle': outputStringUserMainPageTitle,
					'StringRoutineLog': outputStringRoutineLog,
			}



		path = os.path.join(os.path.dirname(__file__), 'pages/usermainpage.html')
		self.response.out.write(template.render(path, template_values))


class Image (webapp.RequestHandler):
	def get(self):
		greeting = db.get(self.request.get("img_user"))
		
		if greeting.avatar:
			self.response.headers['Content-Type'] = "image/"
			self.response.out.write(greeting.avatar)
			#img = images.Image(greeting.avatar)
			#tumbimg = img.execute_transforms(output_encoding=images.PNG)
			#self.response.headers['Content-Type'] = 'image/png'
			#self.response.out.write(tumbimg)
		else:
			self.error(404)

	

		


class DoneLogPage(tarsusaRequestHandler):
	def get(self):
		
		## TODO added permission check, anonymous user should not see any private donelog 
		
		#Donelog should shows User's Done Routine Log
		
		#Donelog page shows User Done's Log.

		username = cgi.escape(self.request.path[9:])  ## Get the username in the middle of /donelog/CNBorn
		
		if username == "": ## if the url are not directed to specific user.

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()

		else:
			
			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE urlname = :1", username)
			CurrentUser = q.get()
			if CurrentUser == None:
				## Can not find this user.
				self.redirect("/")


		tarsusaRoutineLogItemCollection = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 ORDER BY donedate DESC", CurrentUser.user)
		
		outputStringRoutineLog = ""
		Donedate_of_previousRoutineLogItem = None  ## To display the routine item log by Daily.

		for each_RoutineLogItem in tarsusaRoutineLogItemCollection:
			
			DoneDateOfThisItem = datetime.datetime.date(each_RoutineLogItem.donedate)

			if DoneDateOfThisItem != Donedate_of_previousRoutineLogItem:
				outputStringRoutineLog += str(DoneDateOfThisItem) + "Done<br />"
			
			## TODO
			## NOTICE! SPEED KILLER!
			#tarsusaItemCollection = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND "
			
			#tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC ", users.get_current_user(), each_tarsusaItemCollection_DailyRoutine.key().id())

			## Get what the name of this tarsusaItem is.
			ThisRoutineBelongingstarsusaItem = tarsusaItem.get_by_id(each_RoutineLogItem.routineid)
			
			if each_RoutineLogItem.routine != 'none':
				outputStringRoutineLog += 'Done ' + each_RoutineLogItem.routine + ' Routine - '
				## TODO
				## There will be updated when I need the Chinese Version.

			
				
			outputStringRoutineLog += '<a href=/i/' + str(ThisRoutineBelongingstarsusaItem.key().id()) + '>' + ThisRoutineBelongingstarsusaItem.name + "</a><br/>"

			Donedate_of_previousRoutineLogItem = DoneDateOfThisItem 

		## AT THIS PAgE
		## There should be also displaying ordinary items that done.
		## but since there will be a performance killer when selecting almost all doneitems
		## and a major con is that the date property in Datastore model can not be queried as a condition.
		## Thus made this thing more difficult.





		#tarsusaItemCollection = db.GqlQuery("SELECT * FROM tarsusaItem WHERE done = 1 ORDER BY date DESC")

		template_values = {
				'PrefixCSSdir': "../",
				
				'UserLoggedIn': 'Logged In',

				'UserNickName': CurrentUser.user.nickname(), 
				'singlePageTitle': "DoneLog Page",
				
				'StringRoutineLog': outputStringRoutineLog,
		}

	
		path = os.path.join(os.path.dirname(__file__), 'pages/donelog.html')
		self.response.out.write(template.render(path, template_values))





class StatsticsPage(tarsusaRequestHandler):
	def get(self):
		tarsusaItemCollection = db.GqlQuery("SELECT * FROM tarsusaItem ORDER BY date DESC")

		for tarsusaItem in tarsusaItemCollection:
			self.response.out.write('<blockquote>%s</blockquote>' %
                cgi.escape(tarsusaItem.name))

			self.response.out.write('<blockquote>%s</blockquote>' %
                cgi.escape(tarsusaItem.comment))

		self.write('--------------')

		tarsusaRoutineItemCollection = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem ORDER BY date DESC")

		for result in tarsusaRoutineItemCollection:
			self.response.out.write(result.routineid)

			self.response.out.write(result.donedate)

class FindFriendPage(tarsusaRequestHandler):
	def get(self):
	
		## Get Current User.
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()
		
		if users.get_current_user() == None:
			## Prompt them to register!
			self.redirect('/')
			##


		tarsusaPeopleCollection = db.GqlQuery("SELECT * FROM tarsusaUser LIMIT 500")

		#for each_tarsusaUser in tarsusaPeopleCollection:
		#	self.write(each_tarsusaUser)
		#	self.write('---<BR>')



		tarsusaUserFriendCollection = CurrentUser.friends

		UserFriends = ''
		if tarsusaUserFriendCollection: 
			for each_FriendKey in tarsusaUserFriendCollection:
				UsersFriend =  db.get(each_FriendKey)
				if UsersFriend.avatar:
					UserFriends += '<a href=/user/' + cgi.escape(UsersFriend.user.nickname()) +  '>' + "<img src=/img?img_user=" + str(UsersFriend.key()) + " width=64 height=64>" + cgi.escape(UsersFriend.user.nickname()) + '</a>&nbsp;'
					
					UserFriends += '<a href="#;" onclick="if (confirm(' + "'Are you sure to remove " + cgi.escape(UsersFriend.user.nickname()) + "')) {location.href = '/RemoveFriend/" + str(UsersFriend.key().id()) + "';}" + '" class="x">x</a>'
					
					UserFriends += 	'<br />'

				else:
					## Show Default Avatar
					UserFriends += '<a href=/user/' + cgi.escape(UsersFriend.user.nickname()) +  '>' + "<img src='/img/default_avatar.jpg' width=64 height=64>" + cgi.escape(UsersFriend.user.nickname()) + '</a>&nbsp;'
					UserFriends += '<a href="#;" onclick="if (confirm(' + "'Are you sure to remove " + cgi.escape(UsersFriend.user.nickname()) + "')) {location.href = '/RemoveFriend/" + str(UsersFriend.key().id()) + "';}" + '" class="x">x</a>'
					
					UserFriends += 	'<br />'
					


		else:
			UserFriends = '当前没有添加朋友'

		
		template_values = {
				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(self.login_user.nickname()),
				'UserID': CurrentUser.key().id(),
				'UserFriends': UserFriends,	
				'singlePageTitle': "查找朋友.",
				'singlePageContent': "",

				'tarsusaPeopleCollection': tarsusaPeopleCollection,
		}

	
		path = os.path.join(os.path.dirname(__file__), 'addfriend.html')
		self.response.out.write(template.render(path, template_values))


class AddFriendProcess(tarsusaRequestHandler):
	def get(self):
		
		# Permission check is very important.

		ToBeAddedUserId = self.request.path[11:]
			## Please be awared that ItemId here is a string!
		ToBeAddedUser = tarsusaUser.get_by_id(int(ToBeAddedUserId))

		## Get Current User.
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()

		AlreadyAddedAsFriend = False
		for eachFriend in CurrentUser.friends:
			if eachFriend == ToBeAddedUser.key():
				AlreadyAddedAsFriend = True	


		if ToBeAddedUser.key() != CurrentUser.key() and AlreadyAddedAsFriend == False:
			CurrentUser.friends.append(ToBeAddedUser.key())
			CurrentUser.put()

		else:
			## You can't add your self! and You can add a person twice!
			pass
		
		self.redirect('/FindFriend')


class RemoveFriendProcess(tarsusaRequestHandler):
	def get(self):
		
		# Permission check is very important.

		ToBeRemovedUserId = self.request.path[14:]
			## Please be awared that ItemId here is a string!
		ToBeRemovedUser = tarsusaUser.get_by_id(int(ToBeRemovedUserId))

		## Get Current User.
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()

		AlreadyAddedAsFriend = False
		for eachFriend in CurrentUser.friends:
			if eachFriend == ToBeRemovedUser.key():
				AlreadyAddedAsFriend = True	


		if ToBeRemovedUser.key() != CurrentUser.key() and AlreadyAddedAsFriend == True:
			CurrentUser.friends.remove(ToBeRemovedUser.key())
			CurrentUser.put()

		else:
			## You can't remove your self! and You can not remove a person that are not your friend!
			pass
		
		self.redirect('/FindFriend')
	
class DashboardPage(tarsusaRequestHandler):
	def get(self):
		print 'dashboard page'

class GuestbookPage(tarsusaRequestHandler):
	def get(self):
		strAboutPageTitle = "Nevada项目 - Guestbook"
		strAboutPageContent = '''Coming soon.<BR><BR>
		
		'''
		## Get Current User.
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()
	

		try:

			template_values = {
					'UserLoggedIn': 'Logged In',
					'UserNickName': cgi.escape(users.get_current_user().nickname()),
					'UserID': CurrentUser.key().id(),
					'singlePageTitle': strAboutPageTitle,
					'singlePageContent': strAboutPageContent,
			}
		
		except:

			
			template_values = {
				
				'UserNickName': "访客",
				'AnonymousVisitor': "Yes",
				'singlePageTitle': strAboutPageTitle,
				'singlePageContent': strAboutPageContent,

			}


	
		path = os.path.join(os.path.dirname(__file__), 'pages/simple_page.html')
		self.response.out.write(template.render(path, template_values))

	

class BlogPage(webapp.RequestHandler):
	def get(self):
		
		strAboutPageTitle = "Nevada项目 - Blog"
		strAboutPageContent = '''Coming soon.<BR><BR>
		
		'''
		## Get Current User.
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()
	

		try:

			template_values = {
					'UserLoggedIn': 'Logged In',
					'UserNickName': cgi.escape(users.get_current_user().nickname()),
					'UserID': CurrentUser.key().id(),
					'singlePageTitle': strAboutPageTitle,
					'singlePageContent': strAboutPageContent,
			}
		
		except:

			
			template_values = {
				
				'UserNickName': "访客",
				'AnonymousVisitor': "Yes",
				'singlePageTitle': strAboutPageTitle,
				'singlePageContent': strAboutPageContent,

			}


	
		path = os.path.join(os.path.dirname(__file__), 'pages/simple_page.html')
		self.response.out.write(template.render(path, template_values))



class AboutPage(tarsusaRequestHandler):
	def get(self):
	
		strAboutPageTitle = "关于Nevada项目"
		strAboutPageContent = '''这个项目目前可看作是tarsusa时间管理程序在GAE上面的延续，尽管目前离成熟相距甚远，而且GAE会被GFW时刻滋扰，不过我觉得体现出核心的东西才是最主要的<BR><BR>
		
		我正在准备写一篇较为详细的Nevada介绍，在完成之前，请先读下tarsusa的介绍以对这个工具有所了解<BR><BR>

		tarsusa是一个非常简单的时间管理程序。使用它，您可以方便地管理所有您要完成的事情。无论是将杂乱的事项分门别类地整理，还是提醒您优先处理即将到期的任务，tarsusa都游刃有余<BR>
		更为重要的，是 tarsusa 可以提醒您每天都必须完成的工作，并且记录您完成这些工作的情况。<BR><BR>
		
		我正在寻找让它独立于其它成熟或不成熟的项目管理（或说是日程管理）程序的气质，简洁，仍然显得非常重要<BR><BR>

		想太多无益，请立即开始吧！
		
		'''
		## Get Current User.
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()
	

		try:

			template_values = {
					'UserLoggedIn': 'Logged In',
					'UserNickName': cgi.escape(users.get_current_user().nickname()),
					'UserID': CurrentUser.key().id(),
					'singlePageTitle': strAboutPageTitle,
					'singlePageContent': strAboutPageContent,
			}
		
		except:

			
			template_values = {
				
				'UserNickName': "访客",
				'AnonymousVisitor': "Yes",
				'singlePageTitle': strAboutPageTitle,
				'singlePageContent': strAboutPageContent,

			}


	
		path = os.path.join(os.path.dirname(__file__), 'pages/simple_page.html')
		self.response.out.write(template.render(path, template_values))


class NotFoundPage(tarsusaRequestHandler):
	def get(self):
		
		self.redirect('/page/404.html')

		

class AjaxTestPage(webapp.RequestHandler):
	def get(self):
		
		strAboutPageTitle = "Nevada项目 - Blog"
	
		## Get Current User.
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()
	

		try:

			template_values = {
					'UserLoggedIn': 'Logged In',
					'UserNickName': cgi.escape(users.get_current_user().nickname()),
					'UserID': CurrentUser.key().id(),
					'singlePageTitle': strAboutPageTitle,
			}
		
		except:

			
			template_values = {
				
				'UserNickName': "访客",
				'AnonymousVisitor': "Yes",
				'singlePageTitle': strAboutPageTitle,

			}


	
		path = os.path.join(os.path.dirname(__file__), 'pages/ajax_test.html')
		self.response.out.write(template.render(path, template_values))





def main():
	application = webapp.WSGIApplication([('/', MainPage),
									   ('/Add', AddPage),
								       ('/additem',AddItemProcess),
									   ('/AddFriend/\\d+', AddFriendProcess),
									   ('/RemoveFriend/\\d+', RemoveFriendProcess),
									   ('/i/\\d+',ViewItem),
									   ('/doneItem/\\d+',DoneItem),
									   ('/undoneItem/\\d+',UnDoneItem),
									   ('/removeItem/\\d+', RemoveItem),
									   ('/tag/.+',Showtag),
									   ('/tag/', Showtag),
									   ('/user/.+/setting',UserSettingPage),
									   ('/user/.+/todo',UserToDoPage),
									   ('/user/.+/done',UserDonePage),
									   ('/user/.+', UserMainPage),
									   ('/img', Image),
									   ('/FindFriend', FindFriendPage),
									   ('/Login',LoginPage),
								       ('/SignIn',SignInPage),
									   ('/SignOut',SignOutPage),
								       ('/donelog/.+',DoneLogPage),
								       ('/Statstics',StatsticsPage),
								       ('/About',AboutPage),
								       ('/Blog',BlogPage),
									   ('/Guestbook', GuestbookPage),
									   ('/dashboard', DashboardPage),
									   ('/ajaxtest', AjaxTestPage),
									   ('.*',NotFoundPage)],
                                       debug=True)


	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
