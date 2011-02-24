# -*- coding: utf-8 -*-

# ************************************************************* 
# CheckNerds - www.checknerds.com
# version 1.1, codename California
# - ajax.py
# Author: CNBorn, 2008-2010
# http://cnborn.net, http://twitter.com/CNBorn
# ************************************************************* 

import os
import cgi
import datetime
import wsgiref.handlers
import urllib
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

from google.appengine.ext.webapp import template
from django.utils import simplejson

from modules import *
from base import *
import logging

import tarsusaCore
from tarsusaCore import format_done_logs
import memcache
from models.user import get_user

def userloggedin_or_403(function):
    '''
    Decorator:
        to check with UserLoggingIn
    '''
    def user_loggedin_warpper(tRequestHandler, *args, **kw):
        if tRequestHandler.chk_login():
            #CurrentUser = tRequestHadler.get_user_db()
            return function(tRequestHandler, *args, **kw)
        else:
        	return tRequestHandler.response_status(403,'You are not logged in.',False)
    return user_loggedin_warpper

class getdailyroutine_yesterday(tarsusaRequestHandler):
    def post(self):
        
        if self.chk_login():
            CurrentUser = self.get_user_db()
        else:
            self.redirect('/')

        cachedUserDailyroutineYesterday = memcache.get_item("dailyroutine_yesterday", CurrentUser.key().id())
        if cachedUserDailyroutineYesterday is not None:
            strcachedUserDailyroutineYesterday = cachedUserDailyroutineYesterday
        else:   
            # Show His Daily Routine.
            tarsusaItemCollection_DailyRoutine = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'daily' ORDER BY date DESC", users.get_current_user())
            tarsusaItemCollection_DoneDailyRoutine = tarsusaRoutineLogItem 

            # GAE datastore has a gqlquery.count limitation. So right here solve this manully.
            tarsusaItemCollection_DailyRoutine_count = 0
            for each_tarsusaItemCollection_DailyRoutine in tarsusaItemCollection_DailyRoutine:
                tarsusaItemCollection_DailyRoutine_count += 1

            Yesterday_DoneRoutine = 0

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

                #TODO: should add a time limitation to easier this query.
                tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC ", users.get_current_user(), each_tarsusaItemCollection_DailyRoutine.key().id())
                
                ## traversed RoutineDaily
                
                ## Check whether this single item is done.
                DoneThisItemYesterday = False
                
                for tarsusaItem_DoneDailyRoutine in tarsusaItemCollection_DoneDailyRoutine:
                    if datetime.datetime.date(tarsusaItem_DoneDailyRoutine.donedate) == datetime.datetime.date(datetime.datetime.now() - datetime.timedelta(days=1)):
                        
                        #Check if the user had done all his routine today.
                        Yesterday_DoneRoutine += 1
                        DoneThisItemYesterday = True

                        # This routine have been done today.
                        
                        # Due to solve this part, I have to change tarsusaItemModel to db.Expando
                        # I hope there is not so much harm for performance.
                        each_tarsusaItemCollection_DailyRoutine.doneyesterday = 1
                        each_tarsusaItemCollection_DailyRoutine.put()

                    else:
                        ## The Date from RoutineLogItem isn't the same of Today's date
                        ## That means this tarsusaItem(as routine).donetoday should be removed.
                            
                        pass
                
                if DoneThisItemYesterday == False:
                        ## Problem solved by Added this tag. DoneThisItemYesterday
                        try:
                            del each_tarsusaItemCollection_DailyRoutine.doneyesterday
                            each_tarsusaItemCollection_DailyRoutine.put()
                        except:
                            pass

            ## Output the message for DailyRoutine
            template_tag_donealldailyroutine = ''
            
            if Yesterday_DoneRoutine == int(tarsusaItemCollection_DailyRoutine_count) and Yesterday_DoneRoutine != 0:
                template_tag_donealldailyroutine = '<img src="img/favb16.png">恭喜，你完成了昨天要做的所有事情！'
            elif Yesterday_DoneRoutine == int(tarsusaItemCollection_DailyRoutine_count) - 1:
                template_tag_donealldailyroutine = '只差一项，加油！'
            elif int(tarsusaItemCollection_DailyRoutine_count) == 0:
                template_tag_donealldailyroutine = '还没有添加每日计划？赶快添加吧！<br />只要在添加项目时，将“性质”设置为“每天要做的”就可以了！'

            template_values = {
            'UserLoggedIn': 'Logged In',
            'UserNickName': cgi.escape(CurrentUser.dispname),
            'UserID': CurrentUser.key().id(),
            'tarsusaItemCollection_DailyRoutine': tarsusaItemCollection_DailyRoutine,
            'htmltag_DoneAllDailyRoutine': template_tag_donealldailyroutine,
            'htmltag_today': datetime.datetime.date(datetime.datetime.now() - datetime.timedelta(days=1)), 
            }

            #Manupilating Templates 
            path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_dailyroutine_yesterday.html')
            strcachedUserDailyroutineYesterday = template.render(path, template_values)
            memcache.set_item("dailyroutineyesterday", strcachedUserDailyroutineYesterday, CurrentUser.key().id())
        
        self.response.out.write(strcachedUserDailyroutineYesterday)



class get_fp_bottomcontents(tarsusaRequestHandler):
    '''用户登录后，下方的已完成和未完成事项列表'''

    ##Constantly Encountering 405 Error:
    ##Thanks for BenBen's solution: http://www.119797.com/program/gae-405/
    def head(self, *args):
        return self.get(*args)
        
    @userloggedin_or_403
    def get(self):
        CurrentUser = self.get_user_db()
        cachedUserItemlist = memcache.get_item("itemlist", CurrentUser.key().id())

        if cachedUserItemlist is not None:
            strcachedUserItemlist = cachedUserItemlist
        else:   
            tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC LIMIT 6", users.get_current_user())
            tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True ORDER BY donedate DESC LIMIT 6", users.get_current_user())                                    

            template_values = {
                'UserLoggedIn': 'Logged In',
                'UserNickName': cgi.escape(CurrentUser.dispname),
                'UserID': CurrentUser.key().id(),
                'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
                'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
                'tarsusaItemCollection_UserDoneItems': tarsusaItemCollection_UserDoneItems,
            }

            #Manupilating Templates 
            path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_bottomcontents.html')
            strcachedUserItemlist = template.render(path, template_values)  
            memcache.set_item("itemlist", strcachedUserItemlist, CurrentUser.key().id())
            
        self.response.out.write(strcachedUserItemlist)


class additem(tarsusaRequestHandler):
    def get(self):

        urllen = len('/ajax/allpage_additem/')
        RequestCatName = urllib.unquote(self.request.path[urllen:])
        user = users.get_current_user() 
        
        if user:
            if RequestCatName != '':
                strAddItemCatName = str(RequestCatName)
            else:
                strAddItemCatName = ''

            strAddItemToday = str(datetime.datetime.date(datetime.datetime.now()))

        
            template_values = {
                'addItemCatName': strAddItemCatName.decode("utf-8"),
                'addItemToday': strAddItemToday.decode("utf-8"),
            }

            #Manupilating Templates 
            path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_additem.html')
            self.response.out.write(template.render(path, template_values))
    
        else:
            self.write("您必须登录才可以添加条目，利用Google帐户登录，十分方便快捷，立即开始吧")


class edititem(tarsusaRequestHandler):
    def get(self):

        urllen = len('/ajax/allpage_edititem/')
        RequestItemId = urllib.unquote(self.request.path[urllen:])
        user = users.get_current_user() 
    
        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login():
            CurrentUser = self.get_user_db()
        
        tItem = tarsusaItem.get_by_id(int(RequestItemId))
    
        if tItem.user == users.get_current_user():
            
            ## Handle Tags
            # for modified Tags (db.key)
            tItemTags = ''
            try:
                for each_tag in db.get(tItem.tags):
                    if tItemTags == '':
                        tItemTags += cgi.escape(each_tag.name)
                    else:
                        tItemTags += ',' + cgi.escape(each_tag.name)
            except:
                # There is some chances that ThisItem do not have any tags.
                pass    
            
            try:
                tItemExpectdate = datetime.datetime.date(tItem.expectdate)
            except:
                tItemExpectdate = None
            
            try:

                template_values = {
                    'tItemId': tItem.key().id(),
                    'tItemName': cgi.escape(tItem.name),
                    'tItemComment': cgi.escape(tItem.comment),
                    'tItemTag': tItemTags,
                    'tItemRoutine': tItem.routine,
                    'tItemExpectdate': tItemExpectdate, 
                    'tItemPublic': tItem.public,
                    }           

                #Manupilating Templates 
                path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_edititem.html')
                self.response.out.write(template.render(path, template_values))

            except:
                ## GAE Localhost Environment
                template_values = {
                    'tItemId': tItem.key().id(),
                    'tItemName': cgi.escape(tItem.name.encode('utf-8')),
                    'tItemComment': cgi.escape(tItem.comment.encode('utf-8')),
                    'tItemTag': tItemTags.encode('utf-8'),
                    'tItemRoutine': tItem.routine,
                    'tItemExpectdate': tItemExpectdate,
                    'tItemPublic': tItem.public,
                    }           

                #Manupilating Templates 
                path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_edititem.html')
                self.response.out.write(template.render(path, template_values)) 

        else:
            self.write("您没有登录或没有权限编辑该项目")


class getjson_userdoneitems(tarsusaRequestHandler):
    '''JSON - 用户已完成事项'''

    @userloggedin_or_403
    def get(self):
        UserDoneItems = []
        CurrentUser = self.get_user_db()
        tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True ORDER BY date DESC", users.get_current_user())
        for UserDoneItem in tarsusaItemCollection_UserDoneItems:
            item = {'id' : str(UserDoneItem.key().id()), 'name' : UserDoneItem.name, 'date' : str(UserDoneItem.date), 'comment' : UserDoneItem.comment}
            UserDoneItems.append(item)
        
        self.response.out.write(simplejson.dumps(UserDoneItems))


class getjson_usertodoitems(tarsusaRequestHandler):
    '''JSON - 用户未完成事项'''

    @userloggedin_or_403
    def get(self):
        UserTodoItems = []
        CurrentUser = self.get_user_db()
        
        tarsusaItemCollection_UserTodoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC", users.get_current_user())
        for UserTodoItem in tarsusaItemCollection_UserTodoItems:
            item = {'id' : str(UserTodoItem.key().id()), 'name' : UserTodoItem.name, 'date' : str(UserTodoItem.date), 'comment' : UserTodoItem.comment}
            UserTodoItems.append(item)
        
        self.response.out.write(simplejson.dumps(UserTodoItems))
            
class ajax_error(tarsusaRequestHandler):
    def post(self):
        self.write("载入出错，请刷新重试")
    def get(self):
        self.write("载入出错，请刷新重试")

class get_fp_IntroductionBottomForAnonymous(tarsusaRequestHandler):
    
    def get(self):
        ## Homepage for Non-Registered Users.
        ## Since this page will be shown often to the anonymous visitors, and the information can be shown in not actully real-time.
        ## Therefore Memcache implemented.
        ## I can't figure out how to use get_multi so I just cache the whole ajaxpage output. 
        
        ## Thinking of to have an implementation of such Global memcache items
        IsCachedAnonymousWelcomePage = memcache.get_item('strCachedAnonymousWelcomePage', 'global')
        
        if IsCachedAnonymousWelcomePage:
            
            strCachedAnonymousWelcomePage = IsCachedAnonymousWelcomePage

        else:

            ## the not equal != is not supported!
            tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE public = 'public' and routine = 'none' and done = False ORDER BY date DESC LIMIT 9")

            tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE public = 'public' and routine = 'none' and done = True ORDER BY donedate DESC LIMIT 9")

            template_values = {
                'UserNickName': '访客',
                'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
                'tarsusaItemCollection_UserDoneItems': tarsusaItemCollection_UserDoneItems,
             }
            
            #Manupilating Templates 
            path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_anonymousbottomcontents.html')   
            strCachedAnonymousWelcomePage = template.render(path, template_values)
            
            memcache.set_item("strCachedAnonymousWelcomePage", strCachedAnonymousWelcomePage, 'global')

        self.response.out.write(strCachedAnonymousWelcomePage)
        
class get_fp_RecentRegisteredUserForAnonymous(tarsusaRequestHandler):
    
    def get(self):
        IsCachedRecentRegisteredUsers = memcache.get_item('strCachedRecentRegisteredUsers', 'global')
        
        if IsCachedRecentRegisteredUsers:
            strCachedRecentRegisteredUsers = IsCachedRecentRegisteredUsers
        else:

            tarsusaUserCollection = db.GqlQuery("SELECT * FROM tarsusaUser ORDER BY datejoinin DESC LIMIT 9")
            strRecentUsers = ''
            if tarsusaUserCollection: 
                for each_RecentUser in tarsusaUserCollection:
                    if each_RecentUser.avatar:
                        strRecentUsers += '<span ' + 'style="line-height: 2em;"><a href="/user/' + cgi.escape(str(each_RecentUser.key().id())) +  '"><img src=/image?avatar=' + str(each_RecentUser.key().id()) + " width=32 height=32>"
                    else:
                        ## Show Default Avatar
                        strRecentUsers += '<span ' + 'style="line-height: 2em;"><a href="/user/' + cgi.escape(str(each_RecentUser.key().id())) +  '">' + "<img src='/img/default_avatar.jpg' width=32 height=32>"

                    try:
                        strRecentUsers += cgi.escape(each_RecentUser.dispname) + '</a></span>'
                    except:
                        strRecentUsers += cgi.escape(each_RecentUser.user.nickname()) + '</a></span>'

                    #Complicatied TimeStamp needs to be done.
                    #UserFriends += str(datetime.datetime.now() - each_Friend.datejoinin) 
                    strRecentUsers += '<br />'


            template_values = {
                'UserNickName': '访客',
                'tarsusaUser_RecentRegistered': strRecentUsers,
             }
            
            #Manupilating Templates 
            path = os.path.join(os.path.dirname(__file__), 'pages/ajaxpage_anonymousrecentregisteredusers.html')    
            strCachedRecentRegisteredUsers = template.render(path, template_values)
            
            memcache.set_item("strCachedRecentRegisteredUsers", strCachedRecentRegisteredUsers, 'global')

        self.response.out.write(strCachedRecentRegisteredUsers)

class admin_runpatch(tarsusaRequestHandler):
    def get(self):
        urllen = len('/ajax/admin_runpatch/')
        RequestUserID = urllib.unquote(self.request.path[urllen:])
        AppliedUser = tarsusaUser.get_by_id(int(RequestUserID))
        self.write('dispname: ' +  AppliedUser.dispname)
        import DBPatcher
        #Run DB Model Patch when User Logged in.
        DBPatcher.chk_dbmodel_update(AppliedUser)
        self.write('DONE with USERID' + RequestUserID)
        #self.redirect('/')

class render(tarsusaRequestHandler):
    @userloggedin_or_403
    def get(self):
        func = self.request.get("func")
        
        try:
            maxitems = int(self.request.get("maxitems"))
        except:
            maxitems = 100
        
        template_name = "calit2"

        user = self.get_user_db()
        user_id = user.key().id()

        template_values = {
            'UserNickName': cgi.escape(user.dispname),
            'UserID': user_id,
            'func': func,
        }

        if func == "done":
            done_items = tarsusaCore.get_done_items(user_id, maxitems)
            template_values['done_items'] = done_items
            template_kind = "done_list"

        elif func == "undone":
            undone_items = tarsusaCore.get_undone_items(user_id, maxitems)
            template_values['undone_items'] = undone_items
            template_kind = "undone_list"

        elif func == "dailyroutine":
            dailyroutine_items = tarsusaCore.get_items_duetoday(user_id)
            template_values['dailyroutine_items'] = dailyroutine_items
            template_kind = "dailyroutine_list"

        elif func == "friends":
            UserFriendsItem_List = tarsusaCore.get_UserFriendStats(user_id)
            template_values['UserFriendsActivities'] = UserFriendsItem_List
            template_kind = "friends_list"
        
        elif func == "logs":
            from django.utils import simplejson as json
            user = get_user(user_id)
            done_items = user.get_donelog()
            formatted_done_items = format_done_logs(done_items)
            self.response.headers.add_header('Content-Type', "application/json")
            self.write(json.dumps(formatted_done_items))
            return 
 
        path = 'pages/%s/ajax_content_%s.html' % (template_name, template_kind)
        self.write(template.render(path, template_values))


class sidebar(tarsusaRequestHandler):
    @userloggedin_or_403
    def get(self):
        ''' Ajax Functions suites for multiple usage for Calit2 template in sidebar.'''
        current_user = self.get_user_db()
        template_values = {}

        operation_name = self.request.get("obj")
        template_name = self.request.get("template")

        if operation_name == 'user':
            #Cache is a MUST!
            template_values['UserInTemplate'] = current_user
            cached_useritem_stats = tarsusaCore.get_count_UserItemStats(current_user.key().id()) #Cached inside.
            template_values['tarsusaItemCollection_Statstics'] = cached_useritem_stats

        elif operation_name == 'item':
            #try:
            itemid = self.request.get("id")
            item_in_template = tarsusaItem.get_item(itemid)
            if item_in_template and item_in_template.user == current_user.user:
                #current_user's item
                template_values['ItemInTemplate'] = item_in_template

            elif item_in_template:
                #user's friend's item
                operation_name = 'friends' #switched to another template
                user_friend_in_template = item_in_template.usermodel
                template_values['ItemInTemplate'] = item_in_template
                template_values['UserFriendInTemplate'] = user_friend_in_template

            ##except:
            #    self.write("")


        template_values['UserNickName'] = cgi.escape(current_user.dispname)
        template_values['UserID'] = current_user.key().id()
        template_values['htmltag_today'] = datetime.date.today() 
        path = os.path.join(os.path.dirname(__file__), 'pages/%s/ajax_sidebar_%s.html' % (template_name, operation_name))
        try:
            self.write(template.render(path, template_values))
        except:
            ''' Get a unknown func by malicious user.'''
            self.write("")



def main():
    application = webapp.WSGIApplication([
                                        ('/ajax/frontpage_getdailyroutine_yesterday', getdailyroutine_yesterday),
                                        ('/ajax/frontpage_bottomcontents', get_fp_bottomcontents),
                                        ('/ajax/frontpage_introbottomcontentsforanonymous',get_fp_IntroductionBottomForAnonymous),
                                        ('/ajax/frontpage_recentregistereduserforanonymous',get_fp_RecentRegisteredUserForAnonymous),
                                        (r'/ajax/allpage_additem.+', additem),
                                        (r'/ajax/allpage_edititem.+', edititem),
                                        ('/ajax/getjson_usertodoitems', getjson_usertodoitems),
                                        ('/ajax/getjson_userdoneitems', getjson_userdoneitems),
                                        (r'/ajax/render/.*', render),
                                        (r'/ajax/sidebar/.*', sidebar),
                                        ('/ajax/admin_runpatch/.+', admin_runpatch),
                                      ('/ajax/.+',ajax_error)],
                                       debug=True)


    run_wsgi_app(application)

if __name__ == "__main__":
      main()
