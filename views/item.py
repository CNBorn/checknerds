# -*- coding: utf-8 -*-

import os
import sys
sys.path.append("../")

import cgi
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db


from google.appengine.ext.webapp import template
import tarsusaCore

from models import tarsusaItem, tarsusaUser
from base import tarsusaRequestHandler

import datetime


class ViewItem(tarsusaRequestHandler):
    def get(self):
        postid = self.request.path[6:]
        tItem = tarsusaItem.get_item(int(postid))

        if tItem:

            # code below are comming from GAE example
            q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", tItem.user)
            ItemAuthorUser = q.get()

            #Patch since Rev.76
            try:
                if tItem.usermodel == None:
                    tItem.usermodel = ItemAuthorUser
                    tItem.put()
            except:
                tItem.usermodel = ItemAuthorUser
                tItem.put()
            #-------------------


            ## Unregistered Guest may ViewItem too,
            ## Check Their nickname here.
            if users.get_current_user() == None:
                UserNickName = "访客"
            else:
                UserNickName = users.get_current_user().nickname()


            # Check if this item is expired.
            if tItem.expectdate != None:
                if datetime.datetime.now() > tItem.expectdate:
                    tItem.expired = 1
                    tItem.put()
                else:
                    pass

            elif tItem.expectdate != tItem.expectdate:
                if tItem.expired:
                    del tItem.expired
                    tItem.put()
            else:
                pass

            

            # New CheckLogin code built in tarsusaRequestHandler 
            if self.chk_login():
                CurrentUser = self.get_user_db()
            
            logictag_OtherpeopleViewThisItem = None
            CurrentUserIsOneofAuthorsFriends = False
            
            if tItem.user != users.get_current_user():
            
                ## Check if the viewing user is a friend of the ItemAuthor.
            
                # code below are comming from GAE example
                q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", tItem.user)
                ItemAuthorUser = q.get()

                CurrentUserIsOneofAuthorsFriends = False

                try:
                    ## may get anonymous user here.
                    for each_Friend_key in ItemAuthorUser.friends:
                        if each_Friend_key == CurrentUser.key():
                            CurrentUserIsOneofAuthorsFriends = True
                except:
                    CurrentUserIsOneofAuthorsFriends = False

                #Fixed since r116, Now Anonymuse user can't see PublicToFriends items.
                if tItem.public == 'publicOnlyforFriends' and CurrentUserIsOneofAuthorsFriends == True:
                    logictag_OtherpeopleViewThisItem = True

                elif tItem.public == 'public':
                    logictag_OtherpeopleViewThisItem = True
                    
                else:
                    self.redirect('/')
            else:
                ## Viewing User is the Owner of this Item.
                UserNickName = users.get_current_user().nickname()
                logictag_OtherpeopleViewThisItem = False


            # for modified Tags (db.key)
            ItemTags = ''
            
            try:
                if logictag_OtherpeopleViewThisItem == True:
                    for each_tag in db.get(tItem.tags):
                        ItemTags += cgi.escape(each_tag.name) + '&nbsp;'
                else:
                    for each_tag in db.get(tItem.tags):
                        ItemTags += '<a href=/tag/' + cgi.escape(each_tag.name) +  '>' + cgi.escape(each_tag.name) + '</a>&nbsp;'
            except:
                # There is some chances that ThisItem do not have any tags.
                pass



            # process html_tag_tarsusaRoutineItem
            if tItem.routine != 'none':
                html_tag_tarsusaRoutineItem = 'True'

                ## If this routine Item's public == public or showntoFriends,
                ## All these done routine log will be shown!
                if tItem.public == 'publicOnlyforFriends' and CurrentUserIsOneofAuthorsFriends == True or tItem.public == 'public':
                    tarsusaItemCollection_DoneDailyRoutine = db.GqlQuery("SELECT * FROM tarsusaRoutineLogItem WHERE user = :1 and routineid = :2 ORDER BY donedate DESC LIMIT 10", tItem.user, tItem.key().id())
                else:
                    tarsusaItemCollection_DoneDailyRoutine = None
            else:
                tarsusaItemCollection_DoneDailyRoutine = None
                html_tag_tarsusaRoutineItem = None


            ## Since Rev.7x Since GqlQuery can not filter, this function is disabled.   
            
            #Show Undone items in the same category, just like in tarsusa r6
            #Since Nevada allows mutiple tags, It finds item that with any one tags of this showing items.
            #Deprecated since r116.     

            # -----
            #Show the items that are created in the same day, just like in tarsusa r6.

            TheDay = tItem.date
                
            one_day = datetime.timedelta(days=1)
            yesterday_ofTheDay = TheDay - one_day
            nextday_ofTheDay = TheDay + one_day

            #if the viewedUser is not the currentuser, first have to determine whether he is or is not a friend of currentuser.
            # and then display the sameday items of that user.
            outputStringRoutineLog = ""

            if logictag_OtherpeopleViewThisItem == True and CurrentUserIsOneofAuthorsFriends == True:
                ## Display public items and friendvisible items.
                ## BUG HERE! Because of the stupid GAE != issue, friends can only see friendpublic items. :(
                ## Fixed, 09.05.06
                tarsusaItemCollection_SameDayCreated = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND date > :2 AND date <:3 ORDER and public != 'none' BY date DESC LIMIT 20", tItem.user, yesterday_ofTheDay, nextday_ofTheDay)

                ##TODO I found there is an issue with the permission settings.
                ## When the ItemAuthor added CurrentUser as a friend, CurrentUser still can't see Author's friendpublic items
                ## After the CurrentUser added AUthor as a friend, the FriendPub item appears.
                ## Suspection as a wrong detection of Friends.
                ## But later I found this could be useful. Both users should confirm their relationship before sharing the info.
                ## Just have to figure out which part of code will cause this. :)
                ## 09.05.06
    
                ## Code from UserMainPage class.
                for each_Item in tarsusaItemCollection_SameDayCreated:
                ## Added Item public permission check.
        
                    if each_Item.public == 'publicOnlyforFriends':
                        if each_Item.done == True:
                            outputStringRoutineLog += "<img src='/img/accept16.png'>" 
                        outputStringRoutineLog += '<a href="/item/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
                    elif each_Item.public == 'public':
                        if each_Item.done == True:
                            outputStringRoutineLog += "<img src='/img/accept16.png'>" 
                        outputStringRoutineLog += '<a href="/item/' + str(each_Item.key().id()) + '"> ' + each_Item.name + "</a><br />"
                    else:
                        pass


            elif logictag_OtherpeopleViewThisItem == True and CurrentUserIsOneofAuthorsFriends == False:
                ## Display only public items.
                tarsusaItemCollection_SameDayCreated = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND date > :2 AND date <:3 AND public = 'public' ORDER BY date DESC LIMIT 10", tItem.user, yesterday_ofTheDay, nextday_ofTheDay)

            elif logictag_OtherpeopleViewThisItem == False:
                ## if the viewedUser is the currentuser, just display the sameday items of currentuser.
                            
                # SOME how bug is here, there is no way to determine the same date within the gql query.
                tarsusaItemCollection_SameDayCreated = db.GqlQuery("SELECT * FROM tarsusaItem WHERE user = :1 AND date > :2 AND date <:3 ORDER BY date DESC LIMIT 10", users.get_current_user(), yesterday_ofTheDay, nextday_ofTheDay)
                # filter current viewing Item from the related items!           


            if UserNickName != "访客":
                UserNickName = users.get_current_user().nickname()
                ## or dispname?

                template_values = {
                        'PrefixCSSdir': "../",
                        'UserLoggedIn': 'Logged In',

                        'UserID': CurrentUser.key().id(),
                        'UserNickName': UserNickName, 
                        'ItemBelongsToUser': tItem.user,
                        'singlePageTitle': "项目详细信息",
                        'singlePageContent': "",

                        'logictag_OtherpeopleViewThisItem': logictag_OtherpeopleViewThisItem,
                        'logictag_CurrentUserIsOneofAuthorsFriends': CurrentUserIsOneofAuthorsFriends,

                        'tarsusaItem': tItem,
                        'tarsusaItemDone': tItem.done,
                        'tarsusaItemTags': ItemTags,
                        'tarsusaRoutineItem': html_tag_tarsusaRoutineItem,
                        'tarsusaRoutineLogItem': tarsusaItemCollection_DoneDailyRoutine,

                        #'tarsusaItemCollection_SameCategoryUndone': tarsusaItemCollection_SameCategoryUndone,

                        'TheDayCreated': TheDay,
                        'tarsusaItemCollection_SameDayCreated': tarsusaItemCollection_SameDayCreated,
                        'htmlstring_outputStringRoutineLog': outputStringRoutineLog,
                }

            else:
                        template_values = {
                        'PrefixCSSdir': "../",
                        'singlePageTitle': "项目详细信息",
                        'singlePageContent': "",

                        'logictag_OtherpeopleViewThisItem': logictag_OtherpeopleViewThisItem,

                        'tarsusaItem': tItem,
                        'tarsusaItemDone': tItem.done,
                        'tarsusaItemTags': ItemTags,
                        'tarsusaRoutineItem': html_tag_tarsusaRoutineItem,
                        'tarsusaRoutineLogItem': tarsusaItemCollection_DoneDailyRoutine,
                }


        
            path = os.path.join(os.path.dirname(__file__), '../pages/viewitem.html')
            self.response.out.write(template.render(path, template_values))


        else:
            ## Can't find this Item by this id.
            self.redirect('/')

def main():
    application = webapp.WSGIApplication([
                                       ('/item/\\d+',ViewItem),
                                       ],
                                       debug=True)

    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
