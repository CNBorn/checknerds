# -*- coding: utf-8 -*-
#
# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename California
# - service.py
# Copyright (C) CNBorn, 2008-2009
# http://cnborn.net, http://twitter.com/CNBorn
#
# Provides API functions 
#
# **************************************************************** 
import urllib
import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext import search
from google.appengine.ext.webapp import template
from modules import *
from base import *


import time, datetime
import os

import tarsusaCore
import memcache

import logging

class colossus(tarsusaRequestHandler):
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

class badge(tarsusaRequestHandler):
	def get(self):
		
		#http://localhost:8080/service/badge/?userid=42&callback=miniblog
		userid = urllib.unquote(self.request.get('userid'))
		callbackfuncname = urllib.unquote(self.request.get('callback'))
		ThisUser = tarsusaUser.get_by_id(int(userid))
		
		tarsusaItemCollection_CreatedItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and public = 'public' ORDER BY date DESC LIMIT 5", ThisUser.user)	
		tarsusaItemCollection_DoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and public = 'public' and done = True ORDER BY donedate DESC LIMIT 5", ThisUser.user)	
		
		CreatedItem_List = []
		for each_CreatedItem in tarsusaItemCollection_CreatedItems:
			created_item = {'id' : str(each_CreatedItem.key().id()), 'name' : each_CreatedItem.name, 'date' : str(each_CreatedItem.date), 'comment' : each_CreatedItem.comment, 'category' : 'todo'}
			CreatedItem_List.append(created_item)
		
		DoneItem_List = []
		for each_DoneItem in tarsusaItemCollection_DoneItems:
			done_item = {'id' : str(each_DoneItem.key().id()), 'name' : each_DoneItem.name, 'date' : str(each_DoneItem.date), 'comment' : each_DoneItem.comment, 'category' : 'done'}
			DoneItem_List.append(done_item)
		
		#Output = created_item + done_item
		ItemCount = 0
		

		#Sort Algorithms from 
		#http://www.lixiaodou.cn/?p=12
		test_list=CreatedItem_List + DoneItem_List
		
		length = len(test_list)
		for i in range(0,length):
			for j in range(length-1,i,-1):
					#Convert string to datetime.date
					#http://mail.python.org/pipermail/tutor/2006-March/045729.html	
					time_format = "%Y-%m-%d %H:%M:%S"
					if datetime.datetime.fromtimestamp(time.mktime(time.strptime(test_list[j]['date'][:-7], time_format))) > datetime.datetime.fromtimestamp(time.mktime(time.strptime(test_list[j-1]['date'][:-7], time_format))):
						temp = test_list[j]
						test_list[j]=test_list[j-1]
						test_list[j-1]=temp
		#return list
		self.response.headers['Content-Type'] = 'application/json'
		self.response.headers['Content-Disposition'] = str('attachment; filename=' + callbackfuncname)
		self.write(callbackfuncname + '(')
		#self.write(str(test_list)[1:-1])
		self.write(str(test_list))
		self.write(')')

		#for each in CreatedItem_List:
			#self.write(each['date'])
			#timestring = "2005-09-01 12:30:09"
			#time_format = "%Y-%m-%d %H:%M:%S"
			#actul_time = datetime.datetime.fromtimestamp(time.mktime(time.strptime(each['date'][:-7], time_format)))
			#self.write(actul_time)
				
			#Show ordinary items that are created in that day
			#TheDay = actul_time
			#TheDay = DoneDateOfThisItem
			#one_day = datetime.timedelta(days=1)
			#yesterday_ofTheDay = TheDay - one_day						
			#yesterday_ofTheDay = datetime.datetime.combine(TheDay - one_day,datetime.time(0))
			#nextday_ofTheDay = TheDay + one_day
			#nextday_ofTheDay = datetime.datetime.combine(TheDay + one_day, datetime.time(0))

			#DoneDateOfThisItem = datetime.datetime.date(each_RoutineLogItem.donedate)
			#Donedate_of_previousRoutineLogItem = DoneDateOfThisItem 

			#ItemCount += 1
		
		
		#self.response.out.write(simplejson.dumps(Output))
		#self.write(Output)

class patch_error(tarsusaRequestHandler):
	def get(self):
		self.redirect('/')
		
class api_getuser(tarsusaRequestHandler):
	
	#First CheckNerds API: Get User information.

	def get(self):
		self.write('<h1>please use POST</h1>')
	
	def post(self):
		#Verify the AppModel first.
		apiappid = self.request.get('apiappid') 
		apiservicekey = self.request.get('servicekey')
		logging.info(apiservicekey)
		verified = tarsusaCore.verify_AppModel(int(apiappid), apiservicekey)
		
		apiuserid = self.request.get('apiuserid') 
		apikey = self.request.get('apikey')
		userid = self.request.get('userid')
		
		APIUser = tarsusaUser.get_by_id(int(apiuserid))
		
		#Exception.
		if APIUser == None:
			self.write("403 No Such User")
			#self.error(403)
			return 0
		if verified == False:
			self.write("403 Application Verifiction Failed.")
			#self.error(403)
			return 0
		#--- verified AppApi Part.
		if tarsusaCore.verify_UserApi(int(apiuserid), apikey) == False:
			self.write("403 UserID Authentication Failed.")
			return 0
 
		if verified == True and APIUser.apikey != None:
			#Should use log to monitor API usage.
			#Also there should be limitation for the apicalls/per hour.

			ThisUser = tarsusaUser.get_by_id(int(userid))
			user_info = {'id' : str(ThisUser.key().id()), 'name' : ThisUser.dispname, 'datejoinin' : str(ThisUser.datejoinin), 'website' : ThisUser.website, 'avatar' : 'http://www.checknerds.com/image?avatar=' + str(ThisUser.key().id())}
			
			self.write(user_info)
		elif APIUser.apikey == None:
			self.write('APIKEY is not generated.')

#APIs to be added:
#	AddItem, DoneItem, UndoneItem, GetDailyRoutineItem, GteUserPublicItem, GetUserTodoItem, GetUserDoneItem, GetUserItem
#	

class api_getuseritem(tarsusaRequestHandler):
	
	#CheckNerds API: Get User Items.
	#Parameters: apiuserid, apikey, userid, routine, public, maxitems

	def get(self):
		self.write('<h1>please use POST</h1>')
	
	def post(self):
		#self.write(self.request.body)
		apiuserid = self.request.get('apiuserid') 
		apikey = self.request.get('apikey')

		userid = self.request.get('userid')

		done = self.request.get('done')
		if done == 'True':
			done = True
		elif done == 'False':
			done = False
		else:
			done = None

		routine = self.request.get('routine')
		if routine == '':
			routine='none'
		
		logging.info(routine)
		#!!!!!
		#Below Settings should be changed 
		#When user can check other users ITEMs!
		#
		public = self.request.get('public')
		if public == '':
			public = 'none'
			#'none' means it doesn't matter, display all items.
		logging.info(public)
		
		maxitems = self.request.get('maxitems')
		if maxitems == None or maxitems == '':
			count = 10
		else:
			count = int(maxitems)
			if count > 100:
				count = 100
		logging.info(maxitems)
		
		'''
			startdate='',
			enddate='',
			startdonedate=''
			enddonedate=''
		'''

		APIUser = tarsusaUser.get_by_id(int(apiuserid))
		if apikey == APIUser.apikey and APIUser.apikey != None:
			if apiuserid == userid:
				#Get APIUser's Items
				
				#It can only get todo or done items.
				tarsusaItemCollection_UserDoneItems = tarsusaCore.get_tarsusaItemCollection(userid, done=done, routine=routine, maxitems=count, public=public)
				self.write(tarsusaItemCollection_UserDoneItems)	
			else:
				#Get Other Users Items
				self.write('<h1>Currently You can\'t get other user\'s items.</h1>')
		else:
			self.write('<h1>Authentication failed.</h1>')

class api_doneitem(tarsusaRequestHandler):
	
	#CheckNerds API: DoneItem.
	#Parameters: apiuserid, apikey, itemid

	def get(self):	
		self.write('<h1>please use POST</h1>')

	def post(self):
		
		apiuserid = self.request.get('apiuserid') 
		apikey = self.request.get('apikey')

		#Check with API Usage.
		UserApiUsage = memcache.get_item("userapiusage", int(apiuserid))
		if UserApiUsage >= global_vars['apilimit']:
			#Api Limitation exceed.
			self.write('<h1>API Limitation exceed.</h1>')
			return False
		else:	
			#Actual function.
			itemid = self.request.get('itemid')
			APIUser = tarsusaUser.get_by_id(int(apiuserid))
			ThisItem = tarsusaItem.get_by_id(int(itemid))
			if apikey == APIUser.apikey and APIUser.apikey != None:
				if int(apiuserid) == ThisItem.usermodel.key().id():
					#Get APIUser's Items
					Misc = ''
					#Misc could be set to 'y' to done a yesterday's routineitem
					self.write(tarsusaCore.DoneItem(itemid, apiuserid, Misc))
					#Should be 200 status in future, currently just 0(success), 1(failed)

					#------------------------
					#Manipulating API calls count.
					if UserApiUsage	== None:
						UserApiUsage = 0
					UserApiUsage += 5 #For this is a write action.
					memcache.set_item("userapiusage", UserApiUsage, int(apiuserid))
					#------------------------

				else:
					#Get Other Users Items
					self.write('<h1>Currently You can\'t manipulate other user\'s items.</h1>')
			else:
				self.write('<h1>Authentication failed.</h1>')

class api_undoneitem(tarsusaRequestHandler):
	
	#CheckNerds API: UndoneItem.
	#Parameters: apiuserid, apikey, itemid

	def get(self):	
		self.write('<h1>please use POST</h1>')

	def post(self):
		
		apiuserid = self.request.get('apiuserid') 
		apikey = self.request.get('apikey')

		#Check with API Usage.
		UserApiUsage = memcache.get_item("userapiusage", int(apiuserid))
		if UserApiUsage >= global_vars['apilimit']:
			#Api Limitation exceed.
			self.write('<h1>API Limitation exceed.</h1>')
			return False
		else:	
			#Actual function.
			itemid = self.request.get('itemid')
		
			APIUser = tarsusaUser.get_by_id(int(apiuserid))
			ThisItem = tarsusaItem.get_by_id(int(itemid))
			if apikey == APIUser.apikey and APIUser.apikey != None:
				if int(apiuserid) == ThisItem.usermodel.key().id():
					#Get APIUser's Items
					Misc = ''
					#Misc could be set to 'y' to done a yesterday's routineitem
					self.write(tarsusaCore.UndoneItem(itemid, apiuserid, Misc))
					#Should be 200 status in future, currently just 0(success), 1(failed)

					#------------------------
					#Manipulating API calls count.
					if UserApiUsage	== None:
						UserApiUsage = 0
					UserApiUsage += 5 #For this is a write action.
					memcache.set_item("userapiusage", UserApiUsage, int(apiuserid))
					#------------------------

				else:
					#Get Other Users Items
					self.write('<h1>Currently You can\'t manipulate other user\'s items.</h1>')
			else:
				self.write('<h1>Authentication failed.</h1>')

def main():
	application = webapp.WSGIApplication([
									   ('/service/user.+', api_getuser),
									   ('/service/item.+', api_getuseritem),
									   ('/service/done.+', api_doneitem),
									   ('/service/undone.+', api_undoneitem),
									   ('/service/badge.+', badge),
									   ('/service/colossus.+', colossus),
									   ('/patch/.+',patch_error)],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
