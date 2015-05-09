#!/usr/bin/env python

import os
import tornado.ioloop
import tornado.web
import decoder

AVCONV = 'avconv'

class MainHandler(tornado.web.RequestHandler):
    def post(self):
        fbody = self.request.files['video'][0]['body']
        f = open('video.mp4', 'wb')
        f.write(fbody)
        f.close()
        try:
            os.system('rm -f *.bmp')
            os.system(AVCONV + ' -i video.mp4 -f image2 out%03d.bmp')
            self.write(decoder.run())
        except Exception as e:
            print(type(e))
            print(e)
            self.write('Error: ' + str(e))

application = tornado.web.Application([
    (r"/", MainHandler),
])

if __name__ == "__main__":
    application.listen(25252)
    tornado.ioloop.IOLoop.instance().start()
