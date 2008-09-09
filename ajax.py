# -*- coding: utf-8 -*-

#from django.conf import settings
#settings._target = None
import os
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




class getdailyroutine(tarsusaRequestHandler):

	def post(self):
	
		if users.get_current_user() != None:

				# code below are comming from GAE example
				q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
				CurrentUser = q.get()

				# Show His Daily Routine.
				tarsusaItemCollection_DailyRoutine = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'daily' ORDER BY date DESC", users.get_current_user())

				tarsusaItemCollection_DoneDailyRoutine = tarsusaRoutineLogItem 


				# GAE datastore has a gqlquery.count limitation. So right here solve this manully.
				tarsusaItemCollection_DailyRoutine_count = 0
				for each_tarsusaItemCollection_DailyRoutine in tarsusaItemCollection_DailyRoutine:
					tarsusaItemCollection_DailyRoutine_count += 1

				Today_DoneRoutine = 0

				for each_tarsusaItemCollection_DailyRoutine in tarsusaItemCollection_DailyRoutine:
					
					#This query should effectively read out all dailyroutine done by today.
					#for the result will be traversed below, therefore it should be as short as possible.
					#MARK FOR FUTURE IMPROVMENT
					
					# GAE datastore has a gqlquery.count limitation. So right here solve this manully.
					#tarsusaItemCollection_DailyRoutine_count
					# Refer to code above.
					
					
					# LIMIT and OFFSET don't currently support bound parameters.
					# http://code.google.com/p/googleappengine/issues/detail?id=179
					# if this is realized, the code below next line will be used.

					tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC ", users.get_current_user(), each_tarsusaItemCollection_DailyRoutine.key().id())
					
					#tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC LIMIT :3", users.get_current_user(), each_tarsusaItemCollection_DailyRoutine.key().id(), int(tarsusaItemCollection_DailyRoutine_count))

					
					## traversed RoutineDaily
					
					## Check whether this single item is done.
					DoneThisItemToday = False
					
					for tarsusaItem_DoneDailyRoutine in tarsusaItemCollection_DoneDailyRoutine:
						if datetime.datetime.date(tarsusaItem_DoneDailyRoutine.donedate) == datetime.datetime.date(datetime.datetime.now()):
							#Check if the user had done all his routine today.
							Today_DoneRoutine += 1
							DoneThisItemToday = True

							# This routine have been done today.
							
							# Due to solve this part, I have to change tarsusaItemModel to db.Expando
							# I hope there is not so much harm for performance.
							each_tarsusaItemCollection_DailyRoutine.donetoday = 1
							each_tarsusaItemCollection_DailyRoutine.put()

						else:
							## The Date from RoutineLogItem isn't the same of Today's date
							## That means this tarsusaItem(as routine).donetoday should be removed.
								
							pass
					
					if DoneThisItemToday == False:
							## Problem solved by Added this tag. DoneThisItemToday
							try:
								del each_tarsusaItemCollection_DailyRoutine.donetoday
								each_tarsusaItemCollection_DailyRoutine.put()
							except:
								pass



				
				## Output the message for DailyRoutine
				template_tag_donealldailyroutine = ''
				
				if Today_DoneRoutine == int(tarsusaItemCollection_DailyRoutine_count) and Today_DoneRoutine != 0:
					template_tag_donealldailyroutine = '<img src="img/favb16.png">恭喜，你完成了今天要做的所有事情！'
				elif Today_DoneRoutine == int(tarsusaItemCollection_DailyRoutine_count) - 1:
					template_tag_donealldailyroutine = '只差一项，加油！'
				elif int(tarsusaItemCollection_DailyRoutine_count) == 0:
					template_tag_donealldailyroutine = '还没有添加每日计划？赶快添加吧！<br />只要在添加项目时，将“性质”设置为“每天要做的”就可以了！'


				template_values = {
				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(self.login_user.nickname()),
				'UserID': CurrentUser.key().id(),
				
				'tarsusaItemCollection_DailyRoutine': tarsusaItemCollection_DailyRoutine,
				'htmltag_DoneAllDailyRoutine': template_tag_donealldailyroutine,

				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 


				}


				#Manupilating Templates	
				path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_dailyroutine.html')
				self.response.out.write(template.render(path, template_values))






class get_fp_bottomcontents(tarsusaRequestHandler):

	def get(self):
	
		if users.get_current_user() != None:

			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()

			# Count User's Todos and Dones
			tarsusaItemCollection_UserItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' ORDER BY date DESC", users.get_current_user())

			# For Count number, It is said that COUNT in GAE is not satisfied and accuracy.
			# SO there is implemented a stupid way.
			UserTotalItems = 0
			UserToDoItems = 0
			UserDoneItems = 0

			UserDonePercentage = 0.00

			for eachItem in tarsusaItemCollection_UserItems:
				UserTotalItems += 1
				if eachItem.done == True:
					UserDoneItems += 1
				else:
					UserToDoItems += 1
			
			if UserTotalItems != 0:
				UserDonePercentage = UserDoneItems *100 / UserTotalItems 
			else:
				UserDonePercentage = 0.00



			## SPEED KILLER!
			## MULTIPLE DB QUERIES!
			## CAUTION! MODIFY THESE LATER!
			tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC LIMIT 5", users.get_current_user())
			tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True ORDER BY date DESC LIMIT 5", users.get_current_user())


			## SHOW YOUR FRIENDs Recent Activities
			## Currently the IN function is not supported, it is an headache.
			
			## first get current user. 
			## THIS LINES OF CODE ARE DUPLICATED.
			# code below are comming from GAE example
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
			CurrentUser = q.get()

			tarsusaUserFriendCollection = CurrentUser.friends
			
			tarsusaItemCollection_UserFriendsRecentItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC LIMIT 15", users.get_current_user)


			UserFriendsActivities = ''
			if tarsusaUserFriendCollection: 
				for each_FriendKey in tarsusaUserFriendCollection:
					UsersFriend =  db.get(each_FriendKey)
					## THE BELOW LINE IS UN SUPPORTED!
					#tarsusaItemCollection_UserFriendsRecentItems += db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC LIMIT 15", UsersFriend)
					## THERE are too many limits in GAE now...
					tarsusaItemCollection_UserFriendsRecentItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC LIMIT 2", UsersFriend.user)

					for tarsusaItem_UserFriendsRecentItems in tarsusaItemCollection_UserFriendsRecentItems:
						## Check whether should show this item.
						if tarsusaItem_UserFriendsRecentItems.public != 'private':
						
							## Check whether this item had done.
							if tarsusaItem_UserFriendsRecentItems.done == True:
								
								UserFriendsActivities += '<a href="/user/' + UsersFriend.user.nickname() + '">' +  UsersFriend.user.nickname() + '</a> Done <a href="/i/' + tarsusaItem_UserFriendsRecentItems.key().id() + '">' + tarsusaItem_UserFriendsRecentItems.name + '</a><br />'
	 
							else:
								UserFriendsActivities += '<a href="/user/' + UsersFriend.user.nickname() + u'">' + UsersFriend.user.nickname() + '</a> ToDO <a href="/i/' + str(tarsusaItem_UserFriendsRecentItems.key().id()) + '">' + tarsusaItem_UserFriendsRecentItems.name + '</a><br />'


			else:
				UserFriendsActivities = '当前没有添加朋友'

								

			template_values = {
				'UserLoggedIn': 'Logged In',
				
				'UserNickName': cgi.escape(self.login_user.nickname()),
				'UserID': CurrentUser.key().id(),
				
				'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 

				'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
				'tarsusaItemCollection_UserDoneItems': tarsusaItemCollection_UserDoneItems,


				'UserFriendsActivities': UserFriendsActivities,

				'UserTotalItems': UserTotalItems,
				'UserToDoItems': UserToDoItems,
				'UserDoneItems': UserDoneItems,
				'UserDonePercentage': UserDonePercentage,
			}


			#Manupilating Templates	
			path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_bottomcontents.html')
			self.response.out.write(template.render(path, template_values))
	
	

class ajax_error(tarsusaRequestHandler):

	def post(self):

		self.write("载入出错，请刷新重试")







#user = check_api_user_pass(username, password)
#	if not user:
#		raise Exception, 'access denied'
#
#	post = Post.get_by_id(int(postid))
#
#	return {
#			'postid' : postid,
#			'dateCreated' : post.date,
#			'title' : post.title,
#			'description' : unicode(post.content),
#			'categories' : post.tags,
#			'publish' : True,
#			}
#
#



def main():
	application = webapp.WSGIApplication([('/ajax/frontpage_getdailyroutine', getdailyroutine),
										('/ajax/frontpage_bottomcontents', get_fp_bottomcontents),
									   ('.*',ajax_error)],
                                       debug=True)


	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
