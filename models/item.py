# -*- coding: utf-8 -*-

import sys
sys.path.append("../")

from google.appengine.ext import db
from google.appengine.api import taskqueue
from models.user import tarsusaUser
from models.tag import Tag

import datetime
from datetime import timedelta
import memcache
from libs import shardingcounter
from models.consts import ONE_DAY, ONE_SECOND, ONE_HOUR
from utils import cache

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

    def flush(self):
        memcache.delete("item:%s" % self.key().id())

    @staticmethod
    @cache("item:{item_id}")
    def get_item(item_id):
        try:
            item = tarsusaItem.get_by_id(int(item_id))
        except:
            return None
        return item
    
    @staticmethod
    def count():
        return shardingcounter.get_count("tarsusaItem")

    @classmethod
    def get_collection(cls, userid, done, routine='none', maxitems=9, public='none'):
        tUser = tarsusaUser.get_user(int(userid))
        if not tUser and not done: return []

        results = []
        query = db.Query(cls)
        query = query.filter('done =', done)
        query = query.filter('user =', tUser.user)
        query = query.filter('routine =', routine)

        if public != 'none':
            if public == 'nonprivate':
                query.filter('public !=', 'private')
            elif public == 'public':
                query.filter('public =', public)

        sortorder = 'donedate' if done else 'date'
        query.order('-%s' % sortorder)
        
        tItems = query.fetch(limit=maxitems)
        for item in tItems: 
            this_item = item.jsonized()
            this_item['tags'] = " ".join(item.get_tags_name())
            results.append(this_item)
        return results

    def delete_item(self, user_id):
        user = self.usermodel
        if user.key().id() != user_id:
            return False
        
        item_id = int(self.key().id())
        user_id = int(user_id)

        if self.done:
            user.decr_done_items()
        else:
            user.decr_todo_items()

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

        memcache.delete("itemstats:%s" % user_id)
        memcache.delete("item:%s" % item_id)

        return True


    def set_duetoday(self):
        today = datetime.date.today()
        end_of_today = datetime.datetime(today.year, today.month, today.day, 23,59,59)
        self.expectdate = end_of_today
        self.put()
        self.flush()

    def set_duetomorrow(self):
        tomorrow = datetime.date.today() + timedelta(days=1)
        end_of_tomorrow = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23,59,59)
        self.expectdate = end_of_tomorrow
        self.put()
        self.flush()
    
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

    @property
    def is_dueyesterday(self):
        yesterday = datetime.date.today() - timedelta(days=1)
        end_of_yesterday = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 23,59,59)
        return self.expectdate == end_of_yesterday

    @property
    def has_categorized_duedate(self):
        return not (self.is_duetoday or self.is_duetomorrow)

    @property
    def has_done_today(self):
        assert self.routine == "daily"
        today = datetime.date.today()

        item_id = self.key().id()
        is_done_today = memcache.get("item:%s:has_done_in:%s" % (item_id, today), None)
        if is_done_today is not None:
            return is_done_today

        routine_logkey = db.GqlQuery("SELECT __key__ FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC LIMIT 1", self.usermodel.user, self.key().id())
        for this_routine_log in routine_logkey:
            if datetime.datetime.date(tarsusaRoutineLogItem.get_item(this_routine_log.id()).donedate) == datetime.date.today():
                memcache.set("item:%s:has_done_in:%s" % (item_id, today), True)
                return True
        memcache.set("item:%s:has_done_in:%s" % (item_id, today), False)
        return False

    @property
    def has_done_yesterday(self):
        assert self.routine == "daily"
        routine_logkey = db.GqlQuery("SELECT __key__ FROM tarsusaRoutineLogItem WHERE user = :1 and routine = 'daily' and routineid = :2 ORDER BY donedate DESC LIMIT 2", self.usermodel.user, self.key().id())
        for this_routine_log in routine_logkey:
            if tarsusaRoutineLogItem.get_item(this_routine_log.id()).donedate.date() == datetime.date.today() - ONE_DAY:
                return True
        return False

    @property
    def duration(self):
        if not self.done: return 0
        return (self.donedate - self.date).days
    
    def jsonized(self):
        return {
            'id' : str(self.key().id()), 
            'name' : self.name, 
            'date' : self.date.strftime('%Y-%m-%d'),
            'donedate': self.donedate.strftime('%Y-%m-%d') if self.donedate else '',
            'expectdate': self.expectdate.strftime('%Y-%m-%d') if self.expectdate else '',
            'comment' : self.comment, 
            'routine' : self.routine, 
            'category' : self.done, 
            'done': self.done,
            'is_duetoday': self.is_duetoday,
            'is_duetomorrow': self.is_duetomorrow,
            'is_dueyesterday': self.is_dueyesterday,
            'duration': self.duration,
           }

    def in_collection(self, collection):
        return any([x['id'] == self.jsonized()['id'] and x['donedate'] == self.jsonized()['donedate'] for x in collection]) 

    def add_tags_by_name(self, tag_names):
        for tname in tag_names:
            tag = Tag.get_tag(tname)
            if not tag: 
                tag = Tag.new_tag(tname)
            self.tags.append(tag.key())
                
            if not self.usermodel.has_tag(tag.name):
                self.usermodel.usedtags.append(tag.key())     
        self.usermodel.put()
        self.put()

    def get_tags_name(self):
        return [Tag.get(t).name for t in self.tags]

    def done_item(self, user, misc=''):
        item_id = self.key().id()
        user_id = user.key().id()
        if self.usermodel.key().id() != user_id:
            return False

        if self.routine == 'none':
            self._done_(user)

        if self.routine == "daily" and misc != 'y':
            self._done_daily(user)
            
        if self.routine == "daily" and misc == 'y':
            self._done_last_daily(user)

        memcache.set("item:%s" % item_id, self)
        from models.user import get_user
        user = get_user(user_id)
        user.incr_done_items()
        user.decr_todo_items()
        return True

    def _done_(self,user):
        assert self.routine == 'none'
        user_id = user.key().id()
        self.donedate = datetime.datetime.now()
        self.done = True
        self.put()
        memcache.event('doneitem', user_id)

    def _done_daily(self,user):
        assert self.routine == "daily"
        user_id = user.key().id()
        item_id = int(self.key().id())

        if not self.has_done_today:
            new_routinelog_item = tarsusaRoutineLogItem(routine=self.routine, user=user.user, routineid=item_id)
            new_routinelog_item.put()

            today = datetime.date.today()
            memcache.set("item:%s:has_done_in:%s" % (item_id, today), True)

            memcache.event('doneroutineitem_daily_today', user_id)
            memcache.event('refresh_dailyroutine', user_id)

    def _done_last_daily(self, user):
        assert self.routine == "daily"
        user_id = user.key().id()
        item_id = int(self.key().id())
        new_routinelog_item = tarsusaRoutineLogItem(routine=self.routine, user=user.user, routineid=item_id)
        yesterday = datetime.datetime.combine(datetime.date.today() - ONE_DAY, datetime.time(0))
        new_routinelog_item.donedate = yesterday
        is_already_done = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate > :2 and donedate < :3", item_id, yesterday - ONE_DAY , datetime.datetime.combine(yesterday, datetime.time(0)) - ONE_SECOND)
        if is_already_done.count() < 1:
            new_routinelog_item.put()
            memcache.event('doneroutineitem_daily_yesterday', user_id)
            memcache.event('refresh_dailyroutine', user_id)

    def undone_item(self, user, misc=''):
        item_id = self.key().id()
        user_id = user.key().id()
        if self.usermodel.key().id() != user_id:
            return False

        if self.routine == 'none':
            self._undone_(user)

        if self.routine == "daily" and misc != 'y':
            self._undone_daily(user)
            
        if self.routine == "daily" and misc == 'y':
            self._undone_last_daily(user)

        memcache.set("item:%s" % item_id, self)
        from models.user import get_user
        user = get_user(user_id)
        user.incr_todo_items()
        user.decr_done_items()
        return True

    def _undone_(self,user):
        assert self.routine == 'none'
        user_id = user.key().id()
        self.donedate = None
        self.done = False
        self.put()
        memcache.event('undoneitem', user_id)

    def _undone_daily(self,user):
        assert self.routine == "daily"
        user_id = user.key().id()
        item_id = int(self.key().id())
        tarsusaRoutineLogItemCollection_ToBeDeleted = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate < :2", item_id, datetime.datetime.now())
    
        yesterday = datetime.datetime.now() - ONE_DAY
        for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
            if result.donedate < datetime.datetime.now() and result.donedate.date() != yesterday.date() and result.donedate > yesterday:
                result.delete()

        memcache.event('undoneroutineitem_daily_today', user_id)
        memcache.event('refresh_dailyroutine', user_id)


    def _undone_last_daily(self, user):
        assert self.routine == "daily"
        user_id = user.key().id()
        item_id = int(self.key().id())
        yesterday = datetime.datetime.combine(datetime.date.today() - ONE_DAY,datetime.time(0))
        tarsusaRoutineLogItemCollection_ToBeDeleted = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE routineid = :1 and donedate > :2 and donedate < :3", item_id, yesterday-ONE_DAY, datetime.datetime.combine(yesterday, datetime.time(0)) - ONE_SECOND)
                #datetime.datetime.today())
        for result in tarsusaRoutineLogItemCollection_ToBeDeleted:
            if result.donedate < datetime.datetime.now() and result.donedate > yesterday:
                result.delete()
        
        memcache.event('undoneroutineitem_daily_yesterday', user_id)
        memcache.event('refresh_dailyroutine', user_id)

    @staticmethod
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

    @classmethod
    def AddItem(cls, user_id, rawName, rawComment='', rawRoutine='none', rawPublic='private', rawInputDate='', rawTags=None):
        import cgi
        
        user = tarsusaUser.get_user(int(user_id))
        if not user:
            return

        item_name = cgi.escape(rawName)
        if not item_name:
            return
       
        if rawRoutine not in ["none", "daily", "weekly", "monthly", "seasonly", "yearly"]:
            return
        
        if rawPublic not in ['private', 'public', 'publicOnlyforFriends']:
            return

        item_comment = cgi.escape(rawComment)[:500]

        item = tarsusaItem(user=user.user, name=item_name, comment=item_comment, \
                routine=rawRoutine, public=rawPublic, usermodel=user, \
                done=False)

        if rawInputDate and rawInputDate == datetime.datetime.today().strftime("%Y-%m-%d"):
            item.expectdate = datetime.datetime.now()
        else:
            item.expectdate = None

        item_tags = None 
        if rawTags:
            item_tags = cgi.escape(rawTags).split(",")
            if item_tags:
                item.add_tags_by_name(item_tags)

        item.put()
        item_id = item.key().id()
        user_id = user.key().id()
        memcache.set("item:%s" % item_id, item)

        taskqueue.add(url='/workers/stats_after_add', params={'user_id': user_id, 'routine':rawRoutine, 'public':rawPublic})
        return item_id

class tarsusaRoutineLogItem(db.Model):
    user = db.UserProperty()
    routineid = db.IntegerProperty()
    routine = db.StringProperty(required=True, choices=set(["none", "daily", "weekly", "monthly", "seasonly", "yearly"]))
    donedate = db.DateTimeProperty(auto_now_add=True)

    @staticmethod
    @cache("routineitem:{item_id}")
    def get_item(item_id):
        try:
            item = tarsusaRoutineLogItem.get_by_id(int(item_id))
        except:
            return None
        return item

    @classmethod
    @cache("routineitem:count", ONE_HOUR)
    def count(self):
        return db.Query(tarsusaRoutineLogItem,keys_only=True).count(99999999)
