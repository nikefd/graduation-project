#!/usr/bin/python2

import struct
import termios
import tornado.process
import tornado.options
import sys
import signal
import pwd
import io
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

import bcrypt
import concurrent.futures
import MySQLdb
import markdown
import os.path
import re
import torndb
import tornado.escape
from tornado import gen
import tornado.httpserver
import tornado.options
import unicodedata
import socket
from tornado.options import define, options

ip = os.getenv("TOMYSQL_PORT_3306_TCP_ADDR")

myname = socket.getfqdn(socket.gethostname(  ))
server_ip = socket.gethostbyname(myname)
username = None
define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default=ip + ":3306", help="tjide database host")
define("mysql_database", default="tjide", help="tjide database name")
define("mysql_user", default="root", help="tjide database user")
define("mysql_password", default="admin", help="tjide database password")

# A thread pool to be used for password hashing with bcrypt.
executor = concurrent.futures.ThreadPoolExecutor(2)



ioloop = tornado.ioloop.IOLoop.instance()
log = getLogger()
outlabel = True
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
            (r"/auth/create", AuthCreateHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),
            (r"/auth/fileop", AuthFileOperation),
        ]
        settings = dict(
            blog_title=u"TJIDE",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/auth/login",
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        # Have one global connection to the tjide DB across all handlers
        self.db = torndb.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        user_id = self.get_secure_cookie("tjide_user")
        if not user_id: return None
        return self.db.get("SELECT * FROM user WHERE id = %s", int(user_id))

class MainHandler(BaseHandler):
    def get(self):
        if self.current_user:
            global server_ip
            global username
            username = self.current_user.name
            self.render("editor.html", host=server_ip)
            subprocess.call("touch " + self.current_user.name + ".cpp", shell=True)
        else:
            self.render("home.html")

class AuthFileOperation(BaseHandler):
    def get(self):
        print "operation"
        print self.get_argument("operation")
        op = self.get_argument("operation")
        id = self.get_argument("id")
        self.set_header('Content-Type', 'application/json')
        if op == "get_node":
            node = id + '/' if id != '#' else '/userdata/' + self.current_user.name + '/'
            print "node:"
            print node
            rslt = self.lst(node, id == '#')
            print "rslt:"
            print rslt
            i = 0
            if type(rslt) == list:
                if len(rslt) == 0:
                    rslt = "[]"
                    self.write(rslt)
                elif len(rslt) == 1:
                    rslt = rslt[0]
                    self.write(rslt)
                else:
                    self.write("[")
                    while i < len(rslt) - 1:
                        self.write(rslt[i])
                        i = i + 1
                        self.write(", ")
                    self.write(rslt[i])
                    self.write("]")
            else:
                self.write(rslt)
        elif op == "get_content":
            node = id if id != '#' else '/userdata/' + self.current_user.name
            rslt = self.data(node)
            print "rslt"
            print rslt
            self.write(rslt)
        elif op == "create_node":
            node = id if id != '/' else '/userdata/' + self.current_user.name
            name = "New-node"
            type_node = self.get_argument("type")
            rslt = self.create(node, name, type_node != 'file')
            print rslt
            self.write(rslt)
        elif op == "rename_node":
            print "rename_node id:"
            print id
            node = id if id != '/' else '/userdata/' + self.current_user.name
            print "rename_node:"
            print node
            name = self.get_argument("text")
            rslt = self.rename(node, name)
            print rslt
            self.write(rslt)
        elif op == "delete_node":
            node = id if id != '/' else '/userdata/' + self.current_user.name
            rslt = self.remove(node)
            self.write(rslt)
        elif op == "move_node":
            node = id
            parent = self.get_argument("parent")
            parn = parent if parent != '/' else '/userdata/' + self.current_user.name
            rslt = self.move(node, parn)
            self.write(rslt)
        elif op == "copy_node":
            node = id
            parent = self.get_argument("parent")
            parn = parent if parent != '/' else '/userdata/' + self.current_user.name
            rslt = self.copy(node, parn)
            self.write(rslt)

    def copy(self, node, parn):
        tmp = node.split('/')
        name = tmp[-1]
        if os.path.isdir(node):
            subprocess.call("cp -r " + node + ' ' + parn + '/' + name, shell = True)
        else:
            subprocess.call("cp " + node + ' ' + parn + '/' + name, shell = True)
        return {'id' : parn + '/' + name}

    def move(self, node, parn):
        tmp = node.split('/')
        name = tmp[-1]
        subprocess.call("mv " + node + ' ' + parn + '/' + name, shell = True)
        return {'id' : parn + '/' + name}

    def create(self, node, name, mkdir = False):
        dir = node
        if mkdir:
            subprocess.call("mkdir " + dir + '/' + name, shell = True)
        else:
            subprocess.call("touch " + dir + '/' + name, shell = True)
        return {'id' : dir + '/' + name}

    def rename(self, node, name):
        dir = node
        if dir == '/userdata/' + self.current_user.name:
            raise Exception("Cannot rename the root dictionary!")
        if not re.search('^[^\\/:\*\?\|"<>]+$' , name):
            raise Exception("Invalid name!")
        new = node.split("/")
        new.pop()
        new.append(name)
        str = '/'
        new = str.join(new)
        print "mv " + dir + ' ' + new
        subprocess.call("mv " + dir + ' ' + new, shell = True)
        return {'id' : name}

    def remove(self, node):
        dir = node
        if dir == '/userdata/' + self.current_user.name:
            raise Exception("Cannot remove the root dictionary!")
        subprocess.call("rm -rf " + dir, shell = True)
        rslt = {'status': 'OK'}
        return rslt

    def data(self, node):
        dir = node
        if os.path.isfile(dir):
            ext = dir[dir.rfind(".") + 1:]
            rslt = {'type' : ext, 'content' :'File not recognized!'}
            case = ['txt', 'text', 'md', 'js', 'json', 'css', 'html', 'htm', 'xml', 'c', 'cpp', 'h', 'sql', 'log', 'py', 'rb', 'php', 'htaccess', 'java']
            for item in case:
                if ext == item:
                    rslt['content'] = open(node).read(1000)
                    break
        else:
            rslt = ''
        return rslt

    def lst(self, node, with_root = False):
        dir = node
        print "dir:"
        print dir
        lst = os.listdir(dir)
        res = []
        for item in lst:
            if item == '.' or item == '..' or item == None:
                continue
            if os.path.isdir(dir + '/' + item):
                res.append({"text" : item, "children" : True, "id" : dir + item, "icon" : "folder"})
                print "dir"
            else:
                res.append({"text" : item, "children" : False, "id" : dir + item, "type" : "file", "icon" : "file file-" + item[item.rfind(".") + 1:] })
                print "file"
        if with_root and node == '/userdata/' + self.current_user.name + '/':
            res = {'text' : self.current_user.name, 'children' : res, 'id' : '/', 'icon' : 'folder', 'state' : {'open' : True, 'disable' : True}}
        print "res:"
        print res
        print "lst:"
        print lst
        print "node:"
        print node
        print "with_root:"
        print with_root
        return res

class AuthCreateHandler(BaseHandler):
    def get(self):
        self.render("create_author.html", error=None)

    @gen.coroutine
    def post(self):
        author = self.db.get("SELECT * FROM user WHERE email = %s",
                             self.get_argument("email"))
        username = self.db.get("SELECT * FROM user WHERE name = %s",
                             self.get_argument("name"))
        if not author:
            if username:
                self.render("create_author.html", error="The username is already being used.")
                return
            if len(self.get_argument("email")) < 7 or re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", self.get_argument("email")) == None:
                self.render("create_author.html", error="Email must be a valid email address.")
                return
            if len(self.get_argument("name")) == 0:
                self.render("create_author.html", error="Username is a required field.")
                return
            if len(self.get_argument("password")) == 0:
                self.render("create_author.html", error="Password is a required field.")
                return
            if len(self.get_argument("password")) < 6:
                self.render("create_author.html", error="Password must be at least 6 characters long.")
                return
            hashed_password = yield executor.submit(
                bcrypt.hashpw, tornado.escape.utf8(self.get_argument("password")),
                bcrypt.gensalt())
            author_id = self.db.execute(
                "INSERT INTO user (email, name, hashed_password) "
                "VALUES (%s, %s, %s)",
                self.get_argument("email"), self.get_argument("name"),
                hashed_password)
            # Create the user directionary when register
            subprocess.call("mkdir /userdata/" + self.get_argument("name"), shell=True)
            self.set_secure_cookie("tjide_user", str(author_id))
            self.redirect("/")
        else:
            self.render("create_author.html", error="The email is already being used.")


class AuthLoginHandler(BaseHandler):
    def get(self):
        # If there are no user, redirect to the account creation page.
        self.render("login.html", error=None)

    @gen.coroutine
    def post(self):
        author = self.db.get("SELECT * FROM user WHERE email = %s",
                             self.get_argument("email"))
        if not author:
            self.render("login.html", error="email not found")
            return
        hashed_password = yield executor.submit(
            bcrypt.hashpw, tornado.escape.utf8(self.get_argument("password")),
            tornado.escape.utf8(author.hashed_password))
        if hashed_password == author.hashed_password:
            self.set_secure_cookie("tjide_user", str(author.id))
            self.redirect("/")
        else:
            self.render("login.html", error="incorrect password")

class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("tjide_user")
        self.redirect("/")

class WebSocketHandler(BaseHandler, Route, tornado.websocket.WebSocketHandler):

    terminals = set()
    def open(self, user, path):
        self.fd = None
        path = "/home/foo/workplace/graduation-project"
        self.path = path
        # print "path"
        # print path
        # self.callee = User(name=self.current_user.name)
        self.callee = User(name="tjide")
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
        try:
            os.chdir(self.path or self.callee.dir) #Change the current working directory to path
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
            global outlabel
            read = "code" + read
            if read and len(read) != 0 and self.ws_connection and outlabel:
                self.write_message(read.decode('utf-8', 'replace'))
            else:
                events = ioloop.ERROR
            self.write_message("input")
            outlabel = True

    def on_message(self, message):
        if not hasattr(self, 'writer'):
            self.on_close()
            self.close()
            return
        global username
        command = ""
        message_r = base64.b64decode(message)
        print message_r
        if message_r[0:4] == "code":
            message_r = message_r[4:]
            if message_r[0:4] == "cpp ":
                message_r = message_r[4:]
                f = open("/userdata/" + username +  "/test.cpp", "w")
                print >> f, message_r
                f.close()
                # command = "docker run --rm --volumes-from dbdata nikefd/gcc g++-4.8 /dbdata/foo/test.cpp -o /dbdata/foo/test && /dbdata/foo/test"
                command = "docker run --rm -v /home/nikefd/workplace/userdata/" + username + ":/data nikefd/gcc g++ /data/test.cpp -o /data/test && docker run --rm -i -v /home/nikefd/workplace/userdata/" + username + ":/data nikefd/gcc /data/test"
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
                f = open("/userdata/" + username +  "/test.py", "w")
                print >> f, message_r
                f.close()
                command = "docker run --rm -i -v /home/nikefd/workplace/userdata/" + username + ":/data nikefd/python python /data/test.py"
            elif message_r[0:4] == "php ":
                message_r = message_r[4:]
                f = open("/userdata/" + username +  "/test.php", "w")
                print >> f, message_r
                command = "docker run --rm -i -v /home/nikefd/workplace/userdata/" + username + ":/data nikefd/php php /data/test.php"
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
        global outlabel
        outlabel = False

def main():
    applicaton = Application()
    http_server = tornado.httpserver.HTTPServer(applicaton)
    http_server.listen(options.port)
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == "__main__":
    main()
