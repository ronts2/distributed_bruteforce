"""This module contains the server logic and functionality.
The server is used to manage and distribute data to clients.

Attributes
----------
MAX_NUM: long
    the highest value to try.
CHECK_RANGE_SIZE: int
    the size of the range to try on each core.
SERVER_IP: str
    the default ip the server is bound to.
SERVER_PORT: int
    the default port the server is bound to.
LISTEN: int
    the maximum number of queued connections.

"""

import socket
import select
import Queue
import mysocket


MAX_NUM = 10000000000
CHECK_RANGE_SIZE = 1000000
SERVER_IP = socket.getfqdn()
SERVER_PORT = 9900
LISTEN = 1


class Server(object):
    """This class holds the logic and functionality to distribute
    and manage brute-force attacks.
    It is used to manage clients and the distributed data.
    """
    def __init__(self, ip=SERVER_IP, port=SERVER_PORT):
        """The class constructor.
        Parameters
        ----------
        ip: str
            the ip of the server (e.g. '0.0.0.0').
        port: int
            the port of the server (e.g. 9900).
        """
        self.server = mysocket.MySocket(ip, port)
        self.server.bind((ip, port))
        self.ranges = Queue.Queue()

    def activate_socket(self):
        """Activates the server socket listener."""
        self.server.listen(1)

    def populate_range_queue(self):
        """Populates the range queue with checking ranges."""
        start = CHECK_RANGE_SIZE
        end = CHECK_RANGE_SIZE
        left = MAX_NUM - start
        while left > 0:
            self.ranges.put((start, end))
            left -= end
            start = end
            end += CHECK_RANGE_SIZE

    def start_serving(self):
        """Starts serving clients."""
        self.activate_socket()
        self.populate_range_queue()
        while True:
            self.conn = self.server.accept()
            self.handle_conn()

    def close_conn(self):
        self.conn.shutdown(socket.SHUT_RDWR)
        self.conn.close()

    def handle_conn(self):
        self.msg = self.conn.receive()
        print '{}:{} - {}'.format(self.conn.ip, self.conn.port, self.msg)
        if not self.msg:
            return
        self.parse_msg()

    def parse_msg(self):
        self.msg_type, self.data = self.msg.split(mysocket.DATA_SEPARATOR)
        if self.msg_type == mysocket.REQUEST:
            self.do_request()
        else:
            self.do_reply()

    def do_request(self):
        qsize = self.ranges.qsize()
        if not qsize:
            return
        num_cores = int(self.data)
        num_ranges = num_cores if num_cores < qsize else qsize
        ranges = [mysocket.RANGE_SEPARATOR.join([str(i).zfill(10) for i in self.ranges.get()])
                  for r in xrange(num_ranges)]
        msg = mysocket.DATA_SEPARATOR.join(ranges)
        self.conn.send_msg(msg)
        self.close_conn()

    def do_reply(self):
        if self.msg_type == mysocket.SUCCESS_REPLY:
            print 'Found: {}'.format(self.data)
            self.close_conn()
            self.server.close()
            exit()


def main():
    server = Server()
    print 'Serving on {}:{} ...'.format(server.server.ip, server.server.port)
    server.start_serving()


if __name__ == '__main__':
    main()
