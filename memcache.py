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
		'addroutineitem_daily' : ('itemstats', 'dailyroutine_today', 'dailyroutine_yesterday', 'tag'),
		'edititem' :  ('itemstats', 'itemlist', 'tag', 'donelog'),
		'editpublicitem' : ('itemstats', 'itemlist', 'tag', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony', 'donelog'),
		'editroutineitem_daily' : ('itemstats', 'dailyroutine_today', 'dailyroutine_yesterday', 'itemlist', 'tag', 'donelog'),
		'deleteitem' : ('itemstats', 'itemlist' ,'tag', 'donelog'),
		'deletepublicitem' : ('itemstats', 'itemlist', 'tag', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony', 'donelog'),
		'deleteroutineitem_daily' : ('itemstats', 'dailyroutine_today','dailyroutine_yesterday', 'tag', 'donelog'),
		'doneitem' : ('itemstats', 'itemlist', 'donelog'),
		'donepublicitem' : ('itemstats', 'itemlist', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony', 'donelog'),
		'doneroutineitem_daily_today' : ('dailyroutine_today', 'donelog'),
		'doneroutineitem_daily_yesterday' : ('dailytouine_yesterday', 'donelog'),
		'undoneitem' : ('itemstats', 'itemlist', 'donelog'),
		'undonepublicitem' : ('itemstats', 'itemlist', 'mainpage', 'mainpage_publicitems', 'mainpage_publicitems_anony', 'donelog'),
		'undoneroutineitem_daily_today' : ('dailyroutine_today', 'donelog'),
		'undoneroutineitem_daily_yesterday' : ('dailytouine_yesterday', 'donelog'),
		'addfriend' : ('friendstats', 'mainpage_friends'),
		'removefriend' : ('friendstats', 'mainpage_friends'),
		}

def event(key, CurrentUserid):

	logging.info('%s : %s event' % (CurrentUserid, key))

	for role in refresh_roles:
		if re.match(role, key):
			for obj in refresh_roles[role]:
				if memcache.delete("%s_%s" % (CurrentUserid, obj)) != 2:
					logging.info('not delete' + ("%s_%s" % (CurrentUserid, obj)))
				else:
					logging.info("deleted: %s_%s" % (CurrentUserid, obj))
	
	return True

def get(key):
	
	item = memcache.get(key)
	if item == None:
		logging.debug('NONE Memcache item %s' % key)
		return None
	else:
		return item

def set(key, value, time=0):
	
	if memcache.set(key, value, time):
		logging.debug('SET Memcache item %s' % key)
		return True
	else:
		logging.error('SET Memcache item %s FAILED!' % key)
		return False

def get_item(key, CurrentUserID):
	itemoperate = ("%s_%s" % (str(CurrentUserID), key))
	item = memcache.get(itemoperate)
	if item == None:
		logging.debug('NONE Memcache item %s' % itemoperate)
		return None
	else:
		logging.debug('HIT Memcache item %s' % itemoperate)
		return item

def set_item(key, value, CurrentUserID, time=0):
	if str(CurrentUserID) == 'global':
		time += 300
	
	itemoperate = ("%s_%s" % (str(CurrentUserID), key))
	if memcache.set(itemoperate, value, time):
		logging.debug('SET Memcache item %s' % itemoperate)
		return True
	else:
		logging.debug('FAILED SET Memcache item %s' % itemoperate)
		return False

