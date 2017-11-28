"""This module contains the server logic and functionality.
The server is used to manage and distribute data to clients.

Attributes
----------
MAX_NUM: long
    the highest value to try.
JOB_RANGE_SIZE: int
    the size of the range to try on each core.
JOB_TIMEOUT: int
    the maximum amount of time for a client to respond before aborting the job.
SERVER_IP: str
    the default ip the server is bound to.
SERVER_PORT: int
    the default port the server is bound to.
LISTEN: int
    the maximum number of queued connections.

"""

from SocketServer import TCPServer, ThreadingMixIn, BaseRequestHandler
import socket  # used for socket.getfqdn()
import Queue
import mysocket


MAX_NUM = 10000000000
JOB_RANGE_SIZE = 10000
JOB_TIMEOUT = 5
SERVER_IP = socket.getfqdn()
SERVER_PORT = 9900
LISTEN = 1


class JobManager(object):
    """This class offers thread-safe job management."""
    def __init__(self, max_num=MAX_NUM, range_size=JOB_RANGE_SIZE):
        """The class constructor.

        Parameters
        ----------
        max_num:  Union[int, long]
            the maximum number to check.
        range_size: Union[int, long]
            the size of each checking range.
        """
        self.max_num = max_num
        self.range_size = range_size
        self.aborted_jobs = Queue.Queue()
        self._job_generator = self._get()

    def get(self):
        """Generates jobs.

        Returns
        ------
        Tuple[None, None]
            if no more jobs are available.
        Tuple[long, long]
            start and end of a job.
        """
        if self.aborted_jobs.qsize():
            return self.aborted_jobs.get()
        try:
            return next(self._job_generator)
        except StopIteration:
            return None, None

    def _get(self):
        """Generates jobs.

        Yields
        ------
        Tuple[long, long]
            start and end of a job.
        """
        start = 0
        end = self.range_size
        left = MAX_NUM - start
        while left > 0:
            yield str(start), str(end)
            left -= end
            start = end
            end += self.range_size


class Server(ThreadingMixIn, TCPServer, object):
    """This class contains the server """
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        super(Server, self).__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.job_manager = JobManager()


class Handler(BaseRequestHandler):
    def handle(self):
        self.request = mysocket.MySocket(*self.client_address, _socket=self.request)
        msg = self.request.receive()
        print '{}:{} - {}'.format(self.request.ip, self.request.port, msg)
        if not msg:
            return
        msg_type, msg_data = msg.split(mysocket.DATA_SEPARATOR)
        job_request = int(msg_data)
        jobs = []
        job = self.server.job_manager.get()
        if not any(job):
            return
        jobs.append(job)
        for i in xrange(job_request - 1):
            job = self.server.job_manager.get()
            jobs.append(job) if any(job) else None
        msg = mysocket.DATA_SEPARATOR.join([mysocket.RANGE_SEPARATOR.join(job) for job in jobs])
        self.request.send_msg(msg)
        self.request.settimeout(JOB_TIMEOUT)
        try:
            msg = self.request.receive()
            if not msg:
                return
        except socket.timeout:
            for job in jobs:
                self.server.job_manager.aborted_jobs.put(job)
            return
        msg_type, msg_data = msg.split(mysocket.DATA_SEPARATOR)
        if msg_type == mysocket.SUCCESS_REPLY:
            print 'FOUND:', msg_data


def main():
    server = Server((SERVER_IP, SERVER_PORT), Handler)
    server.serve_forever()


if __name__ == '__main__':
    main()
