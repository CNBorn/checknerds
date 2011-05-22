# -*- coding: utf-8 -*-
# CheckNerds - www.checknerds.com
# - utils/__init__.py

import re
from google.appengine.api import memcache

def gen_key_fac(in_key):
    def gen_key(*args, **kwargs):
        key = in_key
        para_re = re.compile(r"{(.*?)}")
        para_name_list = para_re.findall(key)
        for pos, para in enumerate(para_name_list):
            if para in kwargs.keys():
                value = kwargs[para]
                key = key.replace("{%s}" % para, str(value))
            elif pos <= len(args):
                value = args[pos]
                key = key.replace("{%s}" % para, str(value))
            else:
                raise
        return key
    return gen_key


def cache(key="default_mc_key", time=60*60*30):
    def _cache(func):
        gen_key=gen_key_fac(key)
        def _processor(*args, **kwargs):
            mkey = gen_key(*args, **kwargs)
            is_cached = memcache.get(mkey)
            if is_cached:
                return memcache.get(mkey)
            result = func(*args, **kwargs)
            memcache.set(mkey, result, time)
            return result
        return _processor
    return _cache


