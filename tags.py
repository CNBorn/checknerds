# -*- coding: utf-8 -*-
from google.appengine.ext import db
from modules import tarsusaUser, Tag

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
