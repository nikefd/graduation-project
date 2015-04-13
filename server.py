#!/usr/bin/python2

import Settings
import logging
import tornado.web
import tornado.httpserver
import tornado.websocket
import subprocess
import base64
import os
import fcntl
import time
from subprocess import Popen, PIPE


def setNonBlocking(fd):
    """
    Set the file description of the given file descriptor to non-blocking.
    """
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    flags = flags | os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)

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
        global p
        message_r = base64.b64decode(message)
        print message_r
        if message_r[0:4] == "code":
            message_r = message_r[4:]
            f = open("test.cpp", "w")
            print >> f, message_r
            f.close()
            subprocess.call("./run.sh test.cpp", shell=True)
            f = open("test.txt", "r")
            message_s = f.read()
            if len(message_s) == 0:
                p = Popen("./a.out", stdin = PIPE, stdout = PIPE, stderr = PIPE, bufsize = 1)
                setNonBlocking(p.stdout)
                setNonBlocking(p.stderr)
                try:
                    time.sleep(.1)
                    message_s = p.stdout.read()
                except IOError:
                    pass
                else:
                    message_s = "code" + message_s
                    self.write_message(message_s)
                    print message_s
                if p.poll() != 0:
                    message_s = "input"
                    self.write_message(message_s)
            else:
                print message_s
                message_s = "code" + message_s
                self.write_message(message_s)
            f.close()
        elif message_r[0:4] == "docs":
            message_r = message_r[4:]
            docs = "example." + message_r
            print docs
            f = open("./docs/" + docs, "r")
            message_s = f.read()
            message_s = "docs" + message_s
            self.write_message(message_s)
            f.close()
        elif message_r[0:4] == "inpt":
            message_r = message_r[4:]
            p.stdin.write(message_r)
            p.stdin.write('\n')
            p.stdin.flush()
            try:
                time.sleep(.1)
                message_s = p.stdout.read()
            except IOError:
                pass
            else:
                message_s = "code" + message_s
                self.write_message(message_s)
                print message_s
            if p.poll() != 0:
                message_s = "input"
                self.write_message(message_s)
            else:
                message_s = "end"
                self.write_message(message_s)
#        self.write_message(message_s)     #Sends the given message to the client of this Web Socket.


def main():
    applicaton = Application()
    http_server = tornado.httpserver.HTTPServer(applicaton)
    http_server.listen(8889)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
