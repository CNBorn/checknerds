# -*- coding: utf-8 -*-
import sys
sys.path.append("../")

from google.appengine.ext import webapp
from base import tarsusaRequestHandler

import wsgiref.handlers
import memcache

from models import tarsusaUser

class Image(webapp.RequestHandler):
    def output_avatar(self, avatardata, memcached):
        # set the cache headers
        #lastmod = self.avatar.updated // don't have this field.
        fmt = '%a, %d %b %Y %H:%M:%S GMT'
        self.response.headers['Content-Type'] = 'image/jpeg'
        #self.response.headers.add_header('Content-Type', "image/jpg")
        self.response.headers.add_header('Cache-Control', 'max-age=86400')
        self.response.headers.add_header('Expires', (datetime.datetime.now() + datetime.timedelta(days=1)).strftime(fmt))
        self.response.headers.add_header('Last-Modified', datetime.datetime.now().strftime(fmt)) #lastmod.strftime(fmt)
        self.response.headers.add_header('Content-Transfer-Encoding', 'binary')
        #self.resposne.headers.add_header('Charset',"binary")

        if self.request.headers.has_key('If-Modified-Since'):
            #dt = self.request.headers['If-Modified-Since'].split(';')[0]
            #since = int(time.mktime(datetime.datetime.strptime(dt, '%a, %d %b %Y %H:%M:%S %Z').timetuple()))
            #if since > int(time.mktime((datetime.datetime.now()).timetuple())): #should be > lastmod
            if memcached:
                self.response.set_status(304)
            else:
                self.response.out.write(avatardata)
        else:
            self.response.out.write(avatardata)
 
    
    def get(self):
        #get 'avatar' is avatar_id
        #Add memcached here to improve the performence.
        usravatardata = memcache.get('img_useravatar' + self.request.get("avatar"))
        
        if usravatardata is not None:
            self.output_avatar(usravatardata, True)
        else:
            # Request it from BigTable
            AvatarUser = tarsusaUser.get_user(int(self.request.get("avatar")))          

            try:
                if AvatarUser.avatar:
                    if not memcache.set('img_useravatar' + self.request.get("avatar"), AvatarUser.avatar, 16384):
                        logging.error("Memcache set failed: When Loading avatar_image")
                    self.output_avatar(AvatarUser.avatar, False)
            except AttributeError:
                #Not found avatar in DB.
                avatardata = urlfetch.fetch("http://www.checknerds.com/img/default_avatar.jpg", headers={'Content-Type': "image/jpg"})
                if avatardata.status_code == 200:
                    avatardata = avatardata.content
                    memcache.set('img_useravatar' + self.request.get("avatar"), avatardata, 16384)
                    self.output_avatar(avatardata, False)
                else:
                    self.redirect("/img/default_avatar.jpg")
                #self.error(404)
                #should read the default img pic and write it out.

def main():
    application = webapp.WSGIApplication([
        ('/image', Image),
        ],debug=True)

    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
      main()
