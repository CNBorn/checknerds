# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 0.7, codename Nevada
# - ErrorPages.py
# Copyright (C) CNBorn, 2008
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn
#
#
#
#
# **************************************************************** 



class UserNotFound(tarsusaRequestHandler):
	def get(self):
		




def main():
	application = webapp.WSGIApplication([('/error/user_not_found', UserNotFound),
									   ('/error/.+',OtherError)],
                                       debug=True)

	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
