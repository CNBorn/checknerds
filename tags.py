# -*- coding: utf-8 -*-
import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db

import datetime
import string
from google.appengine.ext.webapp import template
from google.appengine.api import images

from modules import *
from base import *
import logging
import urllib

def get_tag_list(user_id):

    user = tarsusaUser.get_by_id(user_id)

    if user.usedtags:
        tag_names = []
        tags = []
        for each_tag in user.usedtags:
            tags.append(each_tag)
            tag_names.append(db.get(each_tag).name)

        tag_names = list(set(tag_names))
        tags = list(set(tags))

    return tag_names
