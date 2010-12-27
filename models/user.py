# -*- coding: utf-8 -*-

import sys
sys.path.append("../")

from google.appengine.ext import db
import memcache
import shardingcounter
from models.tag import Tag

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
        if self.usedtags:
            tag_names = []
            tags = []
            for each_tag in self.usedtags:
                tags.append(each_tag)
                tag_names.append(db.get(each_tag).name)

            tag_names = list(set(tag_names))
            tags = list(set(tags))

        return tag_names

    def tag_item_ids_list(tag_name):
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


def get_user(user_id):
    cached_user = memcache.get("user:%s" % user_id)
    if cached_user:
        return cached_user
    try:
        user = tarsusaUser.get_by_id(int(user_id))
    except:
        return None
    memcache.set("user:%s" % user_id, user)
    return user


