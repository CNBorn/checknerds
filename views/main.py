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
from models import tarsusaUser, tarsusaItem

class MainPage(tarsusaRequestHandler):

    def get(self):

        if self.chk_login():
            CurrentUser = self.get_user_db()
            template_values = {
                    'PrefixCSSdir': "/",
                    'UserLoggedIn': 'Logged In',
                    'UserNickName': cgi.escape(CurrentUser.dispname),
                    'UserID': CurrentUser.key().id(),
            }
            path = '../pages/calit2/index.html'
            strCachedWelcomePage = template.render(path, template_values)
        
        else:           
            #WelcomePage for Non-registered Users.
            IsCachedWelcomePage = memcache.get_item('strCachedWelcomePage', 'global')
            
            if IsCachedWelcomePage:
                strCachedWelcomePage = IsCachedWelcomePage
            else:
                template_values = {
                    'PrefixCSSdir': "/",
                    'UserNickName': "访客",
                    'AnonymousVisitor': "Yes",
                    'htmltag_TotalUser': tarsusaUser.count(),
                    'htmltag_TotaltarsusaItem': tarsusaItem.count(),
                }

                path = '../pages/calit2/welcome.html'
                strCachedWelcomePage = template.render(path, template_values)
                memcache.set_item("strCachedWelcomePage", strCachedWelcomePage, 'global')

        self.response.out.write(strCachedWelcomePage)



def main():
    application = webapp.WSGIApplication([
        ('/', MainPage)], \
            debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
