# -*- coding: utf-8 -*-
# CheckNerds - www.checknerds.com
from google.appengine.api import memcache

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
    if key not in refresh_roles.keys(): return False
    for obj in refresh_roles[key]:
        memkeydel_status = memcache.delete("%s:%s" % (obj, CurrentUserid)) 
    return True

def get(key):
    item = memcache.get(key)
    if item == None:
        return None
    return item

def set(key, value, time=0):
    if memcache.set(key, value, time):
        return True
    return False

def get_item(key, user_id):
    mc_key = ("%s:%s" % (key, str(user_id)))
    item = memcache.get(mc_key, None)
    return item

def set_item(key, value, user_id, time=0):
    if str(user_id) == 'global':
        time += 300
    mc_key = ("%s:%s" % (key, str(user_id)))
    if memcache.set(mc_key, value, time):
        return True
    return False

def delete(key):
    return memcache.delete(key)

def delete_item(key, user_id):
    mc_key = ("%s:%s" % (key, str(user_id)))
    memcache.delete(mc_key)
    return True
