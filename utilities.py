# -*- coding: utf-8 -*-

# **************************************************************** 
# CheckNerds - www.checknerds.com
# version 1.0, codename Nevada
# - utilities.py
# Copyright (C) CNBorn, 2008
# http://blog.donews.com/CNBorn, http://twitter.com/CNBorn
#
# **************************************************************** 

import re

def get_UserAgent(str_user_agent):

	if re.search('iPod', str_user_agent):
		#iPod detected
		return 'iPod'
	elif re.search('iPhone', str_user_agent):
		#iPhone detected.
		return 'iPod'
	else:
		#Non-Apple device.
		return 'Non-iPod'




