# -*- coding: utf-8 -*-
# CheckNerds 
# - memcache.py
# Cpoyright (C) CNBorn, 2008
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn

import datetime
import string
from google.appengine.api import memcache

from modules import *
from base import *
import logging
import re

#Learnt from Plog.
refresh_roles = {
		'.+:page:.+' : ('comment', 'post', 'config', 'blogroll', 'upload'),
		'(guest|login|admin):widget:recentcomments.*' : ('comment', 'config'),
		'(guest|login|admin):widget:recentposts.*' : ('post', 'config'),
		'(guest|login|admin):widget:blogroll.*' : ('blogroll', 'config'),
		'(guest|login|admin):widget:.*' : ('comment', 'post', 'blogroll', 'config'),
		'feed:tag:.*' : ('post', 'config'),
		'additem' : ('itemstats', 'itemlist', 'tag'),
		'addroutineitem_daily' : ('itemstats', 'dailyroutine_today', 'dailyroutine_yesterday', 'tag'),
		'edititem' :  ('itemstats', 'itemlist', 'tag'),
		'editroutineitem_daily' : ('itemstats', 'dailyroutine_today', 'dailyroutine_yesterday', 'itemlist', 'tag'),
		'deleteitem' : ('itemstatus', 'itemlist' ,'tag'),
		'deleteroutineitem_daily' : ('itemstats', 'dailyroutine_today','dailyroutine_yesterday', 'tag'),
		'doneitem' : ('itemstats', 'itemlist'),
		'doneroutineitem_daily_today' : ('dailyroutine_today'),
		'doneroutineitem_daily_yesterday' : ('dailytouine_yesterday'),
		'undoneitem' : ('itemstats', 'itemlist'),
		'undoneroutineitem_daily_today' : ('dailyroutine_today'),
		'undoneroutineitem_daily_yesterday' : ('dailytouine_yesterday'),
		'addfriend' : ('friendstats', ''),
		'removefriend' : ('friendstats', ''),
		}

def check_expire(strkey):
	for role in refresh_roles:
		if re.match(role, strkey):
			for obj in refresh_roles[role]:
				#if memcache_item.timestamp < obj_last_modify[obj]:
				return True
					

			return False
	#logging.warning('No refresh role for %s' % key)
	return True

def event(key, CurrentUserid):

	logging.info('%s : %s event' % (CurrentUserid, key))

	for role in refresh_roles:
		if re.match(role, key):
			for obj in refresh_roles[role]:
				if memcache.delete("%s_%s" % (CurrentUserid, obj)) != 2:
					logging.info('not delete' + ("%s_%s" % (CurrentUserid, obj)) + str(memcache.delete("%s_%s" % (CurrentUserid, obj))))
				else:
					logging.info("delted: %s_%s" % (CurrentUserid, obj))
					
				#return "%s_%s" % (CurrentUserid, obj)
				#return True
	
	#return "%s_%s" % (CurrentUserid, obj)
	return True



def get(key):
	#key = key[:250]

	item = memcache.get(key)
	if item == None:
		logging.debug('NONE Memcache item %s' % key)
		return None
	else:
		return item
		#return item.value
		#if check_expire(item):
		#	logging.info('NEED REFRESH Memcache item %s' % key)
		#	return None
		#else:
		#	logging.debug('HIT Memcache item %s' % key)
		#	return item.value
def set(key, value, time=0):
	#key = key[:250]
	if memcache.set(key, value, time):
		logging.debug('SET Memcache item %s' % key)
		return True
	else:
		logging.error('SET Memcache item %s FAILED!' % key)
		return False


def get_item(key, CurrentUserID):
	#key = key[:250]
	itemoperate = ("%s_%s" % (str(CurrentUserID), key))
	item = memcache.get(itemoperate)
	if item == None:
		logging.debug('NONE Memcache item %s' % itemoperate)
		return None
	else:
		logging.debug('HIT Memcache item %s' % itemoperate)
		return item

def set_item(key, value, CurrentUserID, time=0):
	#key = key[:250]
	itemoperate = ("%s_%s" % (str(CurrentUserID), key))
	if memcache.set(itemoperate, value, time):
		logging.debug('SET Memcache item %s' % itemoperate)
		return True
	else:
		logging.debug('FAILED SET Memcache item %s' % itemoperate)
		return False

