# -*- coding: utf-8 -*-

import sys
sys.path.append("../")

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import memcache
from libs import shardingcounter

class StatsAfterAddWorker(webapp.RequestHandler):
    def post(self):
        user_id = self.request.get('user_id')
        public = self.request.get('public')
        routine = self.request.get('routine')

        if routine == 'daily':
            memcache.event('addroutineitem_daily', user_id)
        else:
            memcache.event('additem', user_id)

        if public != 'private':
            memcache.event('addpublicitem', user_id)

        shardingcounter.increment("tarsusaItem")
        memcache.delete("itemstats:%s" % user_id)


def main():
    application = webapp.WSGIApplication([
        ('/workers/stats_after_add', StatsAfterAddWorker),
        ],
        debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
