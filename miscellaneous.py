# -*- coding: utf-8 -*-


# CheckNerds 
# - miscellaneous.py
# Cpoyright (C) CNBorn, 2008
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn


#from django.conf import settings
#settings._target = None
import os
import sys
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

from google.appengine.api import memcache

class GuestbookPage(tarsusaRequestHandler):
	def get(self):
		strAboutPageTitle = "CheckNerds项目 - Guestbook"
		strAboutPageContent = '''<br /><iframe src="http://spreadsheets.google.com/embeddedform?key=pWd4_W1-LSL4xnGNRuHq6JA" width="95%" height="735" frameborder="0" marginheight="0" marginwidth="0">正在加载...</iframe><BR>
		
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

class BlogPage(tarsusaRequestHandler):
	def get(self):
		
		#from google.appengine.api import urlfetch
		# GAE中对远程网页的获取不能通过urllib，只能通过google自己的urlfetch   

		#url = "http://feed.feedsky.com/cnborn"
		#result = urlfetch.fetch(url)
		
		#if result.status_code == 200:
			
			#import xml.sax
			#from xml.dom import minidom
			#xmldoc = minidom.parseString(result.content.decode('utf-8')))

			#parser = rss_parser()
			#strAboutPageContent = result.content.decode('utf-8')


		#strAboutPageContent = '''Coming soon.<BR><BR>''' #+ d.entries[0].title + d.entries[0].link + d.entries[0].description + d.entries[0].date + d.entries[0].date_parsed + d.entries[0].id

		strAboutPageContent = '''<div id="twitter_div"><ul id="twitter_update_list"></ul></div>
								<script type="text/javascript" src="http://twitter.com/javascripts/blogger.js"></script>
								<script type="text/javascript" src="http://twitter.com/statuses/user_timeline/checknerds.json?callback=twitterCallback2&amp;count=10"></script>'''

		strAboutPageTitle = "CheckNerds - Recent Updates (powered by Twitter)"
		
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

		想太多无益，请立即开始吧！<br />
		<br />
	
		CheckNerds每天都在改进中！想要了解开发详情，欢迎关注Twitter: <a href="http://www.twitter.com/CNBorn">http://twitter.com/CNBorn</a><br />
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


class StatsticsPage(tarsusaRequestHandler):
	def get(self):
		
		# Show statstics information.

		if self.chk_login():
			CurrentUser = self.get_user_db()
		else:
			self.redirect('/')
		
		TotalUserCount = db.GqlQuery("SELECT * FROM tarsusaUser").count()
		TotaltarsusaItem = db.GqlQuery("SELECT * FROM tarsusaItem").count()
		
		htmltag = ''
		htmltag += 'Uptime: ' + str(datetime.datetime.now() - datetime.datetime(2008,8,26,20,0,0))
		htmltag += '<br />Project Started Since: ' + str(datetime.date.today() - datetime.date(2008, 7, 19)) + ' ago.'
		htmltag += '<br />User Account: ' + str(TotalUserCount)
		htmltag += '<br />Total Items: ' + str(TotaltarsusaItem)

		try:
			htmltag += '<br /><br /><b>memcached stats:</b>'
			stats = memcache.get_stats()    
			htmltag += "<br /><b>Cache Hits:</b>" + str(stats['hits'])
			htmltag += "<br /><b>Cache Misses:</b>" +str(stats['misses'])					
			htmltag += "<br /><b>Total Requested Cache bytes:</b>" +str(stats['byte_hits'])
			htmltag += "<br /><b>Total Cache items:</b>" +str(stats['items'])
			htmltag += "<br /><b>Total Cache bytes:</b>" +str(stats['bytes'])
			htmltag += "<br /><b>Oldest Cache items:</b>" +str(stats['oldest_item_age'])
		except:
			pass

		template_values = {
			'UserLoggedIn': 'Logged In',				
			'UserNickName': cgi.escape(self.login_user.nickname()),
			'UserID': CurrentUser.key().id(),	
			
			'singlePageTitle': 'Statstics',
			'singlePageContent': htmltag,

			'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
			'htmltag_TotalUser': TotalUserCount,
			'htmltag_TotaltarsusaItem': TotaltarsusaItem,

		}
		
		#Manupilating Templates	
		path = os.path.join(os.path.dirname(__file__), 'pages/simple_page.html')
		self.response.out.write(template.render(path, template_values))


class FlushCache(tarsusaRequestHandler):
	def get(self):
		memcache.flush_all()
		self.redirect('/')
		

def main():
	application = webapp.WSGIApplication([('/about',AboutPage),
								       ('/blog',BlogPage),
								       ('/statstics',StatsticsPage),
									   ('/flushcache', FlushCache),
									   ('/guestbook', GuestbookPage)],
                                       debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
