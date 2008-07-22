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

			# Show His Daily Routine.
			tarsusaItemCollection_DailyRoutine = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'daily' ORDER BY date DESC", users.get_current_user())

			
			
			
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
				UserDonePercentage = UserDoneItems / UserTotalItems
			else:
				UserDonePercentage = 0.00



			## SPEED KILLER!
			## MULTIPLE DB QUERIES!
			## CAUTION! MODIFY THESE LATER!
			tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC LIMIT 5", users.get_current_user())
			tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True ORDER BY date DESC LIMIT 5", users.get_current_user())



			template_values = {
				'UserLoggedIn': 'Logged In',
				
				'UserNickName': self.login_user.nickname(),
				'tarsusaItemCollection_DailyRoutine': tarsusaItemCollection_DailyRoutine,
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 


				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
				'tarsusaItemCollection_UserDoneItems': tarsusaItemCollection_UserDoneItems,


				'UserTotalItems': UserTotalItems,
				'UserToDoItems': UserToDoItems,
				'UserDoneItems': UserDoneItems,
			}


			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'index.html')
			self.response.out.write(template.render(path, template_values))
			
			# For LoggedIn User, Show his own items.
			#self.response.out.write ('<html><body>now begin to process the first tarsusa item!<BR><BR>')

			#tarsusaItemCollection = db.GqlQuery("SELECT * FROM tarsusaItem ORDER BY date DESC LIMIT 10")

			#for tarsusaItem in tarsusaItemCollection:
			#	if tarsusaItem.user: 
			#		self.response.out.write('<b>%s</b> wrote:' % tarsusaItem.user.nickname())
			#	else:
			#		self.response.out.write('An anonymous person wrote:')

			#	self.response.out.write('<blockquote>%s</blockquote>' %
            #        cgi.escape(tarsusaItem.name))

			#	self.response.out.write('<blockquote>%s</blockquote>' %
            #       cgi.escape(tarsusaItem.comment))
			
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
		类别  <input type="text" name="tag" size="18" class="sl"><br />
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



class AddItemProcess(webapp.RequestHandler):
	def post(self):
		first_tarsusa_item = tarsusaItem(user=users.get_current_user(),name=cgi.escape(self.request.get('name')), comment=cgi.escape(self.request.get('comment')), tag=cgi.escape(self.request.get('tag')),
										routine=cgi.escape(self.request.get('routine')))
		if self.request.get('public') == "True":
			first_tarsusa_item.public = True
		else:
			first_tarsusa_item.public = False

		first_tarsusa_item.done = False

		first_tarsusa_item.put()
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
		}

	
		path = os.path.join(os.path.dirname(__file__), './single.html')
		self.response.out.write(template.render(path, template_values))


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





class StatsticsPage(webapp.RequestHandler):
	def get(self):
		tarsusaItemCollection = db.GqlQuery("SELECT * FROM tarsusaItem ORDER BY date DESC")

		for tarsusaItem in tarsusaItemCollection:
			self.response.out.write('An anonymous person wrote:')

			self.response.out.write('<blockquote>%s</blockquote>' %
                cgi.escape(tarsusaItem.name))

			self.response.out.write('<blockquote>%s</blockquote>' %
                cgi.escape(tarsusaItem.comment))
	
		
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
