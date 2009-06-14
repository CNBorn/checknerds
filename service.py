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
from modules import *
from base import *


import time, datetime

import tarsusaCore

import logging
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
		#self.write(self.request.body)
		apiuserid = self.request.get('apiuserid') 
		apikey = self.request.get('apikey')

		userid = self.request.get('userid')
		
		APIUser = tarsusaUser.get_by_id(int(apiuserid))
		if apikey == APIUser.apikey and APIUser.apikey != None:

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


def main():
	application = webapp.WSGIApplication([
									   ('/service/user.+', api_getuser),
									   ('/service/item.+', api_getuseritem),
									   ('/service/badge.+', badge),
									   ('/patch/.+',patch_error)],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
