# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename California
# - userpage.py
# 
# Author: CNBorn
# http://cnborn.net, http://twitter.com/CNBorn
#
# **************************************************************** 

import os

import urllib
import cgi
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db

import time
import datetime
from google.appengine.ext.webapp import template
from google.appengine.api import images

import memcache
import tarsusaCore
import patcher

from models import *
from base import tarsusaRequestHandler
import logging

class UserSettingPage(tarsusaRequestHandler):
    def get(self):
        userid = urllib.unquote(cgi.escape(self.request.path[6:-8])) ## Get the username in the middle of /user/1234/setting

        EditedUser = tarsusaUser.get_by_id(int(userid))
        CurrentUser = self.get_user_db()

        if not EditedUser and not CurrentUser:
            self.redirect("/")
            
        if CurrentUser.key().id() != EditedUser.key().id():
            self.redirect("/")

        from google.appengine.ext.db import djangoforms
        from django import newforms as forms 
        
        class ItemForm(djangoforms.ModelForm):
            
            ## Custom djangoforms.ModelForm,
            ## http://groups.google.com/group/google-appengine/browse_thread/thread/d3673d0ec7ead0e2
            
            mail =  forms.CharField(label='您的邮箱(不会公开，无法更改)',widget=forms.TextInput(attrs={'readonly':'','size':'30','maxlength':'30','value':EditedUser.user.email()})) 
            dispname = forms.CharField(label='显示名称',widget=forms.TextInput(attrs={'size':'30','maxlength':'30','value':EditedUser.dispname,'class':'sl'}))
            website = forms.CharField(label='您的网址(请加http://)',widget=forms.TextInput(attrs={'size':'36','maxlength':'36','value':EditedUser.website,'class':'sl'}))   
            apikey = forms.CharField(label="ApiKey(请勿泄露)", widget=forms.TextInput(attrs={'readonly':'', 'class':'sl', 'value':EditedUser.apikey}))

            class Meta:
                model = tarsusaUser
                exclude =['user','userid','usedtags','urlname','friends','datejoinin', 'notify_dailybriefing', 'notify_dailybriefing_time', 'notify_addedasfriend']
        
        outputStringUserSettingForms = ItemForm().as_p()

        template_values = {
                'PrefixCSSdir': "/",
                
                'UserLoggedIn': 'Logged In',

                'EditedUserNickName': EditedUser.dispname, 
                'UserNickName': CurrentUser.dispname, #used for base template. Actully right here, shoudl be the same.
                
                'UserID': CurrentUser.key().id(), #This one used for base.html to identified setting URL.
                'EditedUserID': EditedUser.key().id(),

                'UserJoinInDate': datetime.datetime.date(EditedUser.datejoinin),

                'UserSettingForms': outputStringUserSettingForms,
        }
    
        path = os.path.join(os.path.dirname(__file__), 'pages/usersettingpage.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):  
        
        url_mime = 'image/'

        avatar = self.request.get('avatar') 
        mail = self.request.get('mail')
        dispname = self.request.get('dispname')
        website = self.request.get('website')
        
        if avatar:
           pass     
            
        elif self.request.get('apikey_gene') == 'apikey':
                #Regenerate the APIKEY.
                if self.chk_login():
                    CurrentUser = self.get_user_db()
                CurrentUser.generate_apikey()   
                self.redirect("/user/" + str(CurrentUser.key().id()) + "/setting")

        else:
                if self.chk_login():
                    CurrentUser = self.get_user_db()
                
                CurrentUser.mail = mail
                CurrentUser.dispname = dispname
                CurrentUser.user.nickname = dispname
                try:
                    CurrentUser.website = website
                except:
                    CurrentUser.website = "http://" + website
                CurrentUser.put()

                self.redirect("/user/" + str(CurrentUser.key().id()) + "/setting")

def main():
    application = webapp.WSGIApplication([
                                       ('/user/.+/setting', UserSettingPage),
                                       ],
                                       debug=True)

    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
