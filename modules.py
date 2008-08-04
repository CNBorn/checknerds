from google.appengine.ext import db

class tarsusaItem(db.Expando):
    user = db.UserProperty()
    name = db.StringProperty()
    comment = db.StringProperty(multiline=True)
    tags = db.ListProperty(db.Key)
    #tags = db.StringListProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    expectdate = db.DateTimeProperty()
    donedate = db.DateTimeProperty()
    done = db.BooleanProperty()
    routine = db.StringProperty(required=True, choices=set(["none", "daily", "weekly", "monthly", "seasonly", "yearly"]))
    public = db.BooleanProperty()

class tarsusaRoutineLogItem(db.Model):
	
	user = db.UserProperty()
	routineid = db.IntegerProperty()
	routine = db.StringProperty(required=True, choices=set(["none", "daily", "weekly", "monthly", "seasonly", "yearly"]))
	donedate = db.DateTimeProperty(auto_now_add=True)


class User(db.Model):
	user = db.UserProperty(required = True)
	#mail
	dispname = db.StringProperty()
	website = db.LinkProperty()
	usedtags = db.StringProperty()


	def __unicode__(self):
		if self.dispname:
			return self.dispname
		else:
			return self.user.nickname()

	def __str__(self):
		return self.__unicode__().encode('utf-8')



class Tag(db.Model):
	name = db.StringProperty()
	#count = db.IntegerProperty(required=True)

	#design inspried by ericsk

	@property
	def posts(self):
		return Post.gql('WHERE tags = :1', self.key())



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


