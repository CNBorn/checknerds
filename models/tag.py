# -*- coding: utf-8 -*-
import sys
sys.path.append("../")

from google.appengine.ext import db
from utils import cache

class Tag(db.Model):
    name = db.StringProperty()
    count = db.IntegerProperty()

    @classmethod
    @cache("tag:{name}")
    def get_tag(cls, name):
        tag = db.Query(cls).filter("name =", name).get()
        return tag

    @classmethod
    def new_tag(cls, name):
        tag = cls.get_tag(name)
        if not tag:
            tag = cls(name=name)
            tag.put()
        return tag

