# -*- coding: utf-8 -*-

import sys
sys.path.append("../")

from google.appengine.ext import db
from models.user import tarsusaUser

import memcache

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


