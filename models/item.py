# -*- coding: utf-8 -*-

import sys
sys.path.append("../")

from google.appengine.ext import db
from models.user import tarsusaUser

import datetime
from datetime import timedelta
import memcache
import shardingcounter

class tarsusaItem(db.Expando):
    usermodel = db.ReferenceProperty(tarsusaUser)
    user = db.UserProperty()
    name = db.StringProperty()
    comment = db.StringProperty(multiline=True)
    tags = db.ListProperty(db.Key)
    date = db.DateTimeProperty(auto_now_add=True)
    expectdate = db.DateTimeProperty()
    donedate = db.DateTimeProperty()
    done = db.BooleanProperty()
    routine = db.StringProperty(required=True, choices=set(["none", "daily", "weekly", "monthly", "seasonly", "yearly"]))
    public = db.StringProperty(choices=set(["private", "public", "publicOnlyforFriends"]))
   
    @staticmethod
    def get_item(item_id):
        cached_item = memcache.get("item:%s" % item_id)
        if cached_item:
            return cached_item
        try:
            item = tarsusaItem.get_by_id(int(item_id))
        except:
            return None
        memcache.set("item:%s" % item_id, item)
        return item
    
    @staticmethod
    def count():
        return shardingcounter.get_count("tarsusaItem")

    def delete_item(self, user_id):
        if self.usermodel.key().id() != user_id:
            return False
        
        item_id = int(self.key().id())
        user_id = int(user_id)

        if self.public != 'none':
            memcache.event('deletepublicitem', user_id)

        if self.routine == 'none':
            self.delete()
            memcache.event('deleteitem', user_id)

        else:
            routinelog_list = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1", item_id)
            db.delete(routinelog_list)
            self.delete()
            memcache.event('deleteroutineitem_daily', user_id)

        shardingcounter.increment("tarsusaItem", "minus")

        memcache.delete_item("itemstats", user_id)
        memcache.delete("item:%s" % item_id)

        return True


    def set_duetoday(self):
        today = datetime.date.today()
        end_of_today = datetime.datetime(today.year, today.month, today.day, 23,59,59)
        self.expectdate = end_of_today
        self.save()

    def set_duetomorrow(self):
        tomorrow = datetime.date.today() + timedelta(days=1)
        end_of_tomorrow = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23,59,59)
        self.expectdate = end_of_tomorrow
        self.save()
    
    @property
    def is_duetoday(self):
        today = datetime.date.today()
        end_of_today = datetime.datetime(today.year, today.month, today.day, 23,59,59)
        return self.expectdate == end_of_today

    @property
    def is_duetomorrow(self):
        tomorrow = datetime.date.today() + timedelta(days=1)
        end_of_tomorrow = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23,59,59)
        return self.expectdate == end_of_tomorrow
