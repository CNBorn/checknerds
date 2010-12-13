# -*- coding: utf-8 -*-
import sys
sys.path.append("../")

from google.appengine.ext import webapp
from base import tarsusaRequestHandler

import wsgiref.handlers

class LoginPage(tarsusaRequestHandler):
    def get(self):
        self.redirect(self.get_login_url(True))

class SignOutPage(tarsusaRequestHandler):
    def get(self):
        self.redirect(self.get_logout_url(True))

def main():
    application = webapp.WSGIApplication([                                       ('/Login.+',LoginPage),
                ('/Logout.+',SignOutPage),
                ],debug=True)

    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
