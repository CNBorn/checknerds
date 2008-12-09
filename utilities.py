from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from modules import *
from base import *

def chk_dbmodel_update(ThisUser):
	
	# Patch No.1 
	#      Added usermodel property in tarsusaItem since Rev.75
	#	
	# This update needs to browse all the tarsusaItem and add this field to them.
	# Besure that the total item is under 1000.
	tarsusaItemCollection = db.GqlQuery("SELECT * FROM tarsusaItem")	
	for each_tarsusaItem in tarsusaItemCollection:
		if each_tarsusaItem.usermodel == None:
			q = db.GqlQuery("SELECT * FROM tarsusaUser WHERE user = :1", each_tarsusaItem.user)
			itemUser = q.get()
			each_tarsusaItem.usermodel = itemUser
			each_tarsusaItem.put()
			#print 'changed' + each_tarsusaItem.name

	#####################################################


