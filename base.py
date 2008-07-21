from google.appengine.ext import webapp
from google.appengine.api import users

from modules import *


# {{{ Base class
class tarsusaRequestHandler(webapp.RequestHandler):
	def __init__(self):
		pass

	def initialize(self, request, response):
		webapp.RequestHandler.initialize(self, request, response)

		self.login_user = users.get_current_user()
		self.is_login = (self.login_user != None)
		if self.is_login:
			self.user = User.all().filter('user = ', self.login_user).get() or User(user = self.login_user)
		else:
			self.user = None

		self.is_admin = users.is_current_user_admin()
		if self.is_admin:
			self.auth = 'admin'
		elif self.is_login:
			self.auth = 'login'
		else:
			self.auth = 'guest'

		#self.widget = Widget(self)
		#self.theme = global_vars['theme']

		try:
			self.referer = self.request.headers['referer']
		except:
			self.referer = None


	def param(self, name, **kw):
		return self.request.get(name, **kw)

	def write(self, s):
		self.response.out.write(s)


	def get_login_url(self, from_referer=False):
		#if from_referer:
		#	dst = self.referer
		#	if not dst : dst = '/blog/'
		#	return users.create_login_url(dst)
		#else:
		return users.create_login_url(self.request.uri)

	def get_logout_url(self, from_referer=False):
		if from_referer:
			dst = self.referer
			if not dst : dst = '/blog/'
			return users.create_logout_url(dst)
		else:
			return users.create_logout_url(self.request.uri)




	
	def chk_login(self, redirect_url='/'):
		if self.is_login:
			return True
		else:
			self.redirect(redirect_url)
			return False

	def chk_admin(self, redirect_url='/'):
		if self.is_admin:
			return True
		else:
			self.redirect(redirect_url)
			return False
