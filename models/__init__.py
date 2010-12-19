import sys
sys.path.append("../")

from google.appengine.ext import db
from models.user import tarsusaUser
from models.item import tarsusaItem, tarsusaRoutineLogItem
from models.tag import Tag

class AppModel(db.Model):
    """Applications that uses CheckNerds API"""
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    usermodel = db.ReferenceProperty(tarsusaUser)
    servicekey = db.StringProperty(multiline=False)
    api_limit = db.IntegerProperty(required=True, default=400)
    enable = db.BooleanProperty(default=False)
    indate = db.DateProperty(auto_now_add=True)
    
