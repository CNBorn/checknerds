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

#Learnt from Plog.
refresh_roles = {
		'.+:page:.+' : ('comment', 'post', 'config', 'blogroll', 'upload'),
		'(guest|login|admin):widget:recentcomments.*' : ('comment', 'config'),
		'(guest|login|admin):widget:recentposts.*' : ('post', 'config'),
		'(guest|login|admin):widget:blogroll.*' : ('blogroll', 'config'),
		'(guest|login|admin):widget:.*' : ('comment', 'post', 'blogroll', 'config'),
		'feed:post' : ('post', 'config'),
		'feed:tag:.*' : ('post', 'config'),
		}

class MemcacheItem:
	def __init__(self, key, value):
		self.key = key
		self.value = value
		self.timestamp = datetime.utcnow()

def check_expire(memcache_item):
	for role in refresh_roles:
		if re.match(role, memcache_item.key):
			for obj in refresh_roles[role]:
				if memcache_item.timestamp < obj_last_modify[obj]:
					return True
			return False
	logging.warning('No refresh role for %s' % key)
	return True

def notify_update(key):
	logging.info('%s has been changed, some memcache item need update' % key)
	#obj_last_modify[key] = datetime.utcnow()
	#item = LastModified.get_by_key_name(key)
	#item.last_modified = obj_last_modify[key]
	#item.put()

