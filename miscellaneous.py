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




class GuestbookPage(tarsusaRequestHandler):
	def get(self):
		strAboutPageTitle = "CheckNerds项目 - Guestbook"
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
		
		strAboutPageTitle = "CheckNerds - Blog"
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
		import os

		strAboutPageTitle = "关于CheckNerds项目"
		strAboutPageContent = '''这个项目目前可看作是tarsusa时间管理程序在GAE上面的延续，尽管目前离成熟相距甚远，而且GAE会被GFW时刻滋扰，不过我觉得体现出核心的东西才是最主要的<BR><BR>
		CheckNerds是一个非常简单的时间管理程序。使用它，您可以方便地管理所有您要完成的事情。无论是将杂乱的事项分门别类地整理，还是提醒您优先处理即将到期的任务，都游刃有余<BR>
		更为重要的，是CheckNerds提醒您每天都必须完成的工作，并且记录您完成这些工作的情况。<BR><BR>
		
		我正在寻找让它独立于其它成熟或不成熟的项目管理（或说是日程管理）程序的气质，简洁，仍然显得非常重要<BR><BR>

		想要了解详细的CheckNerds介绍，您可<a href="http://blog.donews.com/CNBorn/archive/2008/10/23/1366803.aspx" target="_blank">点击这里</a><br /><br />

		想太多无益，请立即开始吧！
		
		'''
		
		#for name in os.environ.keys():
		#	self.response.out.write("%s = %s<br />\n" % (name, os.environ[name]))
		strAboutPageContent += '<br /><br />ENV:<br /><p>CheckNerds - dev ' + os.environ['CURRENT_VERSION_ID']
		strAboutPageContent += '<br />server - ' + os.environ['SERVER_SOFTWARE']
		strAboutPageContent += '<br />http_user_agent - ' + os.environ['HTTP_USER_AGENT']
		strAboutPageContent += '</p>'

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



def main():
	application = webapp.WSGIApplication([('/about',AboutPage),
								       ('/blog',BlogPage),
									   ('/guestbook', GuestbookPage)],
                                       debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
