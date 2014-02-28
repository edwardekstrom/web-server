import select
import socket
import sys
import os
import time
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
from lazr.restfulclient.errors import BadRequest

class Poller:
    """ Polling server """
    def __init__(self,port):
        self.host = ""
        self.port = port
        self.open_socket()
        self.clients = {}
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
            # poll sockets
            try:
                fds = self.poller.poll(timeout=1)
            except:
                return
            for (fd,event) in fds:
                # handle errors
                if event & (select.POLLHUP | select.POLLERR):
                    self.handleError(fd)
                    continue
                # handle the server socket
                if fd == self.server.fileno():
                    self.handleServer()
                    continue
                # handle client socket
                result = self.handleClient(fd)

    def handleError(self,fd):
        self.poller.unregister(fd)
        if fd == self.server.fileno():
            # recreate server socket
            self.server.close()
            self.open_socket()
            self.poller.register(self.server,self.pollmask)
        else:
            # close the socket
            self.clients[fd].close()
            del self.clients[fd]

    def handleServer(self):
        (client,address) = self.server.accept()
        self.clients[client.fileno()] = client
        self.poller.register(client.fileno(),self.pollmask)

    def handleClient(self,fd):
        data = self.clients[fd].recv(self.size)
        if data:
            request = HTTPRequest(data)
            response = self.generateResponse(request)
            #print response
            self.clients[fd].send(response)
        else:
            self.poller.unregister(fd)
            self.clients[fd].close()
            del self.clients[fd]
    
    def get_time (self,t):
        gmt = time.gmtime (t)
        format = '%a, %d %b %Y %H:%M:%S GMT'
        time_string = time . strftime ( format , gmt )
        return time_string

        
    def generateResponse(self,request):
        hostname = request.headers['host']
        if not hostname in self.hosts.keys():
            hostname = 'default'
        filePath = self.hosts[hostname]
        filePath += request.path
        if filePath == 'web/':
            filePath += 'index.html'
        t = time.time()
        time_string = self.get_time(t)
        if request.command != 'GET':
            if request.command in self.unimplementedMethods:
                return 'HTTP/1.1 501 Not Implemented\r\nDate: '+ time_string + '\r\nServer: EddyPyServer/1.0\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n\r\n501'
            else:
                return 'HTTP/1.1 400 Bad Request\r\nDate: '+ time_string + '\r\nServer: EddyPyServer/1.0\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n\r\n400'
        #print filePath
        try:
            fileName, fileExtension = os.path.splitext(filePath)
            fileExtension = fileExtension.replace('.','')
            f = open(filePath)
            mod_time = os.stat(filePath).st_mtime
            mod_time_string = self.get_time(mod_time)
            #print mod_time_string
            size = os.stat(filePath).st_size
            #size = os.path.getsize(filePath)
            if request.command == 'GET':
                response = 'HTTP/1.1 200 OK\r\nDate: '+ time_string + '\r\nServer: EddyPyServer/1.0\r\nContent-Type: ' + self.media_types[fileExtension] +'\r\nContent-Length: ' + str(size) + '\r\nLast-Modified: ' + mod_time_string + '\r\n\r\n' + f.read()
            else:
                response = 'HTTP/1.1 200 OK\r\nDate: '+ time_string + '\r\nServer: EddyPyServer/1.0\r\nContent-Type: ' + self.media_types[fileExtension] +'\r\nContent-Length: ' + str(size) + '\r\nLast-Modified: ' + mod_time_string + '\r\n\r\n'
            #print 'name: ' + fileName + '\n' + 'file extension: ' + fileExtension 
            #print response
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
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        