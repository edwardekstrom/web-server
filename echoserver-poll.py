"""
A TCP echo server that handles multiple clients with polling.  Typing
Control-C will quit the server.
"""

import argparse

from poller import Poller

class Main:
    """ Parse command line options and perform the download. """
    def __init__(self):
        self.parse_arguments()

    def parse_arguments(self):
        ''' parse arguments, which include '-p' for port '''
        parser = argparse.ArgumentParser(prog='Echo Server', description='A simple echo server that handles one client at a time', add_help=True)
        parser.add_argument('-p', '--port', type=int, action='store', help='port the server will bind to',default=8080)
        parser.add_argument('-d', '--debug', type=bool, action='store', help='debug flag',default=False)
        self.args = parser.parse_args()

    def run(self):
        p = Poller(self.args.port)
        p.unimplementedMethods = ['HEAD','PUT','POST','DELETE','LINK','UNLINK']
        p.hosts = dict()
        p.media_types = dict()
        p.timeout = 0
        with open('web.conf', 'r') as f:
            for line in f:
                if not line in ['\n','\r\n']:
                    words = line.split()
                    if words[0] == 'host':
                        p.hosts[words[1]] = words[2]
                    if words[0] == 'media':
                        p.media_types[words[1]] = words[2]
                    if words[0] == 'parameter':
                        if words[1] == 'timeout':
                            p.timeout = words[2]
        p.run()

if __name__ == "__main__":
    m = Main()
    m.parse_arguments()
    try:
        m.run()
    except KeyboardInterrupt:
        pass
