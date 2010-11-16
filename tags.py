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

def get_tag_item_ids_list(tag_name, user_id):

    if not tag_name: return False

    items = []
    tag = db.Query(Tag).filter("name =", tag_name).get()
    user = tarsusaUser.get_by_id(user_id)

    user_items = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 ORDER BY done, date DESC", user.user)
    for each_item in user_items:
        for each_tag in each_item.tags:
            if db.get(each_tag).name == tag_name:
                items.append(each_item.key().id())
    return items
