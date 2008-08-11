import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
import os
import datetime
import string
from google.appengine.ext.webapp import template


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
				CurrentUser = tarsusaUser(user=users.get_current_user(), urlname=users.get_current_user().nickname())
				#self.write(CurrentUser.user.nickname())
				CurrentUser.put()

			
			## Check usedtags as the evaluation for Tags Model
			## TEMP CODE!
			UserTags = ''
			if CurrentUser.usedtags:
				for each_cate in CurrentUser.usedtags:
					each_tag =  db.get(each_cate)
					#Below line will triggar the 0xe9 unicode problem!
					UserTags += '<a href=/tag/' + cgi.escape(each_tag.name) +  '>' + cgi.escape(each_tag.name) + '</a>&nbsp;'
					#UserTags += 'abc' + unicode(cgi.escape(each_tag.name))
			

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
				for tarsusaItem_DoneDailyRoutine in tarsusaItemCollection_DoneDailyRoutine:
					if datetime.datetime.date(tarsusaItem_DoneDailyRoutine.donedate) == datetime.datetime.date(datetime.datetime.now()):
						#Check if the user had done all his routine today.
						Today_DoneRoutine += 1
						
						# This routine have been done today.
						
						# Due to solve this part, I have to change tarsusaItemModel to db.Expando
						# I hope there is not so much harm for performance.
						each_tarsusaItemCollection_DailyRoutine.donetoday = 1
						each_tarsusaItemCollection_DailyRoutine.put()

					else:
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


			## TODO
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
						if tarsusaItem_UserFriendsRecentItems.done == True: ## And Public to friends!
							
							UserFriendsActivities += '<a href="/user/' + UsersFriend.user.nickname() + '">' +  UsersFriend.user.nickname() + '</a> Done <a href="/i/' + tarsusaItem_UserFriendsRecentItems.key().id() + '">' + tarsusaItem_UserFriendsRecentItems.name + '</a><br />'
	 
						else:
							UserFriendsActivities += '<a href="/user/' + UsersFriend.user.nickname() + u'">' + UsersFriend.user.nickname() + '</a> ToDO <a href="/i/' + str(tarsusaItem_UserFriendsRecentItems.key().id()) + '">' + tarsusaItem_UserFriendsRecentItems.name + '</a><br />'


			else:
				UserFriendsActivities = '当前没有添加朋友'

								

			template_values = {
				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(self.login_user.nickname()),
				
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


			tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE public = True and routine = 'none' ORDER BY date DESC")

			tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE public = True and routine = 'none' and done = True ORDER BY date DESC")
			
			
			
			
			
			
			
			
			
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
		
		if user:
		
			self.response.out.write ('<html><body>add the first tarsusa item!')
			self.response.out.write ('''<form action="/additem" method="post">
									标题  <input type="text" name="name" value="" size="18" class="sl"><br />
									内容  <textarea name="comment" rows="4" cols="16" wrap="PHYSICAL" class="ml"></textarea><br />
									类别  <input type="text" name="tags" size="18" class="sl"><br />
									预计完成于<br />''')
			self.response.out.write ('''性质：<select name="routine">
									<option value="none" selected="selected">非坚持性任务</option>
									<option value="daily">每天</option>
									<option value="weekly">每周</option>
									<option value="monthly">每月</option>
									<option value="seasonly">每季度</option>
									<option value="yearly">每年</option>
									</select><br>''')
	
		## TODO 
		## Added proper calendar date select form
		## Tested django form, it doesnt contain that

			self.response.out.write ('<input type="checkbox" name="public" value="True">公开项目<BR>')

			self.response.out.write ('''<input type="submit" name="submit" value="添加一个任务"></form>''')

		else:
			self.write ("Your are not logged in!")

class AddItemProcess(tarsusaRequestHandler):
	def post(self):
		first_tarsusa_item = tarsusaItem(user=users.get_current_user(),name=cgi.escape(self.request.get('name')), comment=cgi.escape(self.request.get('comment')),routine=cgi.escape(self.request.get('routine')))
		
		# for changed tags from String to List:
		#first_tarsusa_item.tags = cgi.escape(self.request.get('tags')).split(",")
		tarsusaItem_Tags = cgi.escape(self.request.get('tags')).split(",")
		
		## TODO
		## If user defines tag is None, Add '为分类项目' in Database?
		## Or Just display it with Database Logical?
		

		if self.request.get('public') == "True":
			first_tarsusa_item.public = True
		else:
			first_tarsusa_item.public = False

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
			each_cat = Tag(name=each_tag_in_tarsusaitem)
			#each_cat.count += 1
			each_cat.put()
			first_tarsusa_item.tags.append(each_cat.key())
			CurrentUser.usedtags.append(each_cat.key())		
		first_tarsusa_item.put()
		CurrentUser.put()



		UserTags = ''
		for each_cate in CurrentUser.usedtags:
			each_tag =  db.get(each_cate)
			UserTags += '<a href=/tag/' + cgi.escape(each_tag.name) +  '>' + cgi.escape(each_tag.name) + '</a>&nbsp;'

		self.write(UserTags)

		self.redirect('/')

class ViewItem(tarsusaRequestHandler):
	def get(self):
		#self.current_page = "home"
		postid = self.request.path[3:]
		tItem = tarsusaItem.get_by_id(int(postid))

		if tItem != None:  ## If this Item existed in Database.

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
				if tItem.public == True:
					logictag_OtherpeopleViewThisItem = True
				else:
					self.redirect('/')

			template_values = {
					'PrefixCSSdir': "../",
					
					'UserNickName': "The About page of Nevada.",
					'singlePageTitle': "View Item",
					'singlePageContent': "",

					'logictag_OtherpeopleViewThisItem': logictag_OtherpeopleViewThisItem,


					'tarsusaItem': tItem,
					'tarsusaItemDone': tItem.done,
					'tarsusaItemTags': ItemTags,
			}

		
			path = os.path.join(os.path.dirname(__file__), './single.html')
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
				NewlyDoneRoutineItem.routine = tItem.routine
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



		self.redirect('/')




class Showtag(tarsusaRequestHandler):
	def get(self):
		each_cat = Tag(name=self.request.path[5:])
		self.write(each_cat.name)
		self.write(each_cat.count)
		

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
		self.write('This is user setting page.')
		
		username = cgi.escape(self.request.path[6:-8])  ## Get the username in the middle of /user/CNBorn/setting
		self.write(username)





class UserMainPage(tarsusaRequestHandler):
	def get(self):

		username = cgi.escape(self.request.path[6:])  ## Get the username in the middle of /user/CNBorn/
	
		self.write('user ' + username + "'s page")

		## Get this user.
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE urlname = :1 LIMIT 1", username)
		
		ViewUser = q.get()
		self.write(ViewUser)

		if ViewUser != None:
			#tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND public = True ORDER BY date DESC LIMIT 15", ViewUser)

			#tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC", ViewUser)
			
			tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC", ViewUser.user)
			for each_Item in tarsusaItemCollection_UserRecentPublicItems:
				self.write(each_Item.name)

		else:
			self.write('not found any items')

	

		


class DoneLogPage(tarsusaRequestHandler):
	def get(self):
		#Donelog should shows User's Done Routine Log
		
		#Donelog page shows User Done's Log.

		tarsusaItemCollection = db.GqlQuery("SELECT * FROM tarsusaItem WHERE done = 1 ORDER BY date DESC")

		template_values = {
				'PrefixCSSdir': "../",
				
				'UserNickName': "The About page of Nevada.",
				'singlePageTitle': "DoneLog Page",
				'singlePageContent': "",
				
				'DonelogItemCollection': tarsusaItemCollection,

		}

	
		path = os.path.join(os.path.dirname(__file__), './single.html')
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
		
		
		tarsusaPeopleCollection = db.GqlQuery("SELECT * FROM tarsusaUser")

		#for each_tarsusaUser in tarsusaPeopleCollection:
		#	self.write(each_tarsusaUser)
		#	self.write('---<BR>')

		## Get Current User.
		# code below are comming from GAE example
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		CurrentUser = q.get()

		tarsusaUserFriendCollection = CurrentUser.friends

		UserFriends = ''
		if tarsusaUserFriendCollection: 
			for each_FriendKey in tarsusaUserFriendCollection:
				UsersFriend =  db.get(each_FriendKey)
				UserFriends += '<a href=/user/' + cgi.escape(UsersFriend.user.nickname()) +  '>' + cgi.escape(UsersFriend.user.nickname()) + '</a>&nbsp;<br />'
		else:
			UserFriends = '当前没有添加朋友'

		
		template_values = {
				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(self.login_user.nickname()),

				'UserFriends': UserFriends,	
				'singlePageTitle': "The About page of Nevada.",
				'singlePageContent': "This is the About content.",

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

	



class BlogPage(webapp.RequestHandler):
	def get(self):
		print "this is Blog page"



class AboutPage(tarsusaRequestHandler):
	def get(self):
		
		template_values = {
				'UserNickName': "The About page of Nevada.",
				'singlePageTitle': "The About page of Nevada.",
				'singlePageContent': "This is the About content.",
		}

	
		path = os.path.join(os.path.dirname(__file__), 'single.html')
		self.response.out.write(template.render(path, template_values))


class NotFoundPage(tarsusaRequestHandler):
	def get(self):
		
		self.redirect('/page/404.html')

		

def main():
	application = webapp.WSGIApplication([('/', MainPage),
									   ('/Add', AddPage),
								       ('/additem',AddItemProcess),
									   ('/AddFriend/\\d+', AddFriendProcess),
									   ('/i/\\d+',ViewItem),
									   ('/doneItem/\\d+',DoneItem),
									   ('/undoneItem/\\d+',UnDoneItem),
									   ('/tag/.+',Showtag),
									   ('/user/.+/setting',UserSettingPage),
									   ('/user/.+', UserMainPage),
									   ('/FindFriend', FindFriendPage),
									   ('/Login',LoginPage),
								       ('/SignIn',SignInPage),
									   ('/SignOut',SignOutPage),
								       ('/donelog',DoneLogPage),
								       ('/Statstics',StatsticsPage),
								       ('/About',AboutPage),
								       ('/Blog',BlogPage),
									   ('.*',NotFoundPage)],
                                       debug=True)


	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
