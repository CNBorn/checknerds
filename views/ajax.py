# -*- coding: utf-8 -*-

# CheckNerds - www.checknerds.com
# - ajax.py
# http://cnborn.net, http://twitter.com/CNBorn

import sys
sys.path.append("../")

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import cgi, datetime, os, time
from models import tarsusaUser, tarsusaItem
from base import tarsusaRequestHandler
from google.appengine.ext.webapp import template

from utils import login

class DueToday(tarsusaRequestHandler):
    @login
    def get(self):
        item_id = self.request.path.split('/')[-1]
        tarsusaItem.get_item(item_id).set_duetoday()
        self.response_json({"r":"ok"})

class DueTomorrow(tarsusaRequestHandler):
    @login
    def get(self):
        item_id = self.request.path.split('/')[-1]
        tarsusaItem.get_item(item_id).set_duetomorrow()
        self.response_json({"r":"ok"})

class DoneItem(tarsusaRequestHandler):
    @login
    def get(self):
        item_id = self.request.path.split('/')[-1]
        
        DoneYesterdaysDailyRoutine = False
        if item_id == 'y':
            item_id = self.request.path.split('/')[-2]
            DoneYesterdaysDailyRoutine = True

        CurrentUser = self.get_user_db()
        Misc = 'y' if DoneYesterdaysDailyRoutine else ''
        
        item = tarsusaItem.get_item(item_id) 
        item.done_item(CurrentUser, Misc)
        self.response_json({"r":"ok"})

class RemoveItem(tarsusaRequestHandler):
    @login
    def get(self):
        item_id = self.request.path.split('/')[-1]
        current_user = self.get_user_db()
        item = tarsusaItem.get_item(item_id)
        remove_status = item.delete_item(current_user.key().id())
        self.response_json({"r":remove_status})

class UnDoneItem(tarsusaRequestHandler):
    @login
    def get(self):
        ItemId = self.request.path[12:]
        UndoneYesterdaysDailyRoutine = False
        if ItemId[-2:] == '/y':
            ItemId = self.request.path[12:-2]           
            UndoneYesterdaysDailyRoutine = True
        CurrentUser = self.get_user_db()
        item = tarsusaItem.get_item(ItemId) 
        Misc = 'y' if UndoneYesterdaysDailyRoutine else ''
        item.undone_item(CurrentUser, Misc)
        self.response_json({"r":"ok"})

class AddItemProcess(tarsusaRequestHandler):
    @login
    def post(self):
        CurrentUser = self.get_user_db()
        item2beadd_name = cgi.escape(self.request.get('name'))
        item2beadd_comment = cgi.escape(self.request.get('comment'))
        item_id = tarsusaItem.AddItem(CurrentUser.key().id(), item2beadd_name, item2beadd_comment, self.request.get('routine','none'), self.request.get('public', 'private'), self.request.get('inputDate'), self.request.get('tags'))

        if self.referer[-6:] == "/m/add":
            self.redirect("/m/todo")

        self.response_json({"r":item_id})


class ajax_error(tarsusaRequestHandler):
    def post(self):
        self.write("载入出错，请刷新重试")
    def get(self):
        self.write("载入出错，请刷新重试")

class render(tarsusaRequestHandler):
    @login
    def get(self):
        func = self.request.get("func")
        
        maxitems = int(self.request.get("maxitems", "15"))
        
        user = self.get_user_db()
        user_id = user.key().id()

        if func == "done":
            done_items = user.get_done_items(maxitems)
            self.response_json(done_items)

        elif func == "inbox":
            before_item_id = self.request.get("before_item_id",None)
            if before_item_id:
                undone_items = user.get_more_inbox_items(maxitems, before_item_id)
            else:
                undone_items = user.get_inbox_items(maxitems)
            self.response_json(undone_items)

        elif func == "dailyroutine":
            dailyroutine_items = tarsusaUser.get_user(user_id).get_items_duetoday()
            self.response_json(dailyroutine_items)

        elif func == "tomorrow":
            tomorrow_items = tarsusaUser.get_user(user_id).get_items_duetomorrow()
            self.response_json(tomorrow_items)

        elif func == "logs":
            done_items = user.get_donelog()
            formatted_done_items = tarsusaItem.format_done_logs(done_items)
            self.response_json(formatted_done_items)
 
class Stats(tarsusaRequestHandler):
    @login
    def get(self):
        current_user = self.get_user_db()
        results = {'date': time.strftime("%Y-%m-%d"),
                   'name': current_user.dispname,
                   'stats': current_user.get_itemstats(),
                   'pic_url': current_user.gravatar_url,
                  }
        self.response_json(results)

class GetItem(tarsusaRequestHandler):
    @login
    def get(self):
        item_id = self.request.path[8:]
        item = tarsusaItem.get_item(item_id)
        self.response_json(item.jsonized())

def main():
    application = webapp.WSGIApplication([
        (r'/ajax/render/.*', render),
        ('/ajax/.+',ajax_error),
        ('/j/done/\\d+',DoneItem),
        ('/j/undone/\\d+',UnDoneItem),
        ('/duetoday/\\d+',DueToday),
        ('/duetomorrow/\\d+',DueTomorrow),
        ('/j/delete/\\d+', RemoveItem),
        ('/additem',AddItemProcess),
        ('/j/item/\\d+',GetItem),
        ('/j/stats/', Stats),
        ],
        debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
