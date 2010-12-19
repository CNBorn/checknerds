import sys
sys.path.append("../")

from google.appengine.ext import db
from models.user import tarsusaUser
from models.item import tarsusaItem, tarsusaRoutineLogItem

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
    
