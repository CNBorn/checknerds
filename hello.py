import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
import os
import datetime
from google.appengine.ext.webapp import template



class tarsusaItem(db.Model):
    user = db.UserProperty()
    name = db.StringProperty()
    comment = db.StringProperty(multiline=True)
    tag = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    expectdate = db.DateTimeProperty()
    donedate = db.DateTimeProperty()
    done = db.BooleanProperty()
    routine = db.StringProperty(required=True, choices=set(["none", "daily", "weekly", "monthly", "seasonly", "yearly"]))
    public = db.BooleanProperty()



class MainPage(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()	
		
		if user != None:

			# Show His Daily Routine.
			tarsusaItemCollection = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'daily' ORDER BY date DESC",
                               users.get_current_user())

			#for tarsusaItem in tarsusaItemCollection:
			#		self.response.out.write('<b>%s</b> wrote:' % tarsusaItem.user.nickname())
			#	self.response.out.write('<blockquote>%s</blockquote>' %
            #       cgi.escape(tarsusaItem.comment))
			
			template_values = {
				'UserNickName': user.nickname(),
				'tarsusaItemCollection': tarsusaItemCollection,
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
				}

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
			
			path = os.path.join(os.path.dirname(__file__), 'index.html')
			self.response.out.write(template.render("./index.html", template_values))
	

			#self.response.out.write ('<a href="/Add">Add an Item Now!</a>')

		else:
    	
			tarsusaItemCollection = db.GqlQuery("SELECT * FROM tarsusaItem WHERE public=True ORDER BY date DESC LIMIT 10")

			#for tarsusaItem in tarsusaItemCollection:
				#self.response.out.write('An anonymous person wrote:')

				#self.response.out.write('<blockquote>%s</blockquote>' %
                #    cgi.escape(tarsusaItem.name))

				#self.response.out.write('<blockquote>%s</blockquote>' %
                #    cgi.escape(tarsusaItem.comment))

		
		
		#Manupilating Templates	
		#path = os.path.join(os.path.dirname(__file__), 'index.html')

		#self.redirect(users.create_login_url(self.request.uri))

class AddPage(webapp.RequestHandler):
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

			# first_tarsusa_item.name
			#print first_tarsusa_item.comment
			#print first_tarsusa_item.routine
			self.response.out.write ('''<input type="submit" name="submit" value="添加一个任务"></form>''')



class AddItemProcess(webapp.RequestHandler):
	def post(self):
		first_tarsusa_item = tarsusaItem(user=users.get_current_user(),name=cgi.escape(self.request.get('name')), comment=cgi.escape(self.request.get('comment')), tag=cgi.escape(self.request.get('tag')),
										routine=cgi.escape(self.request.get('routine')))
		if self.request.get('public') == "True":
			first_tarsusa_item.public = True
		else:
			first_tarsusa_item.public = False
										
		first_tarsusa_item.put()
		self.redirect('/')


class LoginPage(webapp.RequestHandler):
	def get(self):
		print "this is login page"

class SignInPage(webapp.RequestHandler):
	def get(self):
		print "this is signinpage"

class SignOutPage(webapp.RequestHandler):
	def get(self):
		print ""
		self.redirect(users.create_login_url(self.request.uri))

class UserMainPage(webapp.RequestHandler):
	def get(self):
		print "this is UserMainpage"
class StatsticsPage(webapp.RequestHandler):
	def get(self):
		print "this is  Statsticspage"
class BlogPage(webapp.RequestHandler):
	def get(self):
		print "this is Blog page"



class AboutPage(webapp.RequestHandler):
	def get(self):
		print "This is about page"




def main():
	application = webapp.WSGIApplication([('/', MainPage),
									   ('/Add', AddPage),
								       ('/additem',AddItemProcess),
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
