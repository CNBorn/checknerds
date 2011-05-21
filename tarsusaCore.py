# -*- coding: utf-8 -*-

# ****************************************************************
# CheckNerds - www.checknerds.com
# - tarsusaCore.py
# http://cnborn.net, http://twitter.com/CNBorn
#
# ****************************************************************

import urllib
import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext import search
import logging

from models import *
from base import *
from models.user import get_user

import time, datetime
from datetime import timedelta
import random

import memcache
import re

import shardingcounter

from views import service

def get_tarsusaItemCollection(userid, done, routine='none', startdate='', enddate='', startdonedate='', enddonedate='', sort='asc', maxitems=9, omittopbottom=False, public='none'):
    
    ThisUser = tarsusaUser.get_user(int(userid))
    Item_List = []
    
    #Get tarsusaItemCollection
    #query = tarsusaItem.all()
    query = db.Query(tarsusaItem)

    #It seems that when query gets done=True, it returns nothing!
    
    #Newly Add done=None state
    if done != None:
        query = query.filter('done =', done)

    query = query.filter('user =', ThisUser.user)
    query = query.filter('routine =', routine)

    #Caution: Public setting will display all items by default.
    #When calling the function using external API, 
    #The Setting should be filtered first, 
    #In case users will be able to see other's items.
    if public != 'none':
        if public == 'nonprivate':
            query.filter('public !=', 'private')
        elif public == 'public':
            query.filter('public =', 'public')
        elif public == 'private':           
            query.filter('public =', 'private')
    else:
        #No matter what the public is.
        pass

    if startdate != '':
        logging.info('filter' + str(startdate))
        query = query.filter('date >', startdate)
        query.order('date')
    #For this two conditions can't be run at the same time.
    elif enddate != '':
        logging.info('filter' + str(datetime.datetime.fromtimestamp(time.mktime(time.strptime(str(enddate), "%Y-%m-%d %H:%M:%S")))))
        query = query.filter('date <', datetime.datetime.fromtimestamp(time.mktime(time.strptime(str(enddate), "%Y-%m-%d %H:%M:%S"))))
        #query = query.filter('date <', enddate)
        query = query.order('-date')

    if startdonedate != '':
        #logging.info('startdonedate')
        #logging.info(startdonedate)
        #above line could be used in testing

        query.filter('donedate >', startdonedate)
        query.order('donedate')
        #Above will cause that weird error.(Got nothing.)
    if enddonedate != '':
        #logging.info('enddonedate')
        #logging.info(enddonedate)
        #above line could be used in testing

        query.filter('donedate <', enddonedate)
        query.order('-donedate')
        
    if done == True:
        strOrderSort = 'donedate'
        if startdate == '' and enddonedate == '':   
            #Default order by date DESC.    
            #For example: Done first page.
            #logging.info('donefirstpage')
                        
            #query.filter('done =', True)
            #query.filter('donedate !=', datetime.datetime.now())
            #logging.info(query.fetch(limit=9))
            query.order('-donedate')
    else:
        strOrderSort = 'date'
        #Default order by date DESC.    
        query.order('-date')
    
    #If it doesn't run, run this line
    #print strOrderSort

    tarsusaItemCollection_queryResults = query.fetch(limit=maxitems)
    for each_tarsusaItem in tarsusaItemCollection_queryResults:
        ItemTags = ''   
        try:
            TagsCount = 0
            for each_tag in db.get(each_tarsusaItem.tags):
                if TagsCount >= 1:
                    ItemTags += ',' + cgi.escape(each_tag.name)
                else:
                    ItemTags += cgi.escape(each_tag.name)
                TagsCount += 1
            if ItemTags == '':
                ItemTags = None
        except:
            # There is some chances that ThisItem do not have any tags.
            ItemTags = None
            pass
        this_item = each_tarsusaItem.jsonized()
        this_item['tags'] = ItemTags
        Item_List.append(this_item)
    #print Item_List



    if strOrderSort != 'date':
        
        #sort the results order by donedate:
        #Sort Algorithms from
        #http://www.lixiaodou.cn/?p=12
        length = len(Item_List)
        
        for i in range(0,length):
            for j in range(length-1,i,-1):
                    if Item_List[j][strOrderSort] > Item_List[j-1][strOrderSort]:
                        temp = Item_List[j]
                        Item_List[j]=Item_List[j-1]
                        Item_List[j-1]=temp
        #---

    return Item_List

def gen_key_fac(in_key):
    def gen_key(*args, **kwargs):
        key = in_key
        para_re = re.compile(r"{(.*?)}")
        para_name_list = para_re.findall(key)
        for pos, para in enumerate(para_name_list):
            if para in kwargs.keys():
                value = kwargs[para]
                key = key.replace("{%s}" % para, str(value))
            elif pos <= len(args):
                value = args[pos]
                key = key.replace("{%s}" % para, str(value))
            else:
                raise
        return key
    return gen_key


def cache(key="default_mc_key", time=60*60*30):
    def _cache(func):
        gen_key=gen_key_fac(key)
        def _processor(*args, **kwargs):
            mkey = gen_key(*args, **kwargs)
            is_cached = memcache.get(mkey)
            if is_cached:
                return memcache.get(mkey)
            result = func(*args, **kwargs)
            memcache.set(mkey, result, time)
            return result
        return _processor
    return _cache

@cache("itemlist:{user_id}", 3600)
def get_undone_items(user_id, maxitems=100):
    undone_items = get_tarsusaItemCollection(user_id, done=False, maxitems=maxitems)
    return undone_items

def _get_more_undone_items(user_id, maxitems, after_item_id):
    ThisUser = tarsusaUser.get_user(int(user_id))
    Item_List = []
    query = db.Query(tarsusaItem)
    query = query.filter('user =', ThisUser.user)
    query = query.filter('done =', False)
    query = query.filter('routine =', 'none')

    before_date = tarsusaItem.get_item(after_item_id).date
    query = query.filter('date <', before_date)
    query.order('-date')
    tarsusaItemCollection_queryResults = query.fetch(limit=maxitems)
    for each_tarsusaItem in tarsusaItemCollection_queryResults:
        this_item = each_tarsusaItem.jsonized()
        Item_List.append(this_item)
    return Item_List

def get_more_undone_items(user_id, maxitems, before_item_id):
    undone_items = _get_more_undone_items(user_id, maxitems, before_item_id)
    return undone_items

def get_done_items(user_id, maxitems=100):
    cached_userdoneitems = memcache.get_item("doneitemlist", user_id)
    if cached_userdoneitems:
        return cached_userdoneitems
    done_items = get_tarsusaItemCollection(user_id, done=True, maxitems=maxitems)
    memcache.set_item("doneitemlist", done_items, user_id)
    return done_items

def get_dailyroutine(userid):

    this_user = tarsusaUser.get_user(userid)
 
    cached_user_dailyroutine = memcache.get_item("dailyroutine_items", int(userid))
    if cached_user_dailyroutine is not None:
        return cached_user_dailyroutine

    item_list = []
    for routine_item in this_user.get_dailyroutine_items():
        this_item = routine_item.jsonized()
        this_item['done'] = routine_item.has_done_today()
        item_list.append(this_item)

    memcache.set_item("dailyroutine_items", item_list, int(userid))
    return item_list


def get_items_duetoday(userid):
    
    this_user = tarsusaUser.get_user(userid)

    today = datetime.date.today()
    end_of_today = datetime.datetime(today.year, today.month, today.day, 23,59,59)

    items_due_today = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and expectdate =:2", \
            this_user.user, end_of_today)

    results = [item.jsonized() for item in items_due_today] + get_dailyroutine(userid)
    results = sorted(results, key=lambda item:item['date'], reverse=True)
    return sorted(results, key=lambda item:item['done'])


def check_have_thisitem_in_itemcollection(item, itemcollection):
    Duplicated_tarsusaItem_Inlist = False
    for check_for_duplicated_tarsusaItem in itemcollection:
        if check_for_duplicated_tarsusaItem['id'] == item['id'] and check_for_duplicated_tarsusaItem['donedate'] == item['donedate']:
            Duplicated_tarsusaItem_Inlist = True
    return Duplicated_tarsusaItem_Inlist

def format_done_logs(done_items):
    result = {}
    previous_done_date = None
    for each_item in done_items:
        col_date = each_item['donedate'].strftime('%Y-%m-%d')
        if not previous_done_date or \
           each_item['donedate'] != previous_done_date:
                result.setdefault(col_date,[])
        each_item['donedate'] = col_date
        each_item['date'] = each_item['date'].strftime('%Y-%m-%d')
        if each_item['expectdate']:
            each_item['expectdate'] = each_item['expectdate'].strftime('%Y-%m-%d')
        result[col_date].append(each_item)
        previous_done_date = each_item['donedate']
    return result

def format_items(items):
    result = [] 
    for each_item in items:
        if each_item['donedate']:
            each_item['donedate'] = each_item['donedate'].strftime('%Y-%m-%d')
        each_item['date'] = each_item['date'].strftime('%Y-%m-%d')
        if each_item['expectdate']:
            each_item['expectdate'] = each_item['expectdate'].strftime('%Y-%m-%d')
        result.append(each_item)
    return result

def get_UserFriendStats(userid, startdate='', lookingfor='next', maxdisplayitems=15):
    
    #Get user's FriendStats
    #SHOW YOUR FRIENDs Recent Activities
    
    #lookingfor = 'next' to get the records > startdate
    #             'previous' to get the records <= startdate
    #actully you can not decide how many items will be displayed here. 15 will be a fixed number, maybe less than 15 will be displayed.

    #Have to add this limit for GAE's CPU limitation.
    MaxDisplayedItems = maxdisplayitems
    ThisUser = tarsusaUser.get_user(int(userid))
    
    #---
    userid = ThisUser.key().id()

    tarsusaUserFriendCollection = ThisUser.friends
    DisplayedDonelogDays = 1 

    UserFriendsItem_List = []

    if tarsusaUserFriendCollection:
        #first of all, CurrentUser should have some friends
    
        cached_user_friendstatus = memcache.get_item("friendstatus", int(userid))

        if cached_user_friendstatus is not None:

            return cached_user_friendstatus[:maxdisplayitems]

        else:

            for each_FriendKey in tarsusaUserFriendCollection:
                UsersFriend =  db.get(each_FriendKey)                       
                
                #Due to usermodel and other are applied in a later patch, some tarsusaItem may not have that property.
                #There maybe need to extend if we need more property from tarsusaItem.usermodel
                UsersFriendid = UsersFriend.key().id()
                try:
                    UsersFriendDispname = UsersFriend.dispname
                except:
                    UsersFriendDispname = UsersFriend.user.nickname()


                tarsusaItemCollection_UserFriendsRecentItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY date DESC LIMIT 50", UsersFriend.user)

                for tarsusaItem_UserFriendsRecentItems in tarsusaItemCollection_UserFriendsRecentItems:
                    ## Check whether should show this item.
                    if tarsusaItem_UserFriendsRecentItems.public != 'private':                      
                        #Output Avatar Information
                        UserAvatar = '/img/default_avatar.jpg'
                        #Some of the older items may not have the usermodel property
                        try:
                            if tarsusaItem_UserFriendsRecentItems.usermodel.avatar:
                                UserAvatar = '/image?avatar=' + str(tarsusaItem_UserFriendsRecentItems.usermodel.key().id())
                        except:
                            UserAvatar = '/img/default_avatar.jpg'

                        ## Check whether this item had done.
                        if tarsusaItem_UserFriendsRecentItems.done == True:
                                friend_Item = {'id' : str(tarsusaItem_UserFriendsRecentItems.key().id()), 'name' : tarsusaItem_UserFriendsRecentItems.name, 'date' : str(tarsusaItem_UserFriendsRecentItems.donedate), 'comment' : tarsusaItem_UserFriendsRecentItems.comment, 'category' : 'done', 'userdispname': UsersFriendDispname, 'userid': UsersFriendid, 'avatar': UserAvatar}
                        else:
                            friend_Item = {'id' : str(tarsusaItem_UserFriendsRecentItems.key().id()), 'name' : tarsusaItem_UserFriendsRecentItems.name, 'date' : str(tarsusaItem_UserFriendsRecentItems.date), 'comment' : tarsusaItem_UserFriendsRecentItems.comment, 'category' : 'todo', 'userdispname': UsersFriendDispname, 'userid': UsersFriendid, 'avatar': UserAvatar}

                        UserFriendsItem_List.append(friend_Item)

            #sort the results:
            #Sort Algorithms from
            #http://www.lixiaodou.cn/?p=12
            length = len(UserFriendsItem_List)
            for i in range(0,length):
                for j in range(length-1,i,-1):
                        #Convert string to datetime.date
                        #http://mail.python.org/pipermail/tutor/2006-March/045729.html  
                        time_format = "%Y-%m-%d %H:%M:%S"
                        if datetime.datetime.fromtimestamp(time.mktime(time.strptime(UserFriendsItem_List[j]['date'][:-7], time_format))) > datetime.datetime.fromtimestamp(time.mktime(time.strptime(UserFriendsItem_List[j-1]['date'][:-7], time_format))):
                            temp = UserFriendsItem_List[j]
                            UserFriendsItem_List[j]=UserFriendsItem_List[j-1]
                            UserFriendsItem_List[j-1]=temp

            memcache.set_item("friendstatus", UserFriendsItem_List, int(userid))
            return UserFriendsItem_List[:maxdisplayitems]

    else:
        return None #This User don't have any friends.

def get_count_UserItemStats(userid):    

    CurrentUser = tarsusaUser.get_user(int(userid))

    cachedUserItemStats = memcache.get_item("itemstats", CurrentUser.key().id())
    if cachedUserItemStats:
        return cachedUserItemStats

    tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True ORDER BY date DESC", users.get_current_user())                
    tarsusaItemCollection_UserTodoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC", users.get_current_user())               

    count_done_items = 0
    count_todo_items = 0
    percentage_done = 0.00

    count_done_items = tarsusaItemCollection_UserDoneItems.count() 
    count_todo_items = tarsusaItemCollection_UserTodoItems.count()
    count_total_items = count_done_items + count_todo_items

    if count_total_items != 0:
        percentage_done = count_done_items * 100.00 / count_total_items

    result = {
        'UserTotalItems': count_total_items,
        'UserToDoItems': count_todo_items,
        'UserDoneItems': count_done_items,
        'UserDonePercentage': percentage_done,
    }
    
    memcache.set_item("itemstats", result, CurrentUser.key().id())

    return result 

def DoneItem(ItemId, UserId, Misc=''):
    item = tarsusaItem.get_item(ItemId)
    user = tarsusaUser.get_user(UserId)
    return item.done_item(user, Misc)

  
def UndoneItem(ItemId, UserId, Misc):
    #UndoneItem function specially designed for API calls.  
    #Duplicated Code from tarsusaItemCore, refactor needed in the future.
    
    ## This function won't check permission for login, for external API usage.
    #Instead, you need to provide a userid, and the function will check wheather this user have the permission to do so.
    #Which indicates that you definately need a permission check mechanism when you calling this function from outside.
    # Permission check is very important.

    UndoneYesterdaysDailyRoutine = False
    if Misc == 'y':
        UndoneYesterdaysDailyRoutine = True

    tItem = tarsusaItem.get_item(ItemId)

    if tItem.usermodel.key().id() == int(UserId):
        ## Check User Permission to undone this Item

        if tItem.routine == 'none':
            ## if this item is not a routine item.
            tItem.donedate = ""
            tItem.done = False
            tItem.put()
            #-----  
            memcache.event('undoneitem', int(UserId))
            #return 0 indicates it's ok.
            memcache.set("item:%s" % ItemId, tItem)
            return 0

        else:
            if tItem.routine == 'daily':                

                if UndoneYesterdaysDailyRoutine != True:

                    del tItem.donetoday
                    tItem.put()
                    
                    memcache.event('undoneroutineitem_daily_today', int(UserId))
                    
                    ## Please Do not forget to .put()!

                    ## This is a daily routine, and we are going to undone it.
                    ## For DailyRoutine, now I just count the matter of deleting today's record.
                    ## the code for handling the whole deleting routine( delete all concerning routine log ) will be added in future
                    
                    # GAE can not make dateProperty as query now! There is a BUG for GAE!
                    # http://blog.csdn.net/kernelspirit/archive/2008/07/17/2668223.aspx
                    
                    tarsusaRoutineLogItemCollection_ToBeDeleted = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate < :2", int(ItemId), datetime.datetime.now())
                
                    #It has been fixed. For just deleting TODAY's routinelog.
                    one_day = datetime.timedelta(days=1)
                    yesterday = datetime.datetime.now() - one_day

                    for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
                        if result.donedate < datetime.datetime.now() and result.donedate.date() != yesterday.date() and result.donedate > yesterday:
                            result.delete()

                    #return 0 indicates it's ok.
                    return 0

                else:
                    # Undone Yesterday's daily routine item.    
                    
                    memcache.event('undoneroutineitem_daily_yesterday', int(UserId))
                    
                    try:
                        del tItem.doneyesterday
                        tItem.put()
                    except:
                        pass
                    
                    one_day = datetime.timedelta(days=1)
                    yesterday = datetime.datetime.combine(datetime.date.today() - one_day,datetime.time(0))
                    tarsusaRoutineLogItemCollection_ToBeDeleted = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate > :2 and donedate < :3", int(ItemId), yesterday, datetime.datetime.today())
                    ## CAUTION: SOME ITEM MAY BE DONE IN THE NEXT DAY, SO THE DONEDATE WILL BE IN NEXT DAY
                    ## THEREFORE donedate>:2 and donedate<datetime.datetime.today() <--today() is datetime

                    for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
                        if result.donedate < datetime.datetime.now() and result.donedate.date() == yesterday.date(): #and result.donedate.date() > datetime.datetime.date(datetime.datetime.now() - datetime.timedelta(days=2)):
                            result.delete()
                        else:
                            pass
                    
                    return 0
    else:
        #Authentication failed.
        return 1

def AddItem(UserId, rawName, rawComment='', rawRoutine='none', rawPublic='private', rawInputDate='', rawTags=None):
    
    user = tarsusaUser.get_user(int(UserId))
    item_comment = cgi.escape(rawComment)[:500]
    item_name = cgi.escape(rawName)               
    item_routine = cgi.escape(rawRoutine)
    if item_routine not in ["none", "daily", "weekly", "monthly", "seasonly", "yearly"]:
        item_routine = "none"
    item_public = cgi.escape(rawPublic)
    if item_public not in ['private', 'public', 'publicOnlyforFriends']:
        item_public = 'private'

    item = tarsusaItem(user=user.user, name=item_name, comment=item_comment, routine=item_routine)
    item.public = item_public
    item.usermodel = user              
    item.done = False

    item_expectdate = None
    if rawInputDate != '':
        raw_expectdate = datetime.date(*time.strptime(rawInputDate,"%Y-%m-%d")[:3])
        if raw_expectdate != datetime.datetime.date(datetime.datetime.today()):
            currenttime = datetime.datetime.time(datetime.datetime.now())
            item_raw_expectdate = datetime.datetime(raw_expectdate.year, raw_expectdate.month, \
                             raw_expectdate.day, currenttime.hour, currenttime.minute, \
                             currenttime.second, currenttime.microsecond)
    item.expectdate = item_expectdate

    if item_routine == 'daily':
        memcache.event('addroutineitem_daily', user.key().id())
    else:
        memcache.event('additem', user.key().id())
    if item_public != 'private':
        memcache.event('addpublicitem', user.key().id())

    try:
        item_tags = cgi.escape(rawTags).split(",")
    except:
        item_tags = None 

    if item_tags:

        for each_tag_name in item_tags:

            tag = db.Query(Tag).filter("name =", each_tag_name).get()
            if not tag: 
                tag = Tag(name=each_tag_name)
                tag.put()

            item.tags.append(tag.key())
                
            if not user.has_tag(tag.name):
                user.usedtags.append(tag.key())     
    
    item.put()
    user.put()

    user_id = user.key().id()
    item_id = item.key().id()
    shardingcounter.increment("tarsusaItem")
    memcache.delete_item("itemstats", user_id)
    memcache.set("item:%s" % item_id, item)
    return item_id


def verify_AppModel(apiappid, apiservicekey):
    import hashlib
    
    if apiappid == None or apiservicekey == None:
        return False
    
    #To Verify AppModel, Applications that uses CheckNerds API.
    ThisApp = AppModel.get_by_id(apiappid)
    if ThisApp == None:
        return False
    
    #At beginning, will not turn this on.
    #if ThisApp.enable == False:
    #   return False

    #Check with API Usage.
    AppApiUsage = memcache.get("appapiusage" + str(apiappid))   
    if AppApiUsage >= ThisApp.api_limit:
        #Api Limitation exceed.
        self.write('<h1>API Limitation exceed.</h1>')       
        logging.info("AppID:" + str(apiappid) + ":" + cgi.escape(ThisApp.name) + " has exceed its API limitation.")
        return False
    else:
        if hashlib.sha256(ThisApp.servicekey).hexdigest() == apiservicekey:
            #Accept this App
            #------------------------
            #Manipulating API calls count.
            if AppApiUsage == None:
                memkey = "appapiuseage" + str(apiappid)
                AppApiUsage = 0
            AppApiUsage += 1
            memcache.set_item("appapiusage", AppApiUsage, int(apiappid))
            #------------------------
            #Below line could be turned off.
            logging.info("AppID:" + str(apiappid) + ":" + cgi.escape(ThisApp.name) + " accessed via API")
            #------------------------
            return True
        else:
            #Authentication Failed.
            #Should return a status number in the future.
            return False


def verify_UserApi(userid, userapikey):
    import hashlib
    #To Verify UserApi, the Authentication process.
    
    #To check whether this user is existed.
    ThisUser = tarsusaUser.get_user(userid)
    if ThisUser == None:
        return False

    #Check with API Usage.
    UserApiUsage = memcache.get_item("userapiusage", int(userid))
    if UserApiUsage >= global_vars['apilimit']:
        #Api Limitation exceed.
        #self.write('<h1>API Limitation exceed.</h1>')
        return False
    else:
        if hashlib.sha256(ThisUser.apikey).hexdigest() == userapikey:
            #Should use log to monitor API usage.
            #Also there should be limitation for the apicalls/per hour.
            if UserApiUsage == None:
                UserApiUsage = 0
            UserApiUsage += 1
            memcache.set_item("userapiusage", UserApiUsage, int(userid))
            return True
        else:
            #Authentication Failed.
            return False





