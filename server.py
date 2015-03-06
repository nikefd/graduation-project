#!/usr/bin/python2

import Settings
import logging
import tornado.web
import tornado.httpserver
import tornado.websocket
import subprocess

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
#	logging.debug("This is a debug message")
#	logging.info("got message %r", message)
	f = open("test.cpp", "w")
	print >> f, message
	f.close()
	subprocess.call("./run.sh test.cpp > test.txt", shell=True)
	f = open("test.txt", "r")
	message = f.read()
	self.write_message(message)
#	self.write_message("this is ") #Sends the given message to the client of this Web Socket.

def main():
    applicaton = Application()
    http_server = tornado.httpserver.HTTPServer(applicaton)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
