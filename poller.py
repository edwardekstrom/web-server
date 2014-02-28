import select
import socket
import sys
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO

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
            self.generateResponse(request)
            self.clients[fd].send('HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 3\r\nConnection: Keep-Alive\r\n\r\n123')
        else:
            self.poller.unregister(fd)
            self.clients[fd].close()
            del self.clients[fd]
            
    def generateResponse(self,request):
        hostname = request.headers['host']
        filePath = self.hosts[hostname]
        filePath += request.path
        print filePath
        try:
            f = open(filePath)
        except IOError as (errno,strerror):
            if errno == 13:
                print '403 Forbidden'
            elif errno == 2:
                print '404 Not Found'
            else:
                print '500 Internal Server Error'

class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        