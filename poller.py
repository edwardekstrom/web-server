import select
import socket
import sys
import os
import time
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
from _bsddb import EAGAIN
from errno import EWOULDBLOCK

class Poller:
    """ Polling server """
    def __init__(self,port):
        self.host = ""
        self.port = port
        self.open_socket()
        self.clients = {}
        self.last_active_times = {}
        self.caches = {}
        self.time_last_checked = time.time()
        self.size = 1024

    def open_socket(self):
        """ Setup the socket for incoming clients """
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
            self.server.bind((self.host,self.port))
            self.server.listen(5)
        except socket.error, (value,message):
            if self.server:
                self.server.close()
            print "Could not open socket: " + message
            sys.exit(1)

    def run(self):
        """ Use poll() to handle each incoming client."""
        self.poller = select.epoll()
        self.pollmask = select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR
        self.poller.register(self.server,self.pollmask)
        while True:
            try:
                fds = self.poller.poll(timeout=1)
            except:
                return
            for (fd,event) in fds:
                if event & (select.POLLHUP | select.POLLERR):
                    self.handleError(fd)
                    continue
                if fd == self.server.fileno():
                    self.handleServer()
                    continue
                result = self.handleClient(fd)
            if(time.time() - self.time_last_checked > self.timeout):
                self.sweep()
                self.time_last_checked = time.time()

    def sweep(self):
        deleteAll = []
        for fd,lastTime in self.last_active_times.iteritems():
            if(time.time() - lastTime > 1):
                deleteAll.append(fd)
        for fd in deleteAll:
            self.handleError(fd)
                
    def handleError(self,fd):
        self.poller.unregister(fd)
        if fd == self.server.fileno():
            self.server.close()
            self.open_socket()
            self.poller.register(self.server,self.pollmask)
        else:
            self.clients[fd].send('')
            self.clients[fd].close()
            del self.clients[fd]
            del self.last_active_times[fd]
            del self.caches[fd]
            
    def handleServer(self):
        (client,address) = self.server.accept()
        self.clients[client.fileno()] = client
        self.caches[client.fileno()] = ''
        self.last_active_times[client.fileno()] = time.time()
        client.setblocking(0)
        self.poller.register(client.fileno(),self.pollmask)

    def handleClient(self,fd):
        while(True):
            data = ''
            try:
                data = self.clients[fd].recv(self.size)
            except socket.error as e:
                err = e.args[0]
                break
            if data:
                self.caches[fd] += data
                if '\r\n\r\n' in self.caches[fd]:
                    httpRequests = self.caches[fd].split('\r\n\r\n')
                    self.caches[fd] = httpRequests[-1]
                    del httpRequests[-1]
                    for req in httpRequests:
                        request = HTTPRequest(req + '\r\n\r\n')
                        response = self.generateResponse(request)
                        self.last_active_times[fd] = time.time()
                        while(len(response) > 0):
                            try:
                                gotTo = self.clients[fd].send(response)
                                response = response[gotTo:]
                            except socket.error as e:
                                True
                    break
            else:
                self.handleError(fd)
                break
        
    def get_time (self,t):
        gmt = time.gmtime (t)
        form = '%a, %d %b %Y %H:%M:%S GMT'
        time_string = time . strftime ( form , gmt )
        return time_string

        
    def generateResponse(self,request):
        hostname = request.headers['host']
        if not hostname in self.hosts.keys():
            hostname = 'default'
        filePath = self.hosts[hostname]
        filePath += request.path
        if filePath[-1] == '/':
            filePath += 'index.html'
        t = time.time()
        time_string = self.get_time(t)
        if request.command not in ['GET', 'HEAD']:
            if request.command in self.unimplementedMethods:
                return 'HTTP/1.1 501 Not Implemented\r\nDate: '+ time_string + '\r\nServer: EddyPyServer/1.0\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n\r\n501'
            else:
                return 'HTTP/1.1 400 Bad Request\r\nDate: '+ time_string + '\r\nServer: EddyPyServer/1.0\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n\r\n400'
        try:
            fileName, fileExtension = os.path.splitext(filePath)
            fileExtension = fileExtension.replace('.','')
            f = open(filePath)
            mod_time = os.stat(filePath).st_mtime
            mod_time_string = self.get_time(mod_time)
            size = os.stat(filePath).st_size
            if request.command == 'GET':
                fi = f.read()
                if 'Range' in request.headers:
                    strt = request.headers['Range']
                    strt = strt.replace('bytes=','')
                    bytes = strt.split('-')
                    startByte = int(bytes[0])
                    endByte = int(bytes[1])
                    fi = fi[startByte:endByte]
                    response = 'HTTP/1.1 200 OK\r\nDate: '+ time_string + '\r\nServer: EddyPyServer/1.0\r\nContent-Type: ' + self.media_types[fileExtension] +'\r\nContent-Length: ' + str(size) + '\r\nLast-Modified: ' + mod_time_string + '\r\n\r\n' + fi
                else:
                    response = 'HTTP/1.1 200 OK\r\nDate: '+ time_string + '\r\nServer: EddyPyServer/1.0\r\nContent-Type: ' + self.media_types[fileExtension] +'\r\nContent-Length: ' + str(size) + '\r\nLast-Modified: ' + mod_time_string + '\r\n\r\n' + fi
            else:
                response = 'HTTP/1.1 200 OK\r\nDate: '+ time_string + '\r\nServer: EddyPyServer/1.0\r\nContent-Type: ' + self.media_types[fileExtension] +'\r\nContent-Length: ' + str(size) + '\r\nLast-Modified: ' + mod_time_string + '\r\n\r\n'
            return response
        except IOError as (errno,strerror):
            if errno == 13:
                return 'HTTP/1.1 403 Forbidden\r\nDate: '+ time_string + '\r\nServer: EddyPyServer/1.0\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n\r\n403'
            elif errno == 2:
                return 'HTTP/1.1 404 Not Found\r\nDate: '+ time_string + '\r\nServer: EddyPyServer/1.0\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n\r\n404'
            else:
                return 'HTTP/1.1 500 Internal Server Error\r\nDate: '+ time_string + '\r\nServer: EddyPyServer/1.0\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n\r\n500'
        
class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        