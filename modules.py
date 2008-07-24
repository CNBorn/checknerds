from google.appengine.ext import db

class tarsusaItem(db.Model):
    user = db.UserProperty()
    name = db.StringProperty()
    comment = db.StringProperty(multiline=True)
    tags = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    expectdate = db.DateTimeProperty()
    donedate = db.DateTimeProperty()
    done = db.BooleanProperty()
    routine = db.StringProperty(required=True, choices=set(["none", "daily", "weekly", "monthly", "seasonly", "yearly"]))
    public = db.BooleanProperty()




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
	count = db.IntegerProperty(required=True)





