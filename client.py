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
from itertools import islice, count

import mysocket


HASHED = codecs.decode('EC9C0F7EDCC18A98B1F31853B1813301', 'hex')
NUM_DIGITS = 10
SERVER_IP = socket.getfqdn()
SERVER_PORT = 9900
LISTEN = 1
CORE_NUM = cpu_count()


XRANGE = lambda start, stop, step=1: islice(count(start, step), (stop-start+step-1+2*(step<0))//step)


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
        self.found = False
        self.client = mysocket.MySocket(self.ip, self.port)

    def connect(self):
        self.client.connect()

    def request_ranges(self):
        """Request ranges from the server."""
        msg = mysocket.DATA_SEPARATOR.join([mysocket.REQUEST, str(CORE_NUM)])
        self.client.send_msg(msg)

    def populate_queue(self, response):
        """Populates the range queue with (start, end) ranges."""
        ranges = response.split(mysocket.DATA_SEPARATOR)
        for r in ranges:
            if not r:
                print 'No jobs available!'
                exit()
            start, end = r.split(mysocket.RANGE_SEPARATOR)
            self.ranges.put((start, end))

    def check_range(self):
        start, end = self.ranges.get()
        for i in XRANGE(long(start), long(end)):
            attempt = str(i).zfill(NUM_DIGITS)
            if self.found:
                return
            m = hashlib.md5()
            m.update(attempt)
            result = m.digest()
            if result == HASHED:
                self.client.send_msg(mysocket.DATA_SEPARATOR.join([mysocket.SUCCESS_REPLY, attempt]))
                self.found = True
                return

    def check_queued_ranges(self):
        raw_input('enter')
        threads = [Thread(target=self.check_range) for i in xrange(self.ranges.qsize())]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        if not self.found:
            self.client.send_msg(mysocket.DATA_SEPARATOR.join([mysocket.FAILURE_REPLY, '']))

    def get_job(self):
        self.connect()
        self.request_ranges()
        self.populate_queue(self.client.receive())
        self.check_queued_ranges()


def main():
    client = Client(SERVER_IP, SERVER_PORT)
    client.get_job()


if __name__ == '__main__':
    main()
