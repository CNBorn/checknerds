from google.appengine.ext import db



class tarsusaRoutineLogItem(db.Model):
    
    user = db.UserProperty()
    routineid = db.IntegerProperty()
    routine = db.StringProperty(required=True, choices=set(["none", "daily", "weekly", "monthly", "seasonly", "yearly"]))
    donedate = db.DateTimeProperty(auto_now_add=True)

class tarsusaUser(db.Model):
    user = db.UserProperty()
    userid = db.IntegerProperty()
    mail = db.EmailProperty()
    avatar = db.BlobProperty()
    urlname = db.StringProperty()
    dispname = db.StringProperty()
    website = db.LinkProperty()
    usedtags = db.ListProperty(db.Key)
    friends = db.ListProperty(db.Key)
    
    datejoinin = db.DateTimeProperty(auto_now_add=True)

    apikey = db.StringProperty()
    
    #notification = db.StringProperty()
    notify_dailybriefing = db.BooleanProperty()
    notify_dailybriefing_time = db.TimeProperty()
    notify_addedasfriend = db.BooleanProperty()

    # fields to be appended:
    #   Twitter,    
    
    def __unicode__(self):
        if self.dispname:
            return self.dispname
        else:
            return self.user.nickname()

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class tarsusaItem(db.Expando):
    # if user is a referenceProperty of tarsusaUser, that would be make more sense.
    # therefore a lot of the functions can be implemented.
    usermodel = db.ReferenceProperty(tarsusaUser) # Added since Rev.75
    user = db.UserProperty()
    name = db.StringProperty()
    comment = db.StringProperty(multiline=True)
    tags = db.ListProperty(db.Key)
    date = db.DateTimeProperty(auto_now_add=True)
    expectdate = db.DateTimeProperty()
    donedate = db.DateTimeProperty()
    done = db.BooleanProperty()
    routine = db.StringProperty(required=True, choices=set(["none", "daily", "weekly", "monthly", "seasonly", "yearly"]))
    public = db.StringProperty(choices=set(["private", "public", "publicOnlyforFriends"]))
    

class Tag(db.Model):
    name = db.StringProperty()
    count = db.IntegerProperty()

    #design inspried by ericsk

    #@property
    #def posts(self):
    #   self.count += 1
        #return tarsusaItem.gql('WHERE tags = :1', self.key())
    #   return User.gql('WHERE usedtags = :1', self.key())




## Many to Many model design styles.
## http://blog.ericsk.org/archives/1009


#class Post(db.Model):
#    title = db.StringProperty(required=True)
#    body = db.TextProperty(required=True)
#    post_at = db.DateTimeProperty(auto_now_add=True)
#    categories = db.ListProperty(db.Key)

#class Category(db.Model):
#    name = db.StringProperty(required=True)
#    description = db.TextProperty()
   
#    @property
#    def posts(self):
#        return Post.gql('WHERE categories = :1', self.key())


class AppModel(db.Model):
    """Applications that uses CheckNerds API"""
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    usermodel = db.ReferenceProperty(tarsusaUser)
    servicekey = db.StringProperty(multiline=False)
    api_limit = db.IntegerProperty(required=True, default=400)
    enable = db.BooleanProperty(default=False)
    indate = db.DateProperty(auto_now_add=True)
    
