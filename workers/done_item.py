# -*- coding: utf-8 -*-

import sys
sys.path.append("../")

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from models.user import get_user
from models.item import tarsusaItem

class DoneItemWorker(webapp.RequestHandler):
    def post(self):
        user_id = self.request.get('user_id')
        item_id = self.request.get('item_id')
        misc = self.request.get('misc')

        user = get_user(user_id)
        item = tarsusaItem.get_item(item_id) 
        if item:
            item.done_item(user, misc)

def main():
    application = webapp.WSGIApplication([
        ('/workers/done_item', DoneItemWorker),
        ],
        debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
