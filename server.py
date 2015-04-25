#!/usr/bin/python2

import struct
import termios
import tornado.process
import tornado.options
import sys
import signal
import pwd
import time
import io
import Settings
import logging
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.websocket
import subprocess
import base64
import os
import fcntl
import pty
from subprocess import Popen, PIPE
from logging import getLogger

ioloop = tornado.ioloop.IOLoop.instance()
log = getLogger()
class Route(tornado.web.RequestHandler):
    @property
    def log(self):
        return log

class User(object):
    def __init__(self, uid=None, name=None):
        print "uid"
        print uid
        if uid is None and not name:
            uid = os.getuid()
            print "uid2"
            print uid
        if uid is not None:
            self.pw = pwd.getpwuid(uid)
            print "here is"
            print self.pw
        else:
            self.pw = pwd.getpwnam(name)
            print "here is pw"
            print self.pw
        if self.pw is None:
            raise LookupError('Unknown user')

    @property
    def uid(self):
        return self.pw.pw_uid

    @property
    def gid(self):
        return self.pw.pw_gid

    @property
    def name(self):
        return self.pw.pw_name

    @property
    def dir(self):
        return self.pw.pw_dir

    @property
    def shell(self):
        return self.pw.pw_shell

    @property
    def root(self):
        return self.uid == 0

    def __eq__(self, other):
        if other is None:
            return False
        return self.uid == other.uid

    def __repr__(self):
        return "%s [%r]" % (self.name, self.uid)

#logging.basicConfig(level=logging.INFO,
#                filename='myapp.log',
#                filemode='w')

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/websocket(?:/user/([^/]+))?/?(?:/wd/(.+))?", WebSocketHandler),
        ]
        settings = {
            "template_path": Settings.TEMPLATE_PATH,
            "static_path": Settings.STATIC_PATH,
        }
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("editor.html")

class WebSocketHandler(Route, tornado.websocket.WebSocketHandler):

    terminals = set()
    def open(self, user, path):
        self.fd = None
        path = "/home/nikefd/workplace/graduation-project"
        self.path = path
        # print "path"
        # print path
        self.callee = User(name='nikefd')
        self.pty()

    def pty(self):
        self.pid, self.fd = pty.fork()
        # print "pid fd:"
        # print self.pid
        # print self.fd
        if self.pid == 0:
            self.shell()
        else:
            self.communicate()

    def shell(self):
        # print "callee:"
        # print self.callee
        try:
            os.chdir(self.path or self.callee.dir) #Change the current working directory to path
            # print "self.path"
            # print self.path
            # print "self.callee.dir"
            # print self.callee.dir
        except:
            pass
        env = os.environ
        if os.path.exists('/usr/bin/su'):
            args = ['/usr/bin/su']
        else:
            args = ['/bin/su']
        args.append(self.callee.name)
        os.execvpe(args[0], args, env)

    def communicate(self):
        fcntl.fcntl(self.fd, fcntl.F_SETFL, os.O_NONBLOCK)

        print "self.fd:"
        print self.fd
        def utf8_error(e):
            self.log.error(e)

        self.reader = io.open(
            self.fd,
            'rb',
            buffering=0,
            closefd=False
        )
        self.writer = io.open(
            self.fd,
            'wt',
            encoding='utf-8',
            closefd=False
        )
        ioloop.add_handler(
            self.fd, self.shell_handler, ioloop.READ | ioloop.ERROR)

    def shell_handler(self, fd, events):
        if events & ioloop.READ:
            try:
                read = self.reader.read()
            except IOError:
                read = ''

            self.log.info('READ>%r' % read)
            print "read:"
            print read
            print "read-end"
            read = "code" + read
            if read and len(read) != 0 and self.ws_connection:
                self.write_message(read.decode('utf-8', 'replace'))
                self.write_message("input")
            else:
                events = ioloop.ERROR

    def on_message(self, message):
        if not hasattr(self, 'writer'):
            self.on_close()
            self.close()
            return
        command = ""
        message_r = base64.b64decode(message)
        print message_r
        if message_r[0:4] == "code":
            message_r = message_r[4:]
            if message_r[0:4] == "cpp ":
                message_r = message_r[4:]
                f = open("test.cpp", "w")
                print >> f, message_r
                f.close()
                command = "g++ test.cpp -o test && ./test"
            elif message_r[0:4] == "js  ":
                message_r = message_r[4:]
                message_s = ''
                label = "js"
            elif message_r[0:4] == "java":
                message_r = message_r[4:]
                label = "java"
            elif message_r[0:4] == "html":
                message_r = message_r[4:]
                label = "html"
            elif message_r[0:4] == "py  ":
                message_r = message_r[4:]
                f = open("test.py", "w")
                print >> f, message_r
                f.close()
                command = "python test.py"
            elif message_r[0:4] == "php ":
                message_r = message_r[4:]
                message_s = ''
                label = "php"
            self.writer.write(command.decode('utf-8', 'replace'))
            self.writer.write(u'\n')
            self.writer.flush()

        elif message_r[0:4] == "docs":
            message_r = message_r[4:]
            docs = "example." + message_r
            print docs
            f = open("./docs/" + docs, "r")
            message_s = f.read()
            message_s = "docs" + message_s
            self.write_message(message_s)
        elif message_r[0:4] == "inpt":
            message_r = message_r[4:]
            message_r = message_r + "\n"
            self.writer.write(message_r.decode('utf-8', 'replace'))
            self.writer.flush()
            self.write_message("input")

def main():
    applicaton = Application()
    http_server = tornado.httpserver.HTTPServer(applicaton)
    http_server.listen(8888)
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == "__main__":
    main()
