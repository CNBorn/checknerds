# -*- coding: utf-8 -*-

import sys
sys.path.append("../")
import datetime
from models.consts import ONE_DAY

from google.appengine.ext import db
import memcache
import shardingcounter
from models.tag import Tag
from utils import cache

class tarsusaUser(db.Model):
    user = db.UserProperty()
    userid = db.IntegerProperty()
    mail = db.EmailProperty()
    avatar = db.BlobProperty()
    urlname = db.StringProperty()
    dispname = db.StringProperty()
    website = db.LinkProperty()
    usedtags = db.ListProperty(db.Key)
    friends = db.ListProperty(db.Key)
    
    datejoinin = db.DateTimeProperty(auto_now_add=True)

    apikey = db.StringProperty()
    
    notify_dailybriefing_time = db.TimeProperty()
    notify_addedasfriend = db.BooleanProperty()
    
    def __unicode__(self):
        if self.dispname:
            return self.dispname
        else:
            return self.user.nickname()

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    @classmethod
    def get_latestusers(count=8):
        result = db.GqlQuery("SELECT * FROM tarsusaUser ORDER by datejoinin DESC LIMIT 8")
        return result

    @staticmethod
    def get_user(user_id):
        return get_user(user_id)

    @staticmethod 
    def count():
        return shardingcounter.get_count("tarsusaUser")

    def get_dailyroutine_items(self):
        return db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'daily' ORDER BY date DESC", self.user)

    def has_tag(self, tag_name):
        tag = db.Query(Tag).filter("name =", tag_name).get()
        for check_whether_used_tag in self.usedtags:
            item_check_whether_used_tag = db.get(check_whether_used_tag)
            if item_check_whether_used_tag:
                if tag.key() == check_whether_used_tag or tag.name == item_check_whether_used_tag.name:
                    return True
        return False

    def tag_list(self):
        tag_names = []
        if self.usedtags:
            tags = []
            for each_tag in self.usedtags:
                tags.append(each_tag)
                tag_names.append(db.get(each_tag).name)

            tag_names = list(set(tag_names))
            tags = list(set(tags))

        return tag_names

    def tag_item_ids_list(self, tag_name):
        if not tag_name: return False
        items = []
        tag = db.Query(Tag).filter("name =", tag_name).get()
        user_items = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY done, date DESC", self.user)
        for each_item in user_items:
            for each_tag in each_item.tags:
                if db.get(each_tag).name == tag_name:
                    items.append(each_item.key().id())
        return items

    @property
    def avatarpath(self):
        if self.avatar:
            return '/image?avatar=%s' % self.key().id()
        return '/img/default_avatar.jpg'

    def get_friends(self):
        friend_list = self.friends
        results = []
        if friend_list: 
            for each_key in friend_list:
                friend = db.get(each_key)
                each_result = {'id': str(friend.key().id())}
                each_result['avatarpath'] = friend.avatarpath
                #These code is here due to DB Model change since Rev.76
                try:                                
                    each_result['name'] = cgi.escape(friend.dispname)
                except:
                    each_result['name'] = cgi.escape(friend.user.nickname())
                results.append(each_result)
        return results

    @cache("itemlist:{self.key().id()}")
    def get_undone_items(self, maxitems=100):
        from tarsusaCore import get_tarsusaItemCollection
        undone_items = get_tarsusaItemCollection(self.key().id(), done=False, maxitems=maxitems)
        return undone_items

    def get_doneitems_in(self, date):
        yesterday_ofdate = datetime.datetime.combine(date - ONE_DAY, datetime.time(0))
        nextday_ofdate = datetime.datetime.combine(date + ONE_DAY, datetime.time(0))
        ItemCollection_ThisDayCreated = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND donedate > :2 AND donedate <:3 AND done = True AND routine = 'none' ORDER BY donedate DESC", self.user, yesterday_ofdate, nextday_ofdate)
        result = []
        for each_doneItem_withinOneday in ItemCollection_ThisDayCreated:
            result.append(each_doneItem_withinOneday.jsonized())
        
        return result

    def get_public_items(self, public='public', count=30):
        result = []
        if public == 'public':
            publicitem_collection = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and public = 'public' ORDER BY date DESC LIMIT 30", self.user)
        elif public == 'publicOnlyforFriends':
            publicitem_collection = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and public != 'private' ORDER BY public, date DESC LIMIT 30", self.user)
        for each_item in publicitem_collection:
            result.append(each_item.jsonized())
        return result

    def get_donelog(self, startdate='', lookingfor='next', maxdisplaydonelogdays=7):
        #lookingfor = 'next' to get the records > startdate
        #             'previous' to get the records <= startdate
        from tarsusaCore import check_have_thisitem_in_itemcollection 
        MaxDisplayedDonelogDays = maxdisplaydonelogdays
        ThisUser = self
        sort_backwards = False
        if not lookingfor == 'next':
            sort_backwards = True
        
        DisplayedDonelogDays = 1 

        Item_List = []
        userid = ThisUser.key().id()
        if startdate != '':
            if lookingfor == 'next':
                tarsusaRoutineLogItemCollection = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 AND donedate > :2 ORDER BY donedate DESC", ThisUser.user, startdate)
            else:
                tarsusaRoutineLogItemCollection = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 AND donedate <= :2 ORDER BY donedate DESC", ThisUser.user, startdate)

        else:
            tarsusaRoutineLogItemCollection = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 ORDER BY donedate DESC", ThisUser.user)
                
        Donedate_of_previousRoutineLogItem = None  ## To display the routine item log by Daily.

        for each_RoutineLogItem in tarsusaRoutineLogItemCollection:
            
            DoneDateOfThisItem = datetime.datetime.date(each_RoutineLogItem.donedate)
            if DisplayedDonelogDays > MaxDisplayedDonelogDays:
                break
            
            if DoneDateOfThisItem != Donedate_of_previousRoutineLogItem:
                DisplayedDonelogDays += 1

            from models import tarsusaItem
            this_item = tarsusaItem.get_item(each_RoutineLogItem.routineid).jsonized()
            this_item['donedate']= each_RoutineLogItem.donedate
            Item_List.append(this_item)
            
            normalitems = ThisUser.get_doneitems_in(DoneDateOfThisItem)
            for each_item in normalitems:
                if not check_have_thisitem_in_itemcollection(each_item, Item_List):
                    Item_List.append(each_item) 

            Donedate_of_previousRoutineLogItem = DoneDateOfThisItem 

        Item_List.sort(key=lambda item:item['donedate'], reverse=sort_backwards)
        return Item_List


    @cache("itemstats:{self.key().id()}")
    def get_itemstats(self):

        tarsusaItemCollection_UserDoneItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = True ORDER BY date DESC", self.user)
        tarsusaItemCollection_UserTodoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC", self.user)

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
            'UserDonePercentage': "%.2f%%" % percentage_done,
        }
        
        return result 


@cache("user:{user_id}")
def get_user(user_id):
    try:
        return tarsusaUser.get_by_id(int(user_id))
    except:
        return None
