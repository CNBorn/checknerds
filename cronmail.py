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

class ConfirmUserSignup(tarsusaRequestHandler):
  def get(self):
	user_address = "cnborn@gmail.com"

	if not mail.is_email_valid(user_address):
		# prompt user to enter a valid address
		print 'error'
		pass

	else:
		#confirmation_url = createNewUserConfirmation(self.request)
		if self.chk_login():
			CurrentUser = self.get_user_db()

		tarsusaItemCollection = tarsusaCore.get_dailyroutine(CurrentUser.key().id())
	
		strABC = ''
		for eachItem in tarsusaItemCollection:
			strABC += eachItem.name

		confirmation_url  = "url"
		sender_address = "cnborn@gmail.com"
		subject = strABC# + " registration"
		body = """
Thank you for creating an account!  Please confirm your email address by
clicking on the link below:

%s
""" 
	mail.send_mail(sender_address, user_address, subject, body)


def main():
	application = webapp.WSGIApplication([('/cronmail', ConfirmUserSignup)],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
