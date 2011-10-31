# -*- coding: utf-8 -*-

# ****************************************************************
# CheckNerds - www.checknerds.com
# - tarsusaCore.py
# http://cnborn.net, http://twitter.com/CNBorn
#
# ****************************************************************

import cgi
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

from libs import shardingcounter

from views import service
from utils import cache

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
        item.add_tags_by_name(item_tags)

    user_id = user.key().id()
    item.put()
    item_id = item.key().id()
    shardingcounter.increment("tarsusaItem")
    memcache.delete("itemstats:%s" % user_id)
    memcache.set("item:%s" % item_id, item)
    return item_id

