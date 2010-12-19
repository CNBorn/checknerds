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

    def done_today(self):
        assert self.routine == "daily"
        routine_logkey = db.GqlQuery("SELECT __key__ FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC LIMIT 1", self.usermodel.user, self.key().id())
        for this_routine_log in routine_logkey:
            if datetime.datetime.date(tarsusaRoutineLogItem.get_item(this_routine_log.id()).donedate) == datetime.date.today():
                return True
        return False


    def jsonized(self):
        return {
            'id' : str(self.key().id()), 
            'name' : self.name, 
            'date' : self.date, 
            'donedate': self.donedate, 
            'expectdate': self.expectdate, 
            'comment' : self.comment, 
            'routine' : self.routine, 
            'category' : self.done, 
            'done': self.done,
            'is_duetoday': self.is_duetoday,
            'is_duetomorrow': self.is_duetomorrow
           }


    def done_item(self, user, misc=''):
        item_id = self.key().id()
        user_id = user.key().id()
        if self.usermodel.key().id() != user_id:
            return False

        done_lastday_routine = False
        if misc == 'y':
            done_lastday_routine = True

        if self.routine == 'none':
            self.donedate = datetime.datetime.now()
            self.done = True
            self.put()
            memcache.event('doneitem', user_id)

        if self.routine == "daily":
            new_routinelog_item = tarsusaRoutineLogItem(routine=self.routine, user=user.user, routineid=item_id)
            
            one_day = datetime.timedelta(days=1)
            yesterday = datetime.datetime.combine(datetime.date.today() - one_day, datetime.time(0))
            if done_lastday_routine:
                new_routinelog_item.donedate = yesterday
                is_already_done = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate > :2 and donedate < :3", item_id, yesterday - one_day , datetime.datetime.combine(datetime.date.today(), datetime.time(0)) - datetime.timedelta(seconds=1))
                memcache.event('doneroutineitem_daily_yesterday', user_id)
            else: 
                is_already_done = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate > :2 and donedate < :3", item_id, yesterday + one_day ,datetime.datetime.now())
                memcache.event('doneroutineitem_daily_today', user_id)

            if is_already_done.count() < 1:
                new_routinelog_item.put()
                memcache.event('refresh_dailyroutine', user_id)
    
        memcache.set("item:%s" % item_id, self)
        return True


class tarsusaRoutineLogItem(db.Model):
    user = db.UserProperty()
    routineid = db.IntegerProperty()
    routine = db.StringProperty(required=True, choices=set(["none", "daily", "weekly", "monthly", "seasonly", "yearly"]))
    donedate = db.DateTimeProperty(auto_now_add=True)

    @staticmethod
    def get_item(item_id):
        cached_item = memcache.get("routineitem:%s" % item_id)
        if cached_item:
            return cached_item
        try:
            item = tarsusaRoutineLogItem.get_by_id(int(item_id))
        except:
            return None
        memcache.set("routineitem:%s" % item_id, item)
        return item
