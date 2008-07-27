import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
import os
import datetime
from google.appengine.ext.webapp import template


from modules import *
from base import *


class MainPage(tarsusaRequestHandler):
	def get(self):
		
		#user = users.get_current_user()	
		
		if self.chk_login() == True:

			## Check usedtags as the evaluation for Tags Model
			## TEMP CODE!
			
			UserUsedTagsItems = db.GqlQuery("SELECT * FROM User WHERE user = :1", users.get_current_user())
			for User in UserUsedTagsItems:
				self.write(User.name)
				self.write(User.usedtags)


			# Show His Daily Routine.
			tarsusaItemCollection_DailyRoutine = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'daily' ORDER BY date DESC", users.get_current_user())

			tarsusaItemCollection_DoneDailyRoutine = tarsusaRoutineLogItem 


			# GAE datastore has a gqlquery.count limitation. So right here solve this manully.
			tarsusaItemCollection_DailyRoutine_count = 0
			for each_tarsusaItemCollection_DailyRoutine in tarsusaItemCollection_DailyRoutine:
				tarsusaItemCollection_DailyRoutine_count +=1

			for each_tarsusaItemCollection_DailyRoutine in tarsusaItemCollection_DailyRoutine:
				
				#This query should effectively read out all dailyroutine done by today.
				#for the result will be traversed below, therefore it should be as short as possible.
				#MARK FOR FUTURE IMPROVMENT
				
				# GAE datastore has a gqlquery.count limitation. So right here solve this manully.
				#tarsusaItemCollection_DailyRoutine_count
				# Refer to code above.
				
				
				#LIMIT and OFFSET don't currently support bound parameters.
				# http://code.google.com/p/googleappengine/issues/detail?id=179
				# if this is realized, the code below next line will be used.

				tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC ", users.get_current_user(), each_tarsusaItemCollection_DailyRoutine.key().id())
				
				#tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC LIMIT :3", users.get_current_user(), each_tarsusaItemCollection_DailyRoutine.key().id(), int(tarsusaItemCollection_DailyRoutine_count))

				## traversed RoutineDaily
				tarsusaItem_DailyRoutineDoneTable = []
				for tarsusaItem_DoneDailyRoutine in tarsusaItemCollection_DoneDailyRoutine:
					if datetime.datetime.date(tarsusaItem_DoneDailyRoutine.donedate) == datetime.datetime.date(datetime.datetime.now()):
						# This routine have been done today.
						
						# Due to solve this part, I have to change tarsusaItemModel to db.Expando
						# I hope there is not so much harm for performance.
						each_tarsusaItemCollection_DailyRoutine.donetoday = 1
						each_tarsusaItemCollection_DailyRoutine.put()

					else:
						pass





			
			
			
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


			## Calculating Tags 
			## There is another performance killer.
			
			#SystemTags = db.GqlQuery("SELECT * FROM Tag")
			UserUsedTagsItems = db.GqlQuery("SELECT * FROM User WHERE user = :1 LIMIT 1", users.get_current_user())
			
			UserUsedTagsName = []

			for UserUsedTags in UserUsedTagsItems:
				UserUsedTagsName = split_tags(UserUsedTags.usedtags)
			
			UserTags = []

			for UserUsedTag in UserUsedTagsName:
				tmpSystemTagRead = Tag.all().filter("name=",UserUesdTag)
				
				if tmpSystemTagRead != None:
					UserTags.append(tmpSystemTagRead.name)



			template_values = {
				'UserLoggedIn': 'Logged In',
				
				'UserNickName': self.login_user.nickname(),
				
				'tarsusaItemCollection_DailyRoutine': tarsusaItemCollection_DailyRoutine,


				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 

				'UserUsedTags': UserTags,

				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
				'tarsusaItemCollection_UserDoneItems': tarsusaItemCollection_UserDoneItems,


				'UserTotalItems': UserTotalItems,
				'UserToDoItems': UserToDoItems,
				'UserDoneItems': UserDoneItems,
				'UserDonePercentage': UserDonePercentage,
			}


			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'index.html')
			self.response.out.write(template.render(path, template_values))
			
		else:
			template_values = {
				
				'UserNickName': "访客",
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 


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
			self.response.out.write ('<input type="checkbox" name="public" value="True">公开项目<BR>')

			self.response.out.write ('''<input type="submit" name="submit" value="添加一个任务"></form>''')

		else:
			self.write ("Your are not logged in!")

class AddItemProcess(webapp.RequestHandler):
	def post(self):
		first_tarsusa_item = tarsusaItem(user=users.get_current_user(),name=cgi.escape(self.request.get('name')), comment=cgi.escape(self.request.get('comment')), tags=cgi.escape(self.request.get('tags')),
										routine=cgi.escape(self.request.get('routine')))
		if self.request.get('public') == "True":
			first_tarsusa_item.public = True
		else:
			first_tarsusa_item.public = False

		first_tarsusa_item.done = False

		## the creation date will be added automatically by GAE datastore
		first_tarsusa_item.put()
		
		#Derived from Plog, update the Tag module.
		update_tag_count(old_tags = [], new_tags = cgi.escape(self.request.get('tags')))

		# According to New Tags system, The User model must be used.

		#User.get_by_user(users.get_current_user()).tags += self.request.get('tags')
		#User = Comment.all().filter('post = ', post).order('date')
		UserSettings = db.GqlQuery("SELECT * FROM User WHERE user = :1 LIMIT 1", users.get_current_user())
		for User in UserSettings:
			User.usedtags += self.request.get('tags')
			User.put()
		


		
		# Haven't know what will the below code do.
		# Count the Tags?
		
		#all_post_tag = Tag.get_by_key_name('all_post_tag')
		#all_post_tag.count += 1
		#all_post_tag.put()




		self.redirect('/')

class ViewItem(tarsusaRequestHandler):
	def get(self):
		#self.current_page = "home"
		postid = self.request.path[3:]
		#self.write(postid)
		tItem = tarsusaItem.get_by_id(int(postid))
		#self.write(tItem.name)

		template_values = {
				'PrefixCSSdir': "../",
				
				'UserNickName': "The About page of Nevada.",
				'singlePageTitle': tItem.name,
				'singlePageContent': tItem.comment,


				'tarsusaItem': tItem,
				'tarsusaItemDone': tItem.done
		}

	
		path = os.path.join(os.path.dirname(__file__), './single.html')
		self.response.out.write(template.render(path, template_values))


class DoneItem(tarsusaRequestHandler):
	def get(self):
				
		ItemId = self.request.path[10:]
		tItem = tarsusaItem.get_by_id(int(ItemId))

		if tItem.user == users.get_current_user():
			## Check User Permission to done this Item

			if tItem.routine == 'none':
				## if this item is not a routine item.

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



		self.redirect('/')


class UnDoneItem(tarsusaRequestHandler):
	def get(self):

		# Permission check is very important.

		ItemId = self.request.path[12:]
		tItem = tarsusaItem.get_by_id(int(ItemId))

		if tItem.user == users.get_current_user():
			## Check User Permission to done this Item

			if tItem.routine == 'none':
				## if this item is not a routine item.
				tItem.done = False

				tItem.put()
			else:
				if tItem.routine == 'daily':
					del tItem.donetoday
					## This is a daily routine, and we are going to undone it.
					## For DailyRoutine, now I just count the matter of deleting today's record.
					## the code for handling the whole deleting routine( delete all concerning routine log ) will be added in future
					
					# GAE can not make dateProperty as query now! There is a BUG for GAE!
					# http://blog.csdn.net/kernelspirit/archive/2008/07/17/2668223.aspx
					tarsusaRoutineLogItemCollection_ToBeDeleted = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate = :2", ItemId, datetime.datetime.date(datetime.datetime.now()))
					for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
						result.delete()



		self.redirect('/')




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

class UserMainPage(tarsusaRequestHandler):
	def get(self):
		print "this is UserMainpage"





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

		for tarsusaItem in tarsusaRoutineItemCollection:
			self.response.out.write('<blockquote>%s</blockquote>' %
                cgi.escape(tarsusaItem.routineid))

			self.response.out.write('<blockquote>%s</blockquote>' %
                cgi.escape(tarsusaItem.donedate))	
		
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


def main():
	application = webapp.WSGIApplication([('/', MainPage),
									   ('/Add', AddPage),
								       ('/additem',AddItemProcess),
									   ('/i/\\d+',ViewItem),
									   ('/doneItem/\\d+',DoneItem),
									   ('/undoneItem/\\d+',UnDoneItem),
									   ('/Login',LoginPage),
								       ('/SignIn',SignInPage),
									   ('/SignOut',SignOutPage),
                                       ('/UserMainPage',UserMainPage),
								       ('/Statstics',StatsticsPage),
								       ('/About',AboutPage),
								       ('/Blog',BlogPage)],
                                       debug=True)


	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
