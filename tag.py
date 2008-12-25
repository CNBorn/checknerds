# -*- coding: utf-8 -*-
# CheckNerds 
# - tag.py
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
import logging
import urllib


class Showtag(tarsusaRequestHandler):
	def get(self):
		
		RequestCatName = urllib.unquote(self.request.path[5:])
		catlll = db.GqlQuery("SELECT * FROM Tag WHERE name = :1", RequestCatName.decode('utf-8'))

		# New CheckLogin code built in tarsusaRequestHandler 
		if self.chk_login():
			CurrentUser = self.get_user_db()
		else:
			self.redirect('/')
		
		if self.request.path[5:] <> '':
			
			try:

				each_cat = catlll[0]
				UserNickName = users.get_current_user().nickname()
				
				CountDoneItems = 0
				CountTotalItems = 0

				
				#html_tag_DeleteThisTag = '<a href="/deleteTag/"' + str(each_cat.key().id()) + '>X</a>'
				html_tag_DeleteThisTag = ''
				## NOTICE that the /deleteTag should del the usertags in User model.

				#browser_Items = tarsusaItem(user=users.get_current_user(), routine="none")
				browser_Items = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY done, date DESC", users.get_current_user())

				html_tag_ItemList = ""
				for eachItem in browser_Items:
					for eachTag in eachItem.tags:
						try:

							if db.get(eachTag).name == RequestCatName.decode('utf-8'):								
								CountTotalItems += 1
								#self.write(eachItem.name)
								#html_tag_ItemList += eachItem.name + "<br />"
								if eachItem.done == False:
									html_tag_ItemList += '<a href=/item/' + str(eachItem.key().id()) + '>' + cgi.escape(eachItem.name) + "</a><br/>"
								else:
									html_tag_ItemList += '<img src="/img/accept16.png"><a href=/item/' + str(eachItem.key().id()) + '>' + cgi.escape(eachItem.name) + "</a><br/>"
									CountDoneItems += 1
								
						except:
							pass

				strTagStatus = "共有项目" + str(CountTotalItems) + "&nbsp;完成项目" + str(CountDoneItems) + "&nbsp;未完成项目" + str(CountTotalItems - CountDoneItems)

				template_values = {
						'PrefixCSSdir': "/",
						
						'UserLoggedIn': 'Logged In',
						'UserID': CurrentUser.key().id(),

						'UserNickName': users.get_current_user().nickname(),
						'DeleteThisTag': html_tag_DeleteThisTag,
						'TagName': each_cat.name,
						'TagStatus': strTagStatus,
						'ItemList': html_tag_ItemList,


				}

			
				path = os.path.join(os.path.dirname(__file__), 'pages/viewtag.html')
				self.response.out.write(template.render(path, template_values))

			except:
				## There is no this tag!
				## There is something wrong with Showtag!
				self.redirect("/")
				#pass


		else:
			
			if self.request.path[5:] == '':
				## Show Items with no tag.

				#browser_Items = tarsusaItem(user=users.get_current_user(), routine="none")
				browser_Items = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC", users.get_current_user())

				html_tag_DeleteThisTag = '无标签项目'

				CountDoneItems = 0
				CountTotalItems = 0

				html_tag_ItemList = ""
				for eachItem in browser_Items:
					if len(eachItem.tags) == 0:
						CountTotalItems += 1
						if eachItem.done == False:
							html_tag_ItemList += '<a href=/item/' + str(eachItem.key().id()) + '>' + cgi.escape(eachItem.name) + "</a><br/>"
						else:
							html_tag_ItemList += '<img src="/img/accept16.png"><a href=/item/' + str(eachItem.key().id()) + '>' + cgi.escape(eachItem.name) + "</a><br/>"
							CountDoneItems += 1
				
				strTagStatus = "共有项目" + str(CountTotalItems) + "&nbsp;完成项目" + str(CountDoneItems) + "&nbsp;未完成项目" + str(CountTotalItems - CountDoneItems)

				template_values = {
						'PrefixCSSdir': "/",
						
						'UserLoggedIn': 'Logged In',

						'UserNickName': users.get_current_user().nickname(),
						'DeleteThisTag': html_tag_DeleteThisTag,
						'TagName': "未分类项目",
						'TagStatus': strTagStatus,
						'ItemList': html_tag_ItemList,
				}
				
				path = os.path.join(os.path.dirname(__file__), 'pages/viewtag.html')
				self.response.out.write(template.render(path, template_values))

			else:
				## There is no this tag!
				self.redirect("/")


def main():
	application = webapp.WSGIApplication([('/tag/.+',Showtag),
									   ('/tag/', Showtag)],
                                       debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()

