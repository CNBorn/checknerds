# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename California
# - ErrorPages.py
# Author: CNBorn, 2008-2009
# http://cnborn.net, http://twitter.com/CNBorn
#
# Handles the error pages.
#
# **************************************************************** 
import cgi
import wsgiref.handlers
from google.appengine.ext.webapp import template

from modules import *
from base import *

import os

class Error404(tarsusaRequestHandler):
	def get(self):
		# New CheckLogin code built in tarsusaRequestHandler 
		self.error(404)
		if self.chk_login():
			CurrentUser = self.get_user_db()		
			template_values = {
					'UserLoggedIn': 'Logged In',
					'UserNickName': cgi.escape(CurrentUser.dispname),
					'UserID': CurrentUser.key().id(),
			}
		
		else:			
			template_values = {
				'UserNickName': "访客",
				'AnonymousVisitor': "Yes",
			}

		#Manupilating Templates	
		path = os.path.join(os.path.dirname(__file__), 'pages/error_404.html')
		self.response.out.write(template.render(path, template_values))	

def main():
	application = webapp.WSGIApplication([('/.*', Error404)]
									   , debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
