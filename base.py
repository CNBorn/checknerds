from google.appengine.ext import webapp
from google.appengine.api import users

from modules import *
import cgi

# {{{ Base class
class tarsusaRequestHandler(webapp.RequestHandler):
	def __init__(self):
		pass

	def initialize(self, request, response):
		webapp.RequestHandler.initialize(self, request, response)
		
		self.login_user = users.get_current_user()
		self.is_login = (self.login_user != None)
		
		if self.is_login:
			self.user = tarsusaUser.all().filter('user = ', self.login_user).get() or tarsusaUser(user = self.login_user)
		else:
			self.user = None

		try:
			self.referer = self.request.headers['referer']
		except:
			self.referer = None

	def param(self, name, **kw):
		return self.request.get(name, **kw)

	def write(self, s):
		self.response.out.write(s)

	def get_login_url(self, from_referer=False):
		if from_referer:
			dst = self.referer
			if not dst : dst = '/m'
			return users.create_login_url(dst)
		else:
			return users.create_login_url(self.request.uri)

	def get_logout_url(self, from_referer=False):
		if from_referer:
			dst = self.referer
			if not dst : dst = '/m'
			return users.create_logout_url(dst)
		else:
			return users.create_logout_url(self.request.uri)
	
	def chk_login(self, redirect_url='/'):
		self.login_user = users.get_current_user()
		self.is_login = (self.login_user != None)

		if self.is_login:
			# added register code here
			CurrentUser = self.get_user_db()
			
			if CurrentUser == None:
				# Create a User
				CurrentUser = tarsusaUser(user=users.get_current_user(), urlname=cgi.escape(users.get_current_user().nickname()))
				CurrentUser.put()

				## Added userid property.
				CurrentUser.userid = CurrentUser.key().id()
				CurrentUser.dispname = users.get_current_user().nickname()
				CurrentUser.put()
			
			else:
				## DB Model Patch
				## These code for registered user whose information are not fitted into the new model setting.
				
				#Run DB Model Patch	when User Logged in.
				#DBPatcher.chk_dbmodel_update(CurrentUser)
				#Run this at every ViewItem event

				## Added userid here.
				if CurrentUser.userid == None:
					CurrentUser.userid = CurrentUser.key().id()
					CurrentUser.put()					
			
			return True
		else:
			#self.redirect(redirect_url)
			return False

	def get_user_db(self):
		q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
		return q.get()

	def verify_api(self):
		import modules
		import tarsusaCore, memcache
		import logging
				
		#Verifiction of external API calls.
		#Verify the AppModel first.
		
		apiappid = self.request.get('apiappid') 
		apiservicekey = self.request.get('servicekey')
		
		if apiappid == "" or apiservicekey == "":
			self.write("403 Not enough parameters.")
			return False 
		
		#logging.info(apiservicekey)		
		
		verified = tarsusaCore.verify_AppModel(int(apiappid), apiservicekey)
		
		apiuserid = self.request.get('apiuserid') 
		apikey = self.request.get('apikey')
		userid = self.request.get('userid')
		
		APIUser = tarsusaUser.get_by_id(int(apiuserid))
		
		#Exception.
		if APIUser == None:
			self.write("403 No Such User")
			#self.error(403)
			return False
		if verified == False:
			self.write("403 Application Verifiction Failed.")
			#self.error(403)
			return False
		#--- verified AppApi Part.
		if tarsusaCore.verify_UserApi(int(apiuserid), apikey) == False:
			self.write("403 UserID Authentication Failed.")
			return False
		
		try:
			if APIUser.apikey == None:
				return False
		except:
			return False

		return True

	def verify_api_limit(self):
		import modules
		import tarsusaCore, memcache
		import logging
		
		#Check with API Usage.
		apiappid = self.request.get('apiappid') 
		apiservicekey = self.request.get('servicekey')
	
		AppApiUsage = memcache.get_item("appapiusage", int(apiappid))
		ThisApp = AppModel.get_by_id(int(apiappid))
		if ThisApp == None:
			self.write("404 Application does not exist.")
			return False
		
		if AppApiUsage >= ThisApp.api_limit:
			#Api Limitation exceed.
			self.write('403 API Limitation exceed. ')
			return False	
		elif AppApiUsage == None: #memcache.get_item returns None if there is not such var.
			AppApiUsage = 0
		
		AppApiUsage += 1 
		memcache.set_item("appapiusage", AppApiUsage, int(apiappid))
		
		return True

	def response_status(self, status_code, status_info=None, return_value=False):
		'''
		Set the response status & its info, and return the specify result state
		mainly used in service.py, sample usage:
			return self.response_status(404, 'No such Item', False) 
			#This line returns False, because of the third para in the function
		'''
		self.response.set_status(status_code)
		self.write(status_info)
		return return_value


## These 2 below functions are derived from Plog.
##
## Now Tag is a new type of model 

def split_tags(s):
	tags = list(set([t.strip() for t in re.split('[,;\\/\\\\]*', s) if t != ''])) #uniq
	return tags

def update_tag_count(old_tags = None, new_tags = None):
	if old_tags == None and new_tags == None:
		tags = []
		posts = Post.all()
		for post in posts:
			tags += post.tags
		tags_set = set(tags)
		for tag in tags_set:
			t = Tag.all().filter('name = ', tag).get()
			if t:
				t.count = tags.count(tag)
			else:
				t = Tag(name = tag, count = tags.count(tag))

			t.put()

	else:
		added = [t for t in new_tags if not t in old_tags]
		deleted = [t for t in old_tags if not t in new_tags]

		for tag in added:
			t = Tag.all().filter('name = ', tag).get()
			if t:
				t.count = t.count + 1
			else:
				t = Tag(name = tag, count = 1)

			t.put()

		for tag in deleted:
			t = Tag.all().filter('name = ', tag).get()
			if t:
				t.count = t.count - 1
				if t.count == 0:
					t.delete()
				else:
					t.put()
			else:
				t = Tag(name = tag, count = 1)
				t.put()

## Import this function from tarsusa R6

def printExpireTimeGap(timeOne,timeTwo):
	ReturnString = ''
	
	#My Original Design, Returning a list with ReturnString in [0] and the following is Days Hours Minutes Seconds...
	#ReturnList = []
	if str(timeTwo - timeOne).find(" days,") <> -1:
		#Projects has more than two days.
		WorkString = str(timeTwo - timeOne).split(" days,",1)
		TimeString = WorkString[1].split(":")

	elif str(timeTwo - timeOne).find(" day,") <> -1:
		#Projects has more than one day.
		WorkString = str(timeTwo - timeOne).split("day,",1)
		TimeString = WorkString[1].split(":")

	else:
		#Projects has less than one day.
		TimeString = str(timeTwo - timeOne).split(":")
		if str(timeTwo - timeOne)[0] == "-":
			WorkString = ['-0']
		else:
			WorkString = ['0']

	if WorkString[0][0] == "-":
		ReturnString = "Past" + WorkString[0][1:] + "Days" + TimeString[0] + "Hours" + TimeString[1] + "Mins"
	else:		
		ReturnString = "To GO " + WorkString[0] + "Days" + TimeString[0] + "Hours" + TimeString[1] + "Mins"
	return ReturnString


## Used for API setting.

global_vars = {}
global_vars['apilimit'] = 400

