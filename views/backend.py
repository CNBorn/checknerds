# -*- coding: utf-8 -*-
#
# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename California
# - backend.py
# Copyright (C) CNBorn, 2008-2009
# http://cnborn.net, http://twitter.com/CNBorn
#
# Provides Backend Admin functions 
#
# **************************************************************** 
import urllib
import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from modules import *
from base import *

class colossus(tarsusaRequestHandler):
	'''
		#This is the first admin page for CheckNerds.
		#Admin page for managing all Applications that uses CheckNerds API.
	'''
	def get(self):
		#This is the first admin page for CheckNerds.
		#Admin page for managing all Applications that uses CheckNerds API.

		if self.chk_login() and users.is_current_user_admin() == True:
			CurrentUser = self.get_user_db()	
			AllAppModel = AppModel.all()
			#for each_AppModel in AllAppModel:
			#	self.write("Name:" + each_AppModel.name)

			template_values = {
				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(CurrentUser.dispname),
				'UserID': CurrentUser.key().id(),
				'PrefixCSSdir': "/",
	
				'singlePageTitle': "Admin for AppModel, codename Colossus",
				'AllAppModel': AllAppModel
			}

			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/colossus.html')
			strCachedWelcomePage = template.render(path, template_values)

			self.response.out.write(strCachedWelcomePage)


		else:
			#This User is not an admin.
			self.redirect("/")


	def post(self):
		#Get the Applied Information and record them into the DB.

		item_name = cgi.escape(self.request.get('name'))
		
		try:
			if len(self.request.get('comment'))>500:
				item_comment = cgi.escape(self.request.get('comment')[:500])
			else:
				item_comment = cgi.escape(self.request.get('comment'))
		except:
			item_comment = ''


		NewAppModel = AppModel(name=item_name, description=item_comment)
		
		apiuser = tarsusaUser.get_by_id(int(self.request.get('userid')))
		if apiuser != None:
			NewAppModel.usermodel = apiuser
		else:
			return 0 #Failed to add, without correct UserID

		#From Plog. '''Generate a random string for using as api password, api user is user's full email'''
		from random import sample
		from md5 import md5
		s = 'abcdefghijklmnopqrstuvwxyz1234567890'
		password = ''.join(sample(s, 8))
		NewAppModel.servicekey = md5(str(self.request.get('userid') + 'CheckNerdsAPIWelcomesYou' + password)).hexdigest()

		NewAppModel.put()

		self.redirect("/service/colossus/")
	


def main():
	application = webapp.WSGIApplication([
									   ('/backend/colossus.+', colossus)],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
