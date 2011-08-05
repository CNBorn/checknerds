# -*- coding: utf-8 -*-
# CheckNerds - www.checknerds.com
from google.appengine.api import memcache
from google.appengine.api.memcache import get, set, delete, flush_all

refresh_roles = {
        'additem' : ('itemstats', 'itemlist', 'tag'),
        'addpublicitem' : ('itemstats', 'itemlist', 'tag', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony'),
        'addroutineitem_daily' : ('itemstats','dailyroutine_items', 'dailyroutine_today', 'dailyroutine_yesterday', 'tag'),
        'edititem' :  ('itemstats', 'itemlist', 'tag', 'donelog'),
        'editpublicitem' : ('itemstats', 'itemlist', 'tag', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony', 'donelog'),
        'editroutineitem_daily' : ('itemstats','dailyroutine_items', 'dailyroutine_today', 'dailyroutine_yesterday', 'itemlist', 'tag', 'donelog'),
        'deleteitem' : ('itemstats', 'itemlist', 'doneitemlist','tag', 'donelog'),
        'deletepublicitem' : ('itemstats', 'itemlist', 'doneitemlist', 'tag', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony', 'donelog'),
        'deleteroutineitem_daily' : ('itemstats','dailyroutine_items', 'dailyroutine_today','dailyroutine_yesterday', 'tag', 'donelog'),
        'doneitem' : ('itemstats', 'itemlist', 'doneitemlist', 'donelog'),
        'donepublicitem' : ('itemstats', 'itemlist', 'doneitemlist', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony', 'donelog'),
        'doneroutineitem_daily_today' : ('dailyroutine_items','dailyroutine_today', 'donelog'),
        'doneroutineitem_daily_yesterday' : ('dailyroutine_items','dailytouine_yesterday', 'donelog'),
        'refresh_dailyroutine': ('dailyroutine_items','donelog'), #this is a clean one,.
        'undoneitem' : ('itemstats', 'doneitemlist', 'itemlist', 'donelog'),
        'undonepublicitem' : ('itemstats', 'itemlist', 'doneitemlist', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony', 'donelog'),
        'undoneroutineitem_daily_today' : ('dailyroutine_items','dailyroutine_today', 'donelog'),
        'undoneroutineitem_daily_yesterday' : ('dailyroutine_items','dailytouine_yesterday', 'donelog'),
        'addfriend' : ('friendstats', 'mainpage_friends','friendstatus'),
        'removefriend' : ('friendstats', 'mainpage_friends','friendstatus'),
        }

def event(key, CurrentUserid):
    if key not in refresh_roles.keys(): return False
    for obj in refresh_roles[key]:
        memkeydel_status = delete("%s:%s" % (obj, CurrentUserid)) 
    return True
