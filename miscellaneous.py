# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename California
# - miscellaneous.py
# Copyright (C) CNBorn, 2008-2010
# http://cnborn.net, http://twitter.com/CNBorn
#
# **************************************************************** 

import os
import sys

import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db

import datetime
import string
from google.appengine.ext.webapp import template
from google.appengine.api import images


from modules import *
from base import *

import memcache
import logging
import tarsusaCore

class GuestbookPage(tarsusaRequestHandler):
    def get(self):
        strAboutPageTitle = "CheckNerds项目 - Guestbook"
        strAboutPageContent = '''<br /><iframe src="http://spreadsheets.google.com/embeddedform?key=pWd4_W1-LSL4xnGNRuHq6JA" width="95%" height="735" frameborder="0" marginheight="0" marginwidth="0">正在加载...</iframe><BR>
        
        '''
        ## Get Current User.
        # code below are comming from GAE example
        q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", users.get_current_user())
        CurrentUser = q.get()
    

        try:

            template_values = {
                    'UserLoggedIn': 'Logged In',
                    'UserNickName': cgi.escape(users.get_current_user().nickname()),
                    'UserID': CurrentUser.key().id(),
                    'singlePageTitle': strAboutPageTitle,
                    'singlePageContent': strAboutPageContent,
            }
        
        except:

            
            template_values = {
                
                'UserNickName': "访客",
                'AnonymousVisitor': "Yes",
                'singlePageTitle': strAboutPageTitle,
                'singlePageContent': strAboutPageContent,

            }


    
        path = os.path.join(os.path.dirname(__file__), 'pages/simple_page.html')
        self.response.out.write(template.render(path, template_values))

class BlogPage(tarsusaRequestHandler):
    def get(self):
        
        #from google.appengine.api import urlfetch
        # GAE中对远程网页的获取不能通过urllib，只能通过google自己的urlfetch   

        #url = "http://feed.feedsky.com/cnborn"
        #result = urlfetch.fetch(url)
        
        #if result.status_code == 200:
            
            #import xml.sax
            #from xml.dom import minidom
            #xmldoc = minidom.parseString(result.content.decode('utf-8')))

            #parser = rss_parser()
            #strAboutPageContent = result.content.decode('utf-8')


        #strAboutPageContent = '''Coming soon.<BR><BR>''' #+ d.entries[0].title + d.entries[0].link + d.entries[0].description + d.entries[0].date + d.entries[0].date_parsed + d.entries[0].id

        strAboutPageContent = '''<div id="twitter_div"><ul id="twitter_update_list"></ul></div>
                                <script type="text/javascript" src="http://twitter.com/javascripts/blogger.js"></script>
                                <script type="text/javascript" src="http://twitter.com/statuses/user_timeline/checknerds.json?callback=twitterCallback2&amp;count=10"></script>'''

        strAboutPageTitle = "CheckNerds - Recent Updates (powered by Twitter)"
        
        if self.chk_login():
            CurrentUser = self.get_user_db()
            template_values = {
                    'UserLoggedIn': 'Logged In',
                    'UserNickName': cgi.escape(users.get_current_user().nickname()),
                    'UserID': CurrentUser.key().id(),
                    'singlePageTitle': strAboutPageTitle,
                    'singlePageContent': strAboutPageContent,
            }
        else:
            template_values = {             
                'UserNickName': "访客",
                'AnonymousVisitor': "Yes",
                'singlePageTitle': strAboutPageTitle,
                'singlePageContent': strAboutPageContent,
            }

    
        path = os.path.join(os.path.dirname(__file__), 'pages/simple_page.html')
        self.response.out.write(template.render(path, template_values))

class AboutPage(tarsusaRequestHandler):
    def get(self):
        
        import os
        strdevVersion = os.environ['CURRENT_VERSION_ID']

        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login():
            CurrentUser = self.get_user_db()        
            template_values = {
                    'UserLoggedIn': 'Logged In',
                    'UserNickName': cgi.escape(CurrentUser.dispname),
                    'UserID': CurrentUser.key().id(),
                    'devVersion': strdevVersion,
            }
        
        else:           
            template_values = {
                'UserNickName': "访客",
                'AnonymousVisitor': "Yes",
                'devVersion': strdevVersion,
            }
    
        path = os.path.join(os.path.dirname(__file__), 'pages/about.html')
        self.response.out.write(template.render(path, template_values))

class StatsticsPage(tarsusaRequestHandler):
    def get(self):
        
        # Show statstics information.

        if self.chk_login():
            CurrentUser = self.get_user_db()
        else:
            self.redirect('/')
        
        TotalUserCount = db.GqlQuery("SELECT * FROM tarsusaUser").count()
        TotaltarsusaItem = db.GqlQuery("SELECT * FROM tarsusaItem").count()
        
        htmltag = ''
        htmltag += 'Uptime: ' + str(datetime.datetime.now() - datetime.datetime(2008,8,26,20,0,0))
        htmltag += '<br />Project Started Since: ' + str(datetime.date.today() - datetime.date(2008, 7, 19)) + ' ago.'
        htmltag += '<br />User Account: ' + str(TotalUserCount)
        htmltag += '<br />Total Items: ' + str(TotaltarsusaItem)

        try:
            htmltag += '<br /><br /><b>memcached stats:</b>'
            stats = memcache.get_stats()    
            htmltag += "<br /><b>Cache Hits:</b>" + str(stats['hits'])
            htmltag += "<br /><b>Cache Misses:</b>" +str(stats['misses'])                   
            htmltag += "<br /><b>Total Requested Cache bytes:</b>" +str(stats['byte_hits'])
            htmltag += "<br /><b>Total Cache items:</b>" +str(stats['items'])
            htmltag += "<br /><b>Total Cache bytes:</b>" +str(stats['bytes'])
            htmltag += "<br /><b>Oldest Cache items:</b>" +str(stats['oldest_item_age'])
        except:
            pass

        template_values = {
            'UserLoggedIn': 'Logged In',                
            'UserNickName': cgi.escape(self.login_user.nickname()),
            'UserID': CurrentUser.key().id(),   
            
            'singlePageTitle': 'Statstics',
            'singlePageContent': htmltag,

            'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
            'htmltag_TotalUser': TotalUserCount,
            'htmltag_TotaltarsusaItem': TotaltarsusaItem,

        }
        
        #Manupilating Templates 
        path = os.path.join(os.path.dirname(__file__), 'pages/simple_page.html')
        self.response.out.write(template.render(path, template_values))

class DocsPage(tarsusaRequestHandler):
    def get(self):

        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login():
            CurrentUser = self.get_user_db()        
            template_values = {
                    'PrefixCSSdir': "/",
                    'UserLoggedIn': 'Logged In',
                    'UserNickName': cgi.escape(CurrentUser.dispname),
                    'UserID': CurrentUser.key().id(),
            }
        
        else:           
            template_values = {
                'PrefixCSSdir': "/",
                'UserNickName': "访客",
                'AnonymousVisitor': "Yes",
            }
        
        pageid = self.request.path[len('/docs/'):]
        if pageid == '':
            pageid = 'index'
        path = os.path.join(os.path.dirname(__file__), 'pages/docs/' + pageid + '.html')

        self.response.out.write(template.render(path, template_values))

class LabsPage(tarsusaRequestHandler):
    def get(self):

        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login():
            CurrentUser = self.get_user_db()        
            template_values = {
                    'PrefixCSSdir': "/",
                    'UserLoggedIn': 'Logged In',
                    'UserNickName': cgi.escape(CurrentUser.dispname),
                    'UserID': CurrentUser.key().id(),
            }
        
        else:           
            template_values = {
                'PrefixCSSdir': "/",
                'UserNickName': "访客",
                'AnonymousVisitor': "Yes",
            }
        
        pageid = self.request.path[len('/docs/'):]
        if pageid == '':
            pageid = 'index'
        path = os.path.join(os.path.dirname(__file__), 'pages/labs/index.html')

        self.response.out.write(template.render(path, template_values))
    


class FlushCache(tarsusaRequestHandler):
    def get(self):
        from google.appengine.api import memcache 
        memcache.flush_all()
        logging.info("Memcache Flushed by force.")
        self.redirect('/')

class cron_flushcache(tarsusaRequestHandler):
    def get(self):
        from google.appengine.api import memcache 
        memcache.flush_all()
        logging.info("memcache flushed by cron.")
        return True

#I will evantully add a memcache-api-reset function here.


class CaliforniaPage(tarsusaRequestHandler):
    def get(self):

        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login():
            CurrentUser = self.get_user_db()
            
            template_values = {
                    'PrefixCSSdir': "/",
                    'UserLoggedIn': 'Logged In',
                    'UserNickName': cgi.escape(CurrentUser.dispname),
                    'UserID': CurrentUser.key().id(),
            }
            path = os.path.join(os.path.dirname(__file__), 'pages/calit2/index.html')
        
        else:           
            #WelcomePage for Non-registered Users.

            IsCachedWelcomePage = memcache.get_item('strCachedWelcomePage', 'global')
            
            if IsCachedWelcomePage:
                strCachedWelcomePage = IsCachedWelcomePage
            else:
                TotalUserCount = tarsusaCore.get_count_tarsusaUser()
                TotaltarsusaItem = tarsusaCore.get_count_tarsusaItem()

                template_values = {
                    'PrefixCSSdir': "/",
                    'UserNickName': "访客",
                    'AnonymousVisitor': "Yes",
                    'htmltag_TotalUser': TotalUserCount,
                    'htmltag_TotaltarsusaItem': TotaltarsusaItem,
                }

                #Manupilating Templates 
                path = os.path.join(os.path.dirname(__file__), 'pages/calit2/welcome.html')
                strCachedWelcomePage = template.render(path, template_values)
                memcache.set_item("strCachedWelcomePage", strCachedWelcomePage, 'global')

        self.response.out.write(strCachedWelcomePage)

def main():
    application = webapp.WSGIApplication([('/about',AboutPage),
                                       ('/blog',BlogPage),
                                       ('/docs.+', DocsPage),
                                       ('/labs.+', LabsPage),
                                       ('/statstics',StatsticsPage),
                                       ('/flushcache', FlushCache),
                                       ('/cron_flushcache', cron_flushcache),
                                       ('/beta', CaliforniaPage),
                                       ('/guestbook', GuestbookPage)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
