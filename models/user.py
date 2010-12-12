# -*- coding: utf-8 -*-

import sys
sys.path.append("../")

from google.appengine.ext import db
import memcache
import shardingcounter

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


