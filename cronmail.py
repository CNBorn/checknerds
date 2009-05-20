# -*- coding: utf-8 -*-
# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename Nevada->California
# - cronmail.py
# Copyright (C) CNBorn, 2008-2009
# http://cnborn.net, http://twitter.com/CNBorn
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
import tarsusaCore

from modules import *
from base import *
import logging
from google.appengine.api import mail

class DailyBriefReport(tarsusaRequestHandler):
  def get(self):
	user_address = "cnborn@gmail.com"

	if not mail.is_email_valid(user_address):
		# prompt user to enter a valid address
		#print 'error'
		pass

	else:
		if self.chk_login():
			CurrentUser = self.get_user_db()

		tarsusaItemCollection = tarsusaCore.get_dailyroutine(CurrentUser.key().id())
		tarsusaItem_DueToday = tarsusaCore.get_ItemsDueToday(CurrentUser.key().id())
		
		ItemsInMail = ''
		for eachItem in tarsusaItem_DueToday:
			ItemsInMail += "<li><a href=/item/" + eachItem['id'] + ">" + eachItem['name'] + "</a></li>"

		DueTodayTotal = len(tarsusaItemCollection) + len(tarsusaItem_DueToday)
			
		message = mail.EmailMessage()
		message.sender = "cnborn@gmail.com"
		message.to = user_address
		message.subject = "CheckNerds每日提醒 - " + str(datetime.date.today()) + " - " + str(DueTodayTotal) + "项事项"


		
		#CheckNerds 每日提醒，今日() 共有 项事项等待完成
		emailfooter = u"""
		---
		CheckNerds 在线个人事项管理，欢迎访问 <a href="http://www.checknerds.com">http://www.checknerds.com</a>

		"""

		template_values = {
				'PrefixCSSdir': "/",
				'UserNickName': "访客",
				'AnonymousVisitor': "Yes",

				'EmailTitle': message.subject,
				'ItemsDueToday':tarsusaItemCollection + tarsusaItem_DueToday,
 
			}
	
		path = os.path.join(os.path.dirname(__file__), 'pages/mail/dailybriefing.html')
		final_body = template.render(path, template_values)

		message.html = final_body  
		message.send()




	#mail.send_mail(sender_address, user_address, subject, final_body)


def main():
	application = webapp.WSGIApplication([('/cronmail', DailyBriefReport)],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
