"""This module contains the client logic and functionality.
The client is used to compute and check each given range of numbers
and try to brute force the original, not hashed value.

Attributes
----------
HASHED: str
    the given hashed string.
SERVER_IP: str
    the default ip the client connects to.
SERVER_PORT: int
    the default port the client connects to.

"""

import codecs
import socket
import Queue
from threading import Thread
import hashlib
from multiprocessing import cpu_count

import mysocket


HASHED = codecs.decode('EC9C0F7EDCC18A98B1F31853B1813301', 'hex')
SERVER_IP = socket.getfqdn()
SERVER_PORT = 9900
LISTEN = 1
CORE_NUM = cpu_count()


class Client(object):
    """This class holds the logic and functionality to brute force a hashed value.
    It is used to compute and check each given range of numbers and try to
    brute force the original, not hashed value.
    """
    def __init__(self, ip, port):
        """The class constructor.
        Parameters
        ----------
        ip: str
            the ip of the server (e.g. '0.0.0.0').
        port: int
            the port of the server (e.g. 9900).
        """
        self.ip = ip
        self.port = port
        self.ranges = Queue.Queue()

    def send(self, string):
        self.client = mysocket.MySocket(self.ip, self.port)
        self.connect()
        self.client.send_msg(string)

    def connect(self):
        """Connects to the server."""
        self.client.connect()
        print 'Connected to: {}:{}'.format(self.client.ip, self.client.port)

    def request_ranges(self):
        """Request ranges from the server."""
        self.send(mysocket.DATA_SEPARATOR.join([mysocket.REQUEST, str(CORE_NUM)]))
        self.response = self.client.receive()
        self.close_conn()

    def populate_queue(self):
        """Populates the range queue with (start, end) ranges."""
        ranges = self.response.split(mysocket.DATA_SEPARATOR)
        for r in ranges:
            start, end = r.split(mysocket.RANGE_SEPARATOR)
            self.ranges.put((long(start), long(end)))

    def check_range(self):
        start, end = self.ranges.get()
        for i in xrange(start, end):
            print 'trying: ' + str(i)
            m = hashlib.md5()
            m.update(str(i))
            result = m.digest()
            if result == HASHED:
                self.send(mysocket.DATA_SEPARATOR.join([mysocket.SUCCESS_REPLY, str(i)]))
                self.close_conn()
                exit()

    def check_queued_ranges(self):
        threads = [Thread(target=self.check_range) for i in xrange(self.ranges.qsize())]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def get_job(self):
        self.request_ranges()
        self.populate_queue()
        self.check_queued_ranges()
        self.close_conn()

    def close_conn(self):
        self.client.shutdown(socket.SHUT_RDWR)
        self.client.close()


def main():
    while True:
        client = Client(ip=SERVER_IP, port=SERVER_PORT)
        client.get_job()


if __name__ == '__main__':
    main()
