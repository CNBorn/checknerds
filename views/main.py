# -*- coding: utf-8 -*-
import sys
sys.path.append("../")

from google.appengine.ext import webapp
from base import tarsusaRequestHandler

import wsgiref.handlers

class MainPage(tarsusaRequestHandler):
    def get(self):
        self.redirect('/beta')

def main():
    application = webapp.WSGIApplication([('/', MainPage)], \
            debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
