# -*- coding: utf-8 -*-
from google.appengine.dist import use_library
use_library('django', '1.2')
import sys
sys.path.append("../")

from base import tarsusaRequestHandler
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import cgi
import wsgiref.handlers
import memcache
from utils import cache
from models import tarsusaUser, tarsusaItem, tarsusaRoutineLogItem
from models.consts import MC_ONE_WEEK

class MainPage(tarsusaRequestHandler):

    @cache("homepage_logged:{self.get_user_db().key().id()}", MC_ONE_WEEK)
    def get_logged_page(self):
        CurrentUser = self.get_user_db()
        template_values = {
                'PrefixCSSdir': "/",
                'UserLoggedIn': 'Logged In',
                'UserNickName': cgi.escape(CurrentUser.dispname),
                'UserID': CurrentUser.key().id(),
        }
        path = '../pages/calit2/index_deploy.html'
        return template.render(path, template_values)
   
    @cache("homepage_welcome:0",3600)
    def get_welcome_page(self):
        template_values = {
            'PrefixCSSdir': "/",
            'UserNickName': "访客",
            'AnonymousVisitor': "Yes",
            'htmltag_TotalUser': tarsusaUser.count(),
            'htmltag_TotaltarsusaItem': int(tarsusaItem.count()) + int(tarsusaRoutineLogItem.count()),
        }

        path = '../pages/calit2/welcome.html'
        return template.render(path, template_values)

    def get(self):
        if self.chk_login():
            strCachedWelcomePage = self.get_logged_page()
        else:           
            strCachedWelcomePage = self.get_welcome_page()
        self.response.out.write(strCachedWelcomePage)

def main():
    application = webapp.WSGIApplication([
        ('/', MainPage)], \
            debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
