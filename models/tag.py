# -*- coding: utf-8 -*-
import sys
sys.path.append("../")

from google.appengine.ext import db

class Tag(db.Model):
    name = db.StringProperty()
    count = db.IntegerProperty()
