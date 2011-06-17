# -*- coding: utf-8 -*-

# CheckNerds - www.checknerds.com
# - ajax.py
# http://cnborn.net, http://twitter.com/CNBorn

import sys
sys.path.append("../")

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import cgi, datetime, os
from models import tarsusaUser, tarsusaItem
from base import tarsusaRequestHandler
from google.appengine.ext.webapp import template

from tarsusaCore import format_done_logs, format_items, AddItem
from utils import login

class DueToday(tarsusaRequestHandler):
    @login
    def get(self):
        item_id = self.request.path[10:]
        tarsusaItem.get_item(item_id).set_duetoday()
        self.response_json({"r":"ok"})

class DoneItem(tarsusaRequestHandler):
    @login
    def get(self):
        ItemId = self.request.path[10:]
        DoneYesterdaysDailyRoutine = False
        if ItemId[-2:] == '/y':
            ItemId = self.request.path[10:-2]           
            DoneYesterdaysDailyRoutine = True

        CurrentUser = self.get_user_db()
        Misc = 'y' if DoneYesterdaysDailyRoutine else ''
        
        item = tarsusaItem.get_item(ItemId) 
        item.done_item(CurrentUser, Misc)
        self.response_json({"r":"ok"})

class RemoveItem(tarsusaRequestHandler):
    @login
    def get(self):
        item_id = self.request.path[12:]
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
        item_id = AddItem(CurrentUser.key().id(), item2beadd_name, item2beadd_comment, self.request.get('routine','none'), self.request.get('public', 'private'), self.request.get('inputDate'), self.request.get('tags'))

        if self.referer[-6:] == "/m/add":
            self.redirect("/m/todo")

        self.response.headers.add_header('Content-Type', "application/json")
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
            self.response_json(format_items(done_items))

        elif func == "undone":
            before_item_id = self.request.get("before_item_id",None)
            if before_item_id:
                undone_items = user.get_more_undone_items(maxitems, before_item_id)
            else:
                undone_items = user.get_undone_items(maxitems)
            self.response_json(format_items(undone_items))

        elif func == "dailyroutine":
            dailyroutine_items = tarsusaUser.get_user(user_id).get_items_duetoday()
            self.response_json(format_items(dailyroutine_items))

        elif func == "logs":
            done_items = user.get_donelog()
            formatted_done_items = format_done_logs(done_items)
            self.response_json(formatted_done_items)
 
class sidebar(tarsusaRequestHandler):
    @login
    def get(self):
        current_user = self.get_user_db()
        template_values = {}

        operation_name = self.request.get("obj")
        template_name = self.request.get("template")

        if operation_name == 'user':
            template_values['UserInTemplate'] = current_user
            template_values['tarsusaItemCollection_Statstics'] = current_user.get_itemstats()

        template_values['UserNickName'] = cgi.escape(current_user.dispname)
        template_values['UserID'] = current_user.key().id()
        template_values['htmltag_today'] = datetime.date.today() 

        import urllib, hashlib
        default = self.host + '/img/default_avatar.jpg'
        size = 64
        gravatar_url = "http://www.gravatar.com/avatar.php?"
        gravatar_url += urllib.urlencode({'gravatar_id':hashlib.md5(current_user.user.email()).hexdigest(), 'default':default, 'size':str(size)})
        template_values['user_avatar'] = gravatar_url

        path = os.path.join(os.path.dirname(__file__), '../pages/%s/ajax_sidebar_%s.html' % (template_name, operation_name))
        self.write(template.render(path, template_values))


def main():
    application = webapp.WSGIApplication([
        (r'/ajax/render/.*', render),
        (r'/ajax/sidebar/.*', sidebar),
        ('/ajax/.+',ajax_error),
        ('/doneItem/\\d+',DoneItem),
        ('/undoneItem/\\d+',UnDoneItem),
        ('/duetoday/\\d+',DueToday),
        ('/removeItem/\\d+', RemoveItem),
        ('/additem',AddItemProcess),
        ],
        debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
