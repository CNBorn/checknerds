# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename Nevada
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
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db

import time
import datetime
import string
from google.appengine.ext.webapp import template
from google.appengine.api import images

import memcache
import tarsusaCore
import patcher


import PyRSS2Gen

from modules import *
from base import *
import logging

#Removed a depricated class since r110.
#class DoneLogPage(tarsusaRequestHandler):
                    
class UserToDoPage(tarsusaRequestHandler):
    def get(self):
        # Permission check is very important.
        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login():
            CurrentUser = self.get_user_db()

            CountTotalItems = 0

            ## SPEED KILLER!
            ## MULTIPLE DB QUERIES!
            ## CAUTION! MODIFY THESE LATER!
            tarsusaItemCollection_UserToDoItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and routine = 'none' and done = False ORDER BY date DESC LIMIT 50", CurrentUser.user)

            CountTotalItems = tarsusaItemCollection_UserToDoItems.count()
            strTodoStatus = "共有" + str(CountTotalItems) + "个未完成项目"

            template_values = {
                'PrefixCSSdir': "/",
                'UserLoggedIn': 'Logged In',
                'UserNickName': cgi.escape(CurrentUser.dispname),
                'UserID': CurrentUser.key().id(),
                'htmltag_today': datetime.datetime.date(datetime.datetime.now()), 
                'TodoStatus': strTodoStatus,
                'tarsusaItemCollection_UserToDoItems': tarsusaItemCollection_UserToDoItems,
            }

            #Manupilating Templates 
            path = os.path.join(os.path.dirname(__file__), 'pages/usertodopage.html')
            self.response.out.write(template.render(path, template_values))
        else:
            self.redirect('/')

class UserDonePage(tarsusaRequestHandler):
    def get(self):
        # Permission check is very important.
        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login():
            CurrentUser = self.get_user_db()

            template_values = {
                'PrefixCSSdir': "/",
                'UserLoggedIn': 'Logged In',
                'UserNickName': cgi.escape(CurrentUser.dispname),
                'UserID': CurrentUser.key().id(),
            }

            #Manupilating Templates 
            path = os.path.join(os.path.dirname(__file__), 'pages/userdonepage.html')
            self.response.out.write(template.render(path, template_values))
        else:
            self.redirect('/')

class UserDoneLogPage(tarsusaRequestHandler):
    def get(self):
        
        # Permission check is very important.
        # New CheckLogin code built in tarsusaRequestHandler 
        if self.chk_login():
            CurrentUser = self.get_user_db()

            #self.write(tarsusaCore.get_UserDonelog(CurrentUser.key().id()))
            try:
                pageid = self.request.path[len('/donelog/'):]
                if pageid[:2] == 'p/':
                    tag_ViewPreviousPage = True
                    pageid = pageid[2:]
                else:
                    tag_ViewPreviousPage = False
                donelog_withoutpage = False
            except:
                donelog_withoutpage = True
                pass

            if pageid != None and len(self.request.path) > len('/donelog/'):
                this_timestamp = datetime.datetime.fromtimestamp(int(pageid))
                if tag_ViewPreviousPage == True:
                    ##the defination of 'previous' and 'next' here is different as other pages.
                    tarsusaItemCollection = tarsusaCore.get_UserDonelog(CurrentUser.key().id(), this_timestamp, 'next')
                else:
                    tarsusaItemCollection = tarsusaCore.get_UserDonelog(CurrentUser.key().id(), this_timestamp, 'previous')
            else: 
                #If there is no parameter in the url, displays the default items.
                tarsusaItemCollection = tarsusaCore.get_UserDonelog(CurrentUser.key().id())
                #returned as dictionary, please refer to tarsusaCore.py
            
            if len(tarsusaItemCollection) == 0:
                #If there is no parameter in the url, displays the default items.
                #If there is no results of certain timestamp, displays the default items.
                tarsusaItemCollection = tarsusaCore.get_UserDonelog(CurrentUser.key().id())
                if len(tarsusaItemCollection) != 0: #just in case for the loop redireting(when user have done nothing).
                    #Or should try redirect.
                    self.redirect("/donelog")

            #Memcached Donelog page for better performance.
            IsCachedDonelogPage = memcache.get_item('userdonelog', CurrentUser.key().id())
            if IsCachedDonelogPage:
                strCachedDonelogPage = IsCachedDonelogPage
            else:
                outputStringRoutineLog = '' #"本页面只显示7天内的完成记录<br />".decode('utf-8')
                Donedate_of_previousRoutineLogItem = None  ## To display the routine item log by Daily.
                DaysInDonelog = 0 #How many days are scaled in all data collection.

                for each_Item in tarsusaItemCollection:
                    
                    DoneDateOfThisItem = datetime.datetime.date(each_Item['donedate'])

                    if DoneDateOfThisItem != Donedate_of_previousRoutineLogItem:
                        DaysInDonelog += 1
                        outputStringRoutineLog += ('<br /><h2 class="posttitle" style="font-weight:normal;">' + str(DoneDateOfThisItem) + '完成</h2><br />').decode('utf-8')
                    
                    if each_Item['routine'] != 'none':
                        #FOR DONE_ROUTINE item.
                        strRoutineLogItemPrompt = ''
                        if each_Item['routine'] == 'daily':
                            strRoutineLogItemPrompt = '每日'
                        elif each_Item['routine'] == 'weekly':
                            strRoutineLogItemPrompt = '每周'
                        elif each_Item['routine'] == 'monthly':
                            strRoutineLogItemPrompt = '每月'
                        elif each_Item['routine'] == 'seasonly':
                            strRoutineLogItemPrompt = '每季'
                        elif each_Item['routine'] == 'yearly':
                            strRoutineLogItemPrompt = '每年'

                        outputStringRoutineLog += ('&nbsp;&nbsp;<img src="/img/accept16.png">')
                        outputStringRoutineLog += '<a href=/item/' + str(each_Item['id']) + '>' + each_Item['name'] + "</a> - <strong>" + (strRoutineLogItemPrompt + '任务</strong>').decode('utf-8') + "<br/>"
                        
                    else:
                        #FOR ORDINARY DONE ITEM
                        outputStringRoutineLog += ('&nbsp;&nbsp;<img src="/img/accept16.png">').decode('utf-8')         
                        outputStringRoutineLog += '<a href=/item/' + str(each_Item['id']) + '>' + each_Item['name'] + "</a><br/>"
                        
                    Donedate_of_previousRoutineLogItem = DoneDateOfThisItem 

            

                
                template_values = {
                        'PrefixCSSdir': "/",
                        
                        'UserLoggedIn': 'Logged In',
                        'UserID': CurrentUser.key().id(),
                        'UserNickName': cgi.escape(CurrentUser.dispname),
                        'UserLoginNickName': cgi.escape(CurrentUser.dispname),
                        'singlePageTitle': "",
                        
                        'StringRoutineLog': outputStringRoutineLog,
                }
                
                #Determine next page
                #if there is an error here, there would be not found any records.
                try:
                    previous_timestamp = int(time.mktime(tarsusaItemCollection[0]['donedate'].timetuple()))
                    next_timestamp = int(time.mktime(tarsusaItemCollection[len(tarsusaItemCollection) - 1]['donedate'].timetuple()))
                    if previous_timestamp != 0 and previous_timestamp != '' and pageid != None and donelog_withoutpage != True:
                        template_values['previouspagestamp'] = previous_timestamp       
                        #THIS ALWAYS APPEARS! CHECK!
                        #TODO!
                    if next_timestamp != 0:
                        template_values['nextpagestamp'] = next_timestamp           
                    if next_timestamp == 0 and previous_timestamp == 0 and pageid != None and donelog_withoutpage != True:
                        #Easy to cause 302!
                        #TODO!
                        #self.redirect("/donelog/")         
                        pass
                    #to be improved, if all these records are created in the same day
                    if DaysInDonelog == 1 and tag_ViewPreviousPage == True and pageid != None and donelog_withoutpage != True:
                        #Easy to cause 302!
                        #TODO!
                        #self.redirect("/donelog/")
                        pass
                except:
                    if pageid != None and donelog_withoutpage != True:
                        #Easy to cause 302!
                        #TODO!
                        #self.redirect('/donelog/')
                        pass
                    else:
                        pass
        
                path = os.path.join(os.path.dirname(__file__), 'pages/donelog.html')
                strCachedDonelogPage = template.render(path, template_values)
                #memcache.set_item("userdonelog", strCachedDonelogPage, CurrentUser.key().id())
            self.response.out.write(strCachedDonelogPage)
        else:
            self.redirect('/')

class UserSettingPage(tarsusaRequestHandler):
    def get(self):
        userid = urllib.unquote(cgi.escape(self.request.path[6:-8])) ## Get the username in the middle of /user/1234/setting

        EditedUser = tarsusaUser.get_by_id(int(userid))
        CurrentUser = self.get_user_db()

        #Since r136+
        #UserModel update for notification.
        patcher.patch_notification_daily_and_friends(userid)

        if EditedUser is not None and CurrentUser is not None:          
            
            if CurrentUser.key().id() == EditedUser.key().id():

                from google.appengine.ext.db import djangoforms
                from django import newforms as forms 
                
                class ItemForm(djangoforms.ModelForm):
                    
                    ## Custom djangoforms.ModelForm,
                    ## http://groups.google.com/group/google-appengine/browse_thread/thread/d3673d0ec7ead0e2
                    
                    mail =  forms.CharField(label='您的邮箱(不会公开，无法更改)',widget=forms.TextInput(attrs={'readonly':'','size':'30','maxlength':'30','value':EditedUser.user.email()})) 
                    #urlname =forms.CharField(label='URL显示地址',widget=forms.TextInput(attrs={'size':'30','maxlength':'30','value':CurrentUser.urlname}))
                    dispname = forms.CharField(label='显示名称',widget=forms.TextInput(attrs={'size':'30','maxlength':'30','value':EditedUser.dispname,'class':'sl'}))
                    website = forms.CharField(label='您的网址(请加http://)',widget=forms.TextInput(attrs={'size':'36','maxlength':'36','value':EditedUser.website,'class':'sl'}))   
                    ##Please reference more from the URL

                    #notify_dailybriefing = forms.BooleanField(label='每日邮件提醒',widget=forms.CheckboxInput(attrs={'checked':EditedUser.notify_dailybriefing}))
                    #notify_dailybriefing_time = forms.CharField(label='每日邮件提醒时间', widget=forms.TextInput(attrs={'value':EditedUser.notify_dailybriefing_time,'class':'sl'}))
                    #notify_addedasfriend = forms.BooleanField(label='用户添加好友邮件提醒',widget=forms.CheckboxInput(attrs={'checked':EditedUser.notify_addedasfriend}))

                    apikey = forms.CharField(label="ApiKey(请勿泄露)", widget=forms.TextInput(attrs={'readonly':'', 'class':'sl', 'value':EditedUser.apikey}))

                    class Meta:
                        model = tarsusaUser
                        #exclude =['user','userid','usedtags','urlname','friends','datejoinin']
                        exclude =['user','userid','usedtags','urlname','friends','datejoinin', 'notify_dailybriefing', 'notify_dailybriefing_time', 'notify_addedasfriend']
                
                outputStringUserSettingForms = ItemForm().as_p() #also got as_table(), as_ul()

                ## The Avatar part is inspired by 
                ## http://blog.liangent.cn/2008/07/google-app-engine_28.html

                outputStringUserAvatarSetting = ""
                
                if EditedUser.avatar:
                    outputStringUserAvatarImage = "<img src=/image?avatar=" + str(EditedUser.key().id()) + " width=64 height=64><br />" + cgi.escape(EditedUser.dispname) + '&nbsp;<br />'
                else:
                    outputStringUserAvatarImage = "<img src=/img/default_avatar.jpg width=64 height=64><br />" + cgi.escape(EditedUser.dispname) + '&nbsp;<br />'

                
                outputStringUserAvatarSetting += '''
                             <form method="post" enctype="multipart/form-data"> 
                             选择图像文件(<1M): <input type="file" name="avatar"/ size=15>
                             <input type="submit" value="更新头像"/></form> '''.decode('utf-8')



                template_values = {
                        'PrefixCSSdir': "/",
                        
                        'UserLoggedIn': 'Logged In',

                        'EditedUserNickName': EditedUser.dispname, 
                        'UserNickName': CurrentUser.dispname, #used for base template. Actully right here, shoudl be the same.
                        
                        'UserID': CurrentUser.key().id(), #This one used for base.html to identified setting URL.
                        'EditedUserID': EditedUser.key().id(),

                        'UserJoinInDate': datetime.datetime.date(EditedUser.datejoinin),

                        'UserSettingForms': outputStringUserSettingForms,
                        'UserAvatarImage': outputStringUserAvatarImage,
                        'UserAvatarSetting': outputStringUserAvatarSetting,
                }
            
                path = os.path.join(os.path.dirname(__file__), 'pages/usersettingpage.html')
                self.response.out.write(template.render(path, template_values))

            else:
                # the editedUser is not CurrentUser.
                self.redirect("/")

        else:
            ## can not find this user.
            self.redirect("/")


    def post(self):  
        
        #checkauth(self)  
        
        url_mime = 'image/'

        avatar = self.request.get('avatar') 
        mail = self.request.get('mail')
        dispname = self.request.get('dispname')
        website = self.request.get('website')
        
        if avatar:
                
                # New CheckLogin code built in tarsusaRequestHandler 
                if self.chk_login():
                    CurrentUser = self.get_user_db()

                #Create the Avatar Image Thumbnails.
                avatar_image = images.Image(avatar)
                avatar_image.resize(width=64,height=64)
                avatar_image.im_feeling_lucky()
                avatar_image_thumbnail = avatar_image.execute_transforms(output_encoding=images.JPEG)

                CurrentUser.avatar=db.Blob(avatar_image_thumbnail)
                CurrentUser.put()  
                
                if not memcache.set('img_useravatar' + str(CurrentUser.key().id()), db.Blob(avatar_image_thumbnail), 7200):
                    logging.error("Memcache set failed: When uploading avatar_image")

                self.redirect("/user/" + str(CurrentUser.key().id()) + "/setting")


        elif self.request.get('apikey_gene') == 'apikey':

                #Regenerate the APIKEY.
                if self.chk_login():
                    CurrentUser = self.get_user_db()

                    #From Plog.
                    #Generate a random string for using as api password, api user is user's full email
                    
                    from random import sample
                    import hashlib
                    s = 'abcdefghijklmnopqrstuvwxyz1234567890'
                    fusion_p = ''.join(sample(s, 8))
                    
                    fusion_uky = str(CurrentUser.key().id())
                    fusion_uma = str(CurrentUser.mail)
                    fusion_cn = "CheckNerds Approching to version California"
                    
                    fusion_uni = fusion_p + fusion_uky + fusion_uma + fusion_cn                 
                    
                    CurrentUser.apikey = hashlib.sha1(fusion_uni).hexdigest()[:8]
                    CurrentUser.put()
    
                self.redirect("/user/" + str(CurrentUser.key().id()) + "/setting")


        else:
                
                # New CheckLogin code built in tarsusaRequestHandler 
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




                if self.request.get('fetch') == 'yes':  
                    try:
                        fc = urlfetch.fetch(url_mime)  
                        if fc.status_code == 200:  
                            avatar = fc.content  
                            if 'Content-Type' in fc.headers:  
                                url_mime = fc.headers['Content-Type']  
                            
                                # New CheckLogin code built in tarsusaRequestHandler 
                                if self.chk_login():
                                    CurrentUser = self.get_user_db()
                    
                                
                                self.write('noneok')
                            else:
                                #sendmsg(self, 'no content-type sent from remote server')
                                self.write('ac')
                        else:  
                            #sendmsg(self, 'cannot fetch avatar: http status ' + str(fc.status_code))  
                            self.write('avcx')
                    except:  
                        #sendmsg(self, 'cannot fetch avatar')  
                        self.write('avcx')

                else:  
                    try:
                        avatar = Avatar(url_mime=url_mime)  
                        avatar.put() 
                        if not memcache.set('img_useravatar' + str(CurrentUser.key().id()), db.Blob(avatar_image), 7200):
                            logging.error("Memcache set failed: When uploading(2) avatar_image")

                    except:
                        pass
                        self.redirect("/user/" + str(CurrentUser.key().id()) + "/setting")
                    #sendmsg(self, 'added')  

class UserMainPage(tarsusaRequestHandler):
    def get(self):

        username = urllib.unquote(cgi.escape(self.request.path[6:]))  ## Get the username in the URL string such as /user/1234
        ViewUser = None
        
        try:
            ## After URL style changed, Now won't allow username in URL, only accept id in URL.
            
            ## Get this user.
            q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE userid = :1 LIMIT 1", int(username))
            ViewUser = q.get()

            if ViewUser == None:
                q = tarsusaUser.get_by_id(int(username))
                ViewUser = q
        except:
            self.redirect('/')

        UserNickName = '访客'
        outputStringUserAvatar = ''

        UserNonPrivateItemsList = ''
        UserFriends = []

        if ViewUser != None:
        
            ## Preparation
            ## Will be useed
            if ViewUser.avatar:
                outputStringUserAvatar = "<img src='/image?avatar=" + str(ViewUser.key().id()) + "' width=64 height=64>"
            else:
                outputStringUserAvatar = "<img src='/img/default_avatar.jpg' width=64 height=64>"
                
            outputStringUserMainPageTitle = ViewUser.dispname + "公开的项目".decode("utf-8")

            #-------------------------------------
            if not self.chk_login():
            
                #Not a login user, show only the public items.
                UserNickName = "访客"
                logictag_OneoftheFriendsViewThisPage = False
                CurrentUserIsOneofViewUsersFriends = False
                statusUserFriends = 'NotLogin'
                #Above tag will be recognized by template
                ViewedUserIsOneofCurrentUsersFriends = False

                #Check Whether there is usermainPage_publicitems_anony
                cachedUserMainPagePublicItemsAnony = memcache.get_item("mainpage_publicitems_anony", ViewUser.key().id())
                if cachedUserMainPagePublicItemsAnony is not None:
                    UserNonPrivateItemsList = cachedUserMainPagePublicItemsAnony
                else:
                    UserNonPrivateItemsList = tarsusaCore.get_UserNonPrivateItems(ViewUser.key().id(), 'public')
                

                template_values = {
                    'PrefixCSSdir': "../",
                    
                    'ViewedUserNickName': ViewUser.dispname,

                    'UserAvatarImage': outputStringUserAvatar,
                    
                    'statusViewedUserFriends': statusUserFriends,   
                    'UserJoinInDate': datetime.datetime.date(ViewUser.datejoinin),
                    'UserWebsite': ViewUser.website,
                    'UserMainPageUserTitle': outputStringUserMainPageTitle,
                    'UserNonPrivateItemsList': UserNonPrivateItemsList,
                    
                    'outputFeed': True,
                    'outputFeedTitle': ViewUser.dispname,
                    'outputFeedURL': "/user/" + str(ViewUser.key().id()) + "/feed",
                }

            
            else:               
                #User Login.
                
                #Check Whether CurrerentUser is one of ViewUser's friends
                UserNickName = ViewUser.dispname
                CurrentUser = self.get_user_db()

                CurrentUserIsOneofViewUsersFriends = False

                for each_Friend_key in ViewUser.friends:
                    if each_Friend_key == CurrentUser.key():
                        CurrentUserIsOneofViewUsersFriends = True
                        logictag_OneoftheFriendsViewThisPage = True

                ## Check whether the ViewedUser is a friend of CurrentUser.
                ## For AddUserAsFriend button.
                ViewedUserIsOneofCurrentUsersFriends = False

                for each_Friend_key in CurrentUser.friends:
                    if each_Friend_key == ViewUser.key():
                        ViewedUserIsOneofCurrentUsersFriends = True
            
                # Get user friend list
                cachedUserMainPageFriends = memcache.get_item("mainpage_friends", ViewUser.key().id())
                if cachedUserMainPageFriends is not None:
                    UserFriends = cachedUserMainPageFriends
                else:
                    # This is shown to all logged in users.
                    #Check This Users Friends.
                    
                    UserFriends = tarsusaCore.get_UserFriends(ViewUser.key().id())
                    
                    #set cache item
                    memcache.set_item("mainpage_friends", UserFriends, ViewUser.key().id())
                    
                #----------------------------------------               
                if ViewedUserIsOneofCurrentUsersFriends == True:
                    #Check Whether there is usermainpage_publicitems
                    cachedUserMainPagePublicItems = memcache.get_item("mainpage_publicitems", ViewUser.key().id())
                    if cachedUserMainPagePublicItems is not None:
                        UserNonPrivateItemsList = cachedUserMainPagePublicItems
                    else:
                        UserNonPrivateItemsList = tarsusaCore.get_UserNonPrivateItems(ViewUser.key().id(), 'publicOnlyforFriends')
                        #about the property, it pass this one but actually it's going to digg publicwithPublicforFriends.
                        
                        #set cache item
                        memcache.set_item("mainpage_publicitems", UserNonPrivateItemsList, ViewUser.key().id())

                else:
                    #CurrentUser is not one of ViewUser's friends.

                    #Check Whether there is usermainPage_publicitems_anony
                    cachedUserMainPagePublicItemsAnony = memcache.get_item("mainpage_publicitems_anony", ViewUser.key().id())
                    if cachedUserMainPagePublicItemsAnony is not None:
                        UserNonPrivateItemsList = cachedUserMainPagePublicItemsAnony
                    else:
                        UserNonPrivateItemsList = tarsusaCore.get_UserNonPrivateItems(ViewUser.key().id(), 'public')

                        #set cache item
                        memcache.set_item("mainpage_publicitems_anony", UserNonPrivateItemsList, ViewUser.key().id())

                template_values = {
                    'PrefixCSSdir': "../",
                    
                    'UserLoggedIn': 'Logged In',

                    'UserID': CurrentUser.key().id(), #This indicates the UserSettingPage Link on the topright of the Page, so it should be CurrentUser

                    'ViewedUserNickName': UserNickName,
                    'UserNickName': CurrentUser.dispname,
                    'ViewedUser': ViewUser,

                    'ViewedUserFriends': UserFriends,   

                    'UserAvatarImage': outputStringUserAvatar,
                    
                    'UserJoinInDate': datetime.datetime.date(ViewUser.datejoinin),
                    'UserWebsite': ViewUser.website,
                    'UserMainPageUserTitle': outputStringUserMainPageTitle,
                
                    'ViewedUserIsOneofCurrentUsersFriends': ViewedUserIsOneofCurrentUsersFriends,
                    'UserNonPrivateItemsList': UserNonPrivateItemsList,

                    'outputFeed': True,
                    'outputFeedTitle': ViewUser.dispname,
                    'outputFeedURL': "/user/" + str(ViewUser.key().id()) + "/feed",
                }
            

            path = os.path.join(os.path.dirname(__file__), 'pages/usermainpage.html')
            
            self.response.out.write(template.render(path, template_values))

        else:
            #self.write('not found this user and any items')
            
            # Prompt 'Can not found this user, URL style have been changed since Dec.X 2008, Some of the old external links are invalid now.
            # But We offer you another options, You may check whether these Users, may be one of them is whom you are looking for.
            # Better UE idea!

            outputStringUserMainPageTitle = 'not found this user and any items'
            outputStringRoutineLog = 'None'
            self.error(404)
            self.redirect('/')  

class UserFeedPage(tarsusaRequestHandler):
    def get(self):
        
        #RSS Feed Code, leart from Plog, using PyRSS2Gen Module.

        userid = urllib.unquote(cgi.escape(self.request.path[6:-5]))  ## Get the username in the URL string such as /user/1234/feed
        
        ## Get this user.
        ViewUser = tarsusaUser.get_by_id(int(userid))
            

        UserNickName = '访客'
        outputStringUserAvatar = ''

        if ViewUser != None:
            
            IsCachedUserFeed = memcache.get_item('UserPublicFeed', ViewUser.key().id())
                
            if IsCachedUserFeed:
                userfeed_publicitems = IsCachedUserFeed
            else:
    
                userfeed_publicitems = []
                
                #should look at the routinelog at first.
                #new feed output supports public daily routine.
                tarsusaItemCollection_RecentDoneDailyRoutines = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem ORDER by donedate DESC LIMIT 10")
                for each_DailyRoutineLogItem in tarsusaItemCollection_RecentDoneDailyRoutines:              
                    RoutineItem = tarsusaItem.get_by_id(each_DailyRoutineLogItem.routineid)
                    if RoutineItem.user == ViewUser.user and RoutineItem.public == 'public':
                        str_title = ViewUser.dispname + " 今天完成了 ".decode('utf-8') + tarsusaItem.get_by_id(each_DailyRoutineLogItem.routineid).name
                        item_url = '%s/item/%d' % (self.request.host_url, RoutineItem.key().id())
                        
                        str_title = ViewUser.dispname + " 今天完成了 ".decode('utf-8') + RoutineItem.name
                        try:
                            # some very old items may not have usermodel property 
                            str_author = RoutineItem.usermodel.dispname
                        except:
                            str_author = RoutineItem.user.nickname()

                        userfeed_publicitems.append({
                                        'title': str_title,
                                        'author': str_author,
                                        'link': item_url,
                                        'description': '每日任务'.decode('utf-8'), #Later will be comment for each dailydone. 
                                        'pubDate': each_DailyRoutineLogItem.donedate,
                                        'guid': PyRSS2Gen.Guid(str_title + str(each_DailyRoutineLogItem.donedate))
                                        #categories
                                        })      

                
                #There is a force 15 limits for RSS feed.
                #Plog is setting this as an option in setting.
                tarsusaItemCollection_UserRecentPublicItems = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 and public = 'public' ORDER BY date DESC LIMIT 15", ViewUser.user)
                #the code block below is a little bit duplicated, will find a way to make it simple in future. TODO
                for each_Item in tarsusaItemCollection_UserRecentPublicItems:
                    
                    try:
                        # some very old items may not have usermodel property 
                        str_author = each_Item.usermodel.dispname
                    except:
                        str_author = each_Item.user.nickname()
                    
                    item_url = '%s/item/%d' % (self.request.host_url, each_Item.key().id())

                    if each_Item.done == True:
                        str_title = ViewUser.dispname + " 完成了 ".decode('utf-8') + each_Item.name
                    else:
                        str_title = ViewUser.dispname + " 要做 ".decode('utf-8') + each_Item.name
                    
                    userfeed_publicitems.append({
                                        'title': str_title,
                                        'author': str_author,
                                        'link': item_url,
                                        'description':each_Item.comment,
                                        'pubDate': each_Item.date,
                                        'guid': PyRSS2Gen.Guid(item_url)
                                        #categories
                                        })                  

                #sort the results:
                #Sort Algorithms from
                #http://www.lixiaodou.cn/?p=12
                length = len(userfeed_publicitems)
                for i in range(0,length):
                    for j in range(length-1,i,-1):
                        #Convert string to datetime.date
                        #http://mail.python.org/pipermail/tutor/2006-March/045729.html  
                        time_format = "%Y-%m-%d %H:%M:%S"
                        #if datetime.datetime.fromtimestamp(time.mktime(time.strptime(userfeed_publicitems[j]['pubDate'][:-7], time_format))) > datetime.datetime.fromtimestamp(time.mktime(time.strptime(userfeed_publicitems[j-1]['pubDate'][:-7], time_format))):
                        if userfeed_publicitems[j]['pubDate'] > userfeed_publicitems[j-1]['pubDate']:
                            temp = userfeed_publicitems[j]
                            userfeed_publicitems[j]=userfeed_publicitems[j-1]
                            userfeed_publicitems[j-1]=temp
                
                
                memcache.set_item("UserPublicFeed", userfeed_publicitems, ViewUser.key().id(), 1800)
                #cache it for at least half an hour.


            publicItems = []
            for each in userfeed_publicitems:
                publicItems.append(PyRSS2Gen.RSSItem(
                                title = each['title'],
                                author = each['author'],
                                link = each['link'],
                                description = each['description'],
                                pubDate = each['pubDate'],
                                guid = each['guid']
                                ))

            
            rss = PyRSS2Gen.RSS2(
                title = "CheckNerds - " + ViewUser.dispname,
                link = self.request.host_url + '/user/' + str(ViewUser.key().id()),
                description = ViewUser.dispname + '最新的公开事项，在线个人事项管理——欢迎访问http://www.checknerds.com'.decode('utf-8'),
                lastBuildDate = datetime.datetime.utcnow(),
                items = publicItems
                )

            self.response.headers['Content-Type'] = 'application/rss+xml; charset=utf-8'
            rss_xml = rss.to_xml(encoding='utf-8')
            self.write(rss_xml)




def main():
    application = webapp.WSGIApplication([('/donelog.*', UserDoneLogPage),
                                       #Once I have both Donelog functions in this file.
                                       #Disabled one of them. since r110.
                                       #('/user/.+/donelog',DoneLogPage),
                                       
                                       ('/user/.+/feed', UserFeedPage),
                                       ('/user/.+/setting', UserSettingPage),
                                       ('/user/.+/todo', UserToDoPage),
                                       ('/user/.+/done', UserDonePage),
                                       ('/user/.+', UserMainPage),
                                       ],
                                       debug=True)

    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
