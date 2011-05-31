# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 0.7, codename Nevada
# - search.py
# Copyright (C) CNBorn, 2008
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn
#
# 
#
#
# **************************************************************** 
import urllib
import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext import search
from models import *
from base import *

class search(tarsusaRequestHandler):
	def get(self):
		if not self.chk_login():
			self.redirect('/')
		
		self.response.headers['Content-Type'] = 'text/plain'
	
		#RequestItemId = urllib.unquote(self.request.get['keyword'])
		#self.write(RequestItemId)
		self.write(self.request.get['keyword'])
		keyword = self.request.get['keyword']
		
		# Search the 'Person' Entity based on our keyword
		query = search.SearchableQuery('tarsusaItem')
		query.Search(keyword)
		for result in query.Run():
			#self.response.out.write('%s' % result)
			self.write(result)

class patch_error(tarsusaRequestHandler):
	def get(self):
		self.redirect('/')
		

def main():
	application = webapp.WSGIApplication([('/search/.+', search),
									   ('/patch/.+',patch_error)],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
