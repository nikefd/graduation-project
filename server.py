#!/usr/bin/python2

import Settings
import logging
import tornado.web
import tornado.httpserver
import tornado.websocket
import subprocess
import re

#logging.basicConfig(level=logging.INFO,
#                filename='myapp.log',
#                filemode='w')

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/websocket", WebSocketHandler),
        ]
        settings = {
            "template_path": Settings.TEMPLATE_PATH,
            "static_path": Settings.STATIC_PATH,
        }
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("editor.html")

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def on_message(self, message):
#        print type(message)
        print message
        umessage = eval("u'" + message + "'")
        print umessage
#        temp = re.findall('(?:\\\u)([\w]+)', message)    #change unicode to string
#        length = len(temp)
#        print length
#        print temp
#        result = ''
        # for char in temp:
#            print int(char, 16)
            # result = result + map(unichr, [int(char, 16)])[0]
#        print type(result)
        # print result
        umessage = umessage.encode("utf-8")
	f = open("test.cpp", "w")
	print >> f, umessage
	f.close()
	subprocess.call("./run.sh test.cpp > test.txt", shell=True)
	f = open("test.txt", "r")
	umessage = f.read()
	self.write_message(umessage)     #Sends the given message to the client of this Web Socket.

def main():
    applicaton = Application()
    http_server = tornado.httpserver.HTTPServer(applicaton)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
