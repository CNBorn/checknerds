# -*- coding: utf-8 -*-
#
# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename California
# - memcache.py
# Copyright (C) CNBorn, 2008-2009
# http://cnborn.net, http://twitter.com/CNBorn
#
# **************************************************************** 

import datetime
import string
from google.appengine.api import memcache

from modules import *
from base import *
import logging
import re

#Learnt from Plog.
refresh_roles = {
        'additem' : ('itemstats', 'itemlist', 'tag'),
        'addpublicitem' : ('itemstats', 'itemlist', 'tag', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony'),
        'addroutineitem_daily' : ('itemstats','dailyroutine_items', 'dailyroutine_today', 'dailyroutine_yesterday', 'tag'),
        'edititem' :  ('itemstats', 'itemlist', 'tag', 'donelog'),
        'editpublicitem' : ('itemstats', 'itemlist', 'tag', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony', 'donelog'),
        'editroutineitem_daily' : ('itemstats','dailyroutine_items', 'dailyroutine_today', 'dailyroutine_yesterday', 'itemlist', 'tag', 'donelog'),
        'deleteitem' : ('itemstats', 'itemlist' ,'tag', 'donelog'),
        'deletepublicitem' : ('itemstats', 'itemlist', 'tag', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony', 'donelog'),
        'deleteroutineitem_daily' : ('itemstats','dailyroutine_items', 'dailyroutine_today','dailyroutine_yesterday', 'tag', 'donelog'),
        'doneitem' : ('itemstats', 'itemlist', 'donelog'),
        'donepublicitem' : ('itemstats', 'itemlist', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony', 'donelog'),
        'doneroutineitem_daily_today' : ('dailyroutine_items','dailyroutine_today', 'donelog'),
        'doneroutineitem_daily_yesterday' : ('dailyroutine_items','dailytouine_yesterday', 'donelog'),
        'refresh_dailyroutine': ('dailyroutine_items','donelog'), #this is a clean one,.
        'undoneitem' : ('itemstats', 'itemlist', 'donelog'),
        'undonepublicitem' : ('itemstats', 'itemlist', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony', 'donelog'),
        'undoneroutineitem_daily_today' : ('dailyroutine_items','dailyroutine_today', 'donelog'),
        'undoneroutineitem_daily_yesterday' : ('dailyroutine_items','dailytouine_yesterday', 'donelog'),
        'addfriend' : ('friendstats', 'mainpage_friends','friendstatus'),
        'removefriend' : ('friendstats', 'mainpage_friends','friendstatus'),
        }

def event(key, CurrentUserid):

    logging.info('memcache - user %s : %s' % (CurrentUserid, key))

    for role in refresh_roles:
        if re.match(role, key):
            for obj in refresh_roles[role]:
                memkeydel_status = memcache.delete("%s:%s" % (obj, CurrentUserid)) 
                if memkeydel_status == 1:
                    #1=DELETE_ITEM_MISSING
                    logging.debug('missing: ' + ("%s_%s" % (CurrentUserid, obj)))
                elif memkeydel_status == 2:
                    #2=DELETE_SUCCESSFUL
                    logging.debug("deleted: %s_%s" % (CurrentUserid, obj))
                else:
                    #logging.debug('not delete' + ("%s_%s" % (CurrentUserid, obj)))
                    pass
    
    return True

#I think it is nonsense to see alot memcache missing info here.
def get(key):
    
    item = memcache.get(key)
    if item == None:
        #logging.debug('NONE Memcache item %s' % key)
        return None
    else:
        return item

def set(key, value, time=0):
    
    if memcache.set(key, value, time):
        #logging.debug('SET Memcache item %s' % key)
        return True
    else:
        #logging.error('SET Memcache item %s FAILED!' % key)
        return False

def get_item(key, user_id):
    mc_key = ("%s:%s" % (key, str(user_id)))
    item = memcache.get(mc_key)
    if not item:
        return None
    return item

def set_item(key, value, user_id, time=0):
    if str(user_id) == 'global':
        time += 300
    mc_key = ("%s:%s" % (key, str(user_id)))
    if memcache.set(mc_key, value, time):
        return True
    return False

