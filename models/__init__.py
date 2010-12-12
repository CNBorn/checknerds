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
    
    notify_dailybriefing_time = db.TimeProperty()
    notify_addedasfriend = db.BooleanProperty()
    
    def __unicode__(self):
        if self.dispname:
            return self.dispname
        else:
            return self.user.nickname()

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    @classmethod
    def get_latestusers(count=8):
        result = db.GqlQuery("SELECT * FROM tarsusaUser ORDER by datejoinin DESC LIMIT 8")
        return result

class tarsusaItem(db.Expando):
    usermodel = db.ReferenceProperty(tarsusaUser)
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

class AppModel(db.Model):
    """Applications that uses CheckNerds API"""
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    usermodel = db.ReferenceProperty(tarsusaUser)
    servicekey = db.StringProperty(multiline=False)
    api_limit = db.IntegerProperty(required=True, default=400)
    enable = db.BooleanProperty(default=False)
    indate = db.DateProperty(auto_now_add=True)
    
