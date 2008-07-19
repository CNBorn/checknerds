import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db

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
		
		if user:
		
			self.response.out.write ('<html><body>now begin to process the first tarsusa item!<BR><BR>')

			tarsusaItemCollection = db.GqlQuery("SELECT * FROM tarsusaItem ORDER BY date DESC LIMIT 10")

			for tarsusaItem in tarsusaItemCollection:
				if tarsusaItem.user:
					self.response.out.write('<b>%s</b> wrote:' % tarsusaItem.user.nickname())
				else:
					self.response.out.write('An anonymous person wrote:')

				self.response.out.write('<blockquote>%s</blockquote>' %
                    cgi.escape(tarsusaItem.name))

				self.response.out.write('<blockquote>%s</blockquote>' %
                    cgi.escape(tarsusaItem.comment))
	

			self.response.out.write ('<a href="/Add">Add an Item Now!</a>')

	    #else:
    	#	self.redirect(users.create_login_url(self.request.uri))

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
		预计完成于<br /></body></html>''')
	
					# first_tarsusa_item.name
			#print first_tarsusa_item.comment
			#print first_tarsusa_item.routine
			self.response.out.write ('''<input type="submit" name="submit" value="添加一个任务"></form>''')



class AddItemProcess(webapp.RequestHandler):
	def post(self):
		first_tarsusa_item = tarsusaItem(user=users.get_current_user(),name=cgi.escape(self.request.get('name')), comment=cgi.escape(self.request.get('comment')), tag=cgi.escape(self.request.get('tag')),
										routine="none", 
										public=False)
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
