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
import time
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
        if uid is None and not name:
            uid = os.getuid()
        if uid is not None:
            self.pw = pwd.getpwuid(uid)
        else:
            self.pw = pwd.getpwnam(name)
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

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/ws", Coding),
            (r"/uploadfile", Upload),
            (r"/search", Searching),
            (r"/search/add", AddInfo),
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
            xsrf_cookies=False,
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

class Coding(BaseHandler, tornado.web.RequestHandler):
    def get(self):
        if self.current_user:
            global username
            username = self.current_user.name
            self.render("coding.html", error=None)
        else:
            self.render("home.html")

class Upload(BaseHandler, tornado.web.RequestHandler):
    def post(self):
        savepath = "static/images/" + self.current_user.name + ".jpg"
        print savepath
        pic1 = base64.b64decode(self.get_argument("pic1"))
        f = open(savepath, 'w')
        f.write(pic1)
        f.close()
        items = self.db.query("SELECT * FROM share")
        for item in items:
            print item.address
            print item.name
        info = self.db.get("SELECT * FROM share WHERE name=%s", self.current_user.name)
        self.render("map.html", items=items, info=info)


class Searching(BaseHandler, tornado.web.RequestHandler):
    def get(self):
        if self.current_user:
            global username
            username = self.current_user.name
            items = self.db.query("SELECT * FROM share")
            for item in items:
                print item.address
                print item.name
            info = self.db.get("SELECT * FROM share WHERE name=%s", self.current_user.name)
            self.render("map.html", items=items, info=info)
        else:
            self.render("home.html")

class MainHandler(BaseHandler):
    def get(self):
        if self.current_user:
            global server_ip
            global username
            username = self.current_user.name
            self.render("editor.html", host=server_ip)
        else:
            self.render("home.html")

class AuthFileOperation(BaseHandler):
    def get(self):
        op = self.get_argument("operation")
        id = self.get_argument("id")
        self.set_header('Content-Type', 'application/json')
        if op == "get_node":
            node = id + '/' if id != '#' else '/userdata/' + self.current_user.name + '/'
            rslt = self.lst(node, id == '#')
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
            self.write(rslt)
        elif op == "create_node":
            node = id if id != '/' else '/userdata/' + self.current_user.name
            name = "New-node"
            type_node = self.get_argument("type")
            rslt = self.create(node, name, type_node != 'file')
            self.write(rslt)
        elif op == "rename_node":
            node = id if id != '/' else '/userdata/' + self.current_user.name
            name = self.get_argument("text")
            rslt = self.rename(node, name)
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
        subprocess.call("mv " + dir + ' ' + new, shell = True)
        return {'id' : new}

    def remove(self, node):
        dir = node
        if dir == '/userdata/' + self.current_user.name:
            raise Exception("Cannot remove the root dictionary!")
        subprocess.call("rm -rf " + dir, shell = True)
        rslt = {'status': 'OK'}
        return rslt

    def data(self, node):
        dir = node
        ext = dir[dir.rfind(".") + 1:]
        rslt = {'type' : ext, 'content' :'File not recognized!'}
        if os.path.isfile(dir):
            case = ['txt', 'text', 'md', 'js', 'json', 'css', 'html', 'htm', 'xml', 'c', 'cpp', 'h', 'sql', 'log', 'py', 'rb', 'php', 'htaccess', 'java']
            for item in case:
                if ext == item:
                    rslt['content'] = open(node).read(1000)
                    break
        return rslt

    def lst(self, node, with_root = False):
        dir = node
        lst = os.listdir(dir)
        res = []
        for item in lst:
            if item == '.' or item == '..' or item == None:
                continue
            if os.path.isdir(dir + '/' + item):
                res.append({"text" : item, "children" : True, "id" : dir + item, "icon" : "folder"})
            else:
                res.append({"text" : item, "children" : False, "id" : dir + item, "type" : "file", "icon" : "file file-" + item[item.rfind(".") + 1:] })
        if with_root and node == '/userdata/' + self.current_user.name + '/':
            res = {'text' : self.current_user.name, 'children' : res, 'id' : '/', 'icon' : 'folder', 'state' : {'open' : True, 'disable' : True}}
        return res

class AddInfo(BaseHandler):
    def post(self):
        print self.current_user.name
        print self.get_argument("address")
        print self.get_argument("share_email")
        print self.get_argument("interests")
        print self.get_argument("say")
        username = self.db.get("SELECT * FROM share WHERE name = %s",
                                self.current_user.name)
        if username:
            self.db.execute(
                "UPDATE share SET address=%s, share_email=%s, interests=%s, say=%s WHERE name=%s",
                self.get_argument("address"), self.get_argument("share_email"),
                self.get_argument("interests"), self.get_argument("say"),
                self.current_user.name)
        else:
            self.db.execute(
                "INSERT INTO share (name, address, share_email, interests, say, share) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                self.current_user.name, self.get_argument("address"),
                self.get_argument("share_email"), self.get_argument("interests"),
                self.get_argument("say"), 1)
        items = self.db.query("SELECT * FROM share")
        for item in items:
            print item.address
            print item.name
        info = self.db.get("SELECT * FROM share WHERE name=%s", self.current_user.name)
        self.render("map.html", items=items, info=info)

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
            subprocess.call("cp -r example /userdata/" + self.get_argument("name"), shell=True)
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

    waiters = set()
    terminals = set()
    def open(self, user, path):
        subprocess.call("docker rm -f " + self.current_user.name, shell= True)
        for waiter in WebSocketHandler.waiters:
            waiter.write_message("new_user")
            break
        WebSocketHandler.waiters.add(self)
        self.fd = None
        path = "/home/foo/workplace/graduation-project"
        self.path = path
        self.callee = User(name="tjide")
        self.pty()

    def on_close(self):
        WebSocketHandler.waiters.remove(self)

    def pty(self):
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            self.shell()
        else:
            self.communicate()

    def send_update(cls, message):
        message = base64.b64encode(message)
        for waiter in cls.waiters:
            try:
                waiter.write_message(message)
            except:
                logging.error("Error sending message", exc_info=True)

    def send_initvalue(cls, message):
        message = base64.b64encode(message)
        message = "initvalue" + message;
        for waiter in cls.waiters:
            waiter.write_message(message);
            waiter.write_message("make the sendall = 1")

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
            print read
            self.log.info('READ>%r' % read)
            global outlabel
            print outlabel
            read = "code" + read
            if read and len(read) != 0 and self.ws_connection and outlabel:
                self.write_message(read.decode('utf-8', 'replace'))
            else:
                events = ioloop.ERROR
            if read[-6:] == "/try$ ":   #************************************I change here*************************
                self.write_message("end")
                subprocess.call("docker rm -f " + self.current_user.name, shell= True)
                global username
                subprocess.call("rm -rf /userdata/" + username +"/temp", shell=True)
            else:
                self.write_message("input")
            outlabel = True

    def send_talking(cls, message, user):
        send_user = user + ": "
        send_message = base64.b64encode(message)
        for waiter in cls.waiters:
            try:
                waiter.write_message("talking" + send_user + send_message)
            except:
                logging.error("Error sending message", exc_info=True)

    def on_message(self, message):
        message_r = base64.b64decode(message)
        global username
	username = self.current_user.name
        if not hasattr(self, 'writer'):
            self.on_close()
            self.close()
            return
	if message_r[0:7] == "talking":
            self.send_talking(message_r[7:], username)
            return
        if message_r[0:9] == "initvalue":
            self.send_initvalue(message_r[9:])
            return
        if message_r[0:4] == "work":
            self.send_update(message_r[4:])
            return
        command = ""
        if message_r[0:4] == "dir:":
            message_r = message_r[4:]
            sepa = message_r.find(' ')
            dir = message_r[:sepa]
            content = message_r[sepa + 1:]
            if os.path.isdir(dir):
                raise Exception("Cannot execuse dir!")
            f = open(dir, "w")
            print >> f, content
            f.close()
            ext = dir[dir.rfind(".") + 1:]
            subprocess.call("mkdir /userdata/" + username + "/temp", shell=True)
            if ext == "c" or ext == "cpp":
                command = "docker run --rm -v /home/nikefd/workplace/userdata/" + username + ":/userdata/" + username + " nikefd/gcc g++ " + dir + " -o /userdata/" + username + "/temp/test && docker run -m 128m -c 512 --rm -i -v /home/nikefd/workplace/userdata/" + username + ":/data --name "+ username + " nikefd/gcc /data/temp/test"
            elif ext == "py":
                command = "docker run -m 128m -c 512 --rm -i -v /home/nikefd/workplace/userdata/" + username + ":/userdata/" + username + " nikefd/python python " + dir
            elif ext == "php":
                command = "docker run -m 128m -c 512 --rm -i -v /home/nikefd/workplace/userdata/" + username + ":/userdata/" + username + " nikefd/php php " + dir
            elif ext == "java":
                parent = dir[:dir.rfind("/")]
                jfile = dir[dir.rfind("/") + 1:]
                cls = jfile[:jfile.rfind(".")]
                command = "docker run --rm -v /home/nikefd/workplace/userdata/" + username + ":/userdata/" + username + " nikefd/java /usr/lib/jvm/default-jvm/bin/javac " + dir + " -d /userdata/" + username + "/temp && docker run -m 128m -c 512 --rm -i -v /home/nikefd/workplace/userdata/" + username + ":/userdata/" + username + " --name "+ username + " nikefd/java java -classpath " + "/userdata/" + username + "/temp " + cls
            elif ext == "js":
                self.write_message("codeI am feel really sorry, we haven't support js now! hhhhhhhhh")
            else:
                self.write_message("codeHey, what do you want to do ?")
                return
            self.writer.write(command.decode('utf-8', 'replace'))
            self.writer.write(u'\n')
            self.writer.flush()
        elif message_r[0:4] == "docs":
            message_r = message_r[4:]
            docs = "example." + message_r
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
