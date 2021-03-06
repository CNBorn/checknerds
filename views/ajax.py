# -*- coding: utf-8 -*-

# CheckNerds - www.checknerds.com
# - ajax.py
# http://cnborn.net, http://twitter.com/CNBorn

import sys
sys.path.append("../")

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import taskqueue

import time
from models import tarsusaUser, tarsusaItem
from base import tarsusaRequestHandler

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
       
        misc = ''
        if item_id == 'y':
            item_id = self.request.path.split('/')[-2]
            misc = 'y'
        
        user = self.get_user_db()
        user_id = user.key().id()
        taskqueue.add(url='/workers/done_item', params={'item_id': item_id, 'user_id':user_id, 'misc':misc})

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

class AddItem(tarsusaRequestHandler):
    @login
    def post(self):
        CurrentUser = self.get_user_db()
        item_id = tarsusaItem.AddItem(CurrentUser.key().id(), self.request.get('name'), self.request.get('comment'), self.request.get('routine','none'), self.request.get('public', 'private'), self.request.get('inputDate'), self.request.get('tags'))
        self.response_json({"r":item_id})

class FetchItem(tarsusaRequestHandler):
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
        (r'/j/fetch/.*', FetchItem),
        ('/j/done/\\d+',DoneItem),
        ('/j/undone/\\d+',UnDoneItem),
        ('/j/due_today/\\d+',DueToday),
        ('/j/due_tomorrow/\\d+',DueTomorrow),
        ('/j/delete/\\d+', RemoveItem),
        ('/j/add_item',AddItem),
        ('/j/item/\\d+',GetItem),
        ('/j/stats/', Stats),
        ],
        debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
