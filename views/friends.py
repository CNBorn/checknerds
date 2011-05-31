# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename California
# - friends.py
# Copyright (C) CNBorn, 2008-2009
# http://cnborn.net, http://twitter.com/CNBorn
#
# **************************************************************** 

import os
import cgi
import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from models import *
from base import *
import memcache
import tarsusaCore


def user_loggingin(function):
    '''
    to check with UserLoggingIn
    '''
    def user_loggingin_warpper(tRequestHandler, *args, **kw):
        if tRequestHandler.chk_login():
            #CurrentUser = tRequestHadler.get_user_db()
            return function(tRequestHandler, *args, **kw)
        else:
            return tRequestHandler.redirect('/')
    return user_loggingin_warpper



class FindFriendPage(tarsusaRequestHandler):
    def get(self):
    
        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login():
            CurrentUser = self.get_user_db()

            ## SHOW YOUR FRIENDs Recent Activities
            UserFriendsItem_List = tarsusaCore.get_UserFriendStats(CurrentUser.key().id())

            tarsusaLatestPeople = tarsusaUser.get_latestusers()
            
            tarsusaUserFriendCollection = map(lambda each_FriendKey: db.get(each_FriendKey), CurrentUser.friends)
            
            template_values = {
                    'UserLoggedIn': 'Logged In',
                    
                    'UserNickName': cgi.escape(CurrentUser.dispname),
                    'UserID': CurrentUser.key().id(),
                    'UserFriends': tarsusaUserFriendCollection, 
                    'singlePageTitle': "查找朋友.",
                    'singlePageContent': "",
                    
                    'UserFriendsActivities': UserFriendsItem_List,
                    'tarsusaPeopleCollection': tarsusaLatestPeople,
            }
        
            path = os.path.join(os.path.dirname(__file__), 'pages/addfriend.html')
            self.response.out.write(template.render(path, template_values))

        else:
            ##if users.get_current_user() is None 
            #TODO   
            template_values = {
                    'UserLoggedIn': 'Logged In',
                    
                    'UserNickName': '', #cgi.escape(self.login_user.nickname()),
                    'UserID': '', #CurrentUser.key().id(),
                    'UserFriends': '', #UserFriends,    
                    'singlePageTitle': "查找朋友.",
                    'singlePageContent': "",

                    'tarsusaPeopleCollection': '', #tarsusaPeopleCollection,
            }   
            path = os.path.join(os.path.dirname(__file__), 'pages/welcome_friends.html')
            self.response.out.write(template.render(path, template_values))
            
            ## Prompt them to register!


class AddFriendProcess(tarsusaRequestHandler):
    '''Get? Handler to Add a New Friends
     to a User's friend list.'''

    # Permission check is very important.
    @user_loggingin
    def get(self):       
        ToBeAddedUserId = self.request.path[11:]
        ## Please be awared that ItemId here is a string!
        ToBeAddedUser = tarsusaUser.get_by_id(int(ToBeAddedUserId))

        ## Get Current User.
        CurrentUser = self.get_user_db()

        #I can use a reduct here.
        AlreadyAddedAsFriend = False
        for eachFriend in CurrentUser.friends:
            if eachFriend == ToBeAddedUser.key():
                AlreadyAddedAsFriend = True 


        if ToBeAddedUser.key() != CurrentUser.key() and AlreadyAddedAsFriend == False:
            CurrentUser.friends.append(ToBeAddedUser.key())
            CurrentUser.put()

        else:
            ## You can't add your self! and You can add a person twice!
            pass
        
        memcache.event('addfriend', CurrentUser.key().id())
        self.redirect('/FindFriend')


class RemoveFriendProcess(tarsusaRequestHandler):
    def get(self):
        
        # Permission check is very important.

        ToBeRemovedUserId = self.request.path[14:]
            ## Please be awared that ItemId here is a string!
        ToBeRemovedUser = tarsusaUser.get_by_id(int(ToBeRemovedUserId))

        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login():
            CurrentUser = self.get_user_db()


        AlreadyAddedAsFriend = False
        for eachFriend in CurrentUser.friends:
            if eachFriend == ToBeRemovedUser.key():
                AlreadyAddedAsFriend = True 


        if ToBeRemovedUser.key() != CurrentUser.key() and AlreadyAddedAsFriend == True:
            CurrentUser.friends.remove(ToBeRemovedUser.key())
            CurrentUser.put()

        else:
            ## You can't remove your self!
            ## and You can not remove a person that are not your friend!
            pass
        
        memcache.event('removefriend', CurrentUser.key().id())
        self.redirect('/FindFriend')


def main():
    application = webapp.WSGIApplication([('/AddFriend/\\d+', AddFriendProcess),
                                       ('/RemoveFriend/\\d+', RemoveFriendProcess),
                                       ('/FindFriend', FindFriendPage)],
                                       debug=True)

    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
