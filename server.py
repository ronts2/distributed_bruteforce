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
MAX_JOB_QUEUE_SIZE: int
    the maximum amount of jobs in the queue at once.

"""

from threading import Thread
from SocketServer import TCPServer, ThreadingMixIn, BaseRequestHandler
import socket
import Queue
import mysocket


MAX_NUM = 10000000000
JOB_RANGE_SIZE = 10000
JOB_TIMEOUT = 5
SERVER_IP = '0.0.0.0'
SERVER_PORT = 9900
LISTEN = 1
MAX_JOB_QUEUE_SIZE = 50


class JobManager(object):
    """This class offers thread-safe job management."""
    def __init__(self, max_num=MAX_NUM, range_size=JOB_RANGE_SIZE, max_job_queue_size=MAX_JOB_QUEUE_SIZE):
        """The class constructor.

        Parameters
        ----------
        max_num:  Union[int, long]
            the maximum number to check.
        range_size: Union[int, long]
            the size of each checking range.
        max_job_queue_size: int
            the maximum amount of jobs in the queue at once.
        """
        self.max_num = max_num
        self.range_size = range_size
        self.jobs = Queue.Queue(max_job_queue_size)

    def populate_job_queue(self):
        """Runs the queue populator thread."""
        populator = Thread(target=self._job_queue_populator)
        populator.start()

    def get(self):
        """Generates jobs.

        Returns
        -------
        Tuple[None, None]
            if no more jobs are available.
        Tuple[str, str]
            start and end of a job.
        """
        if not self.jobs.qsize():
            return None, None
        return self.jobs.get()

    def _job_queue_populator(self):
        """Populates the job queue with generated jobs.
        This is necessary to keep the job manager thread-safe.
        """
        for job in self._job_generator():
            self.jobs.put(job)

    def _job_generator(self, start=0):
        """Generates jobs.

        Parameters
        ----------
        start: Union[int, long]
            the initial range value.

        Yields
        ------
        Tuple[str, str]
            start and end of a job.
        """
        start = start
        end = start + self.range_size
        while start < self.max_num:
            yield str(start), str(end)
            start = end
            end += self.range_size


class Server(ThreadingMixIn, TCPServer, object):
    """This class is used for managing work between clients."""
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        """The class constructor.

        Parameters
        ----------
        server_address: Tuple[str, int]
            the address the server will be bound to.
        RequestHandlerClass: RequestHandler
            a class which is instantiated for each connection and is used to handle it.
        bind_and_activate: bool
            binds and activates the listener if True.
        """
        super(Server, self).__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.job_manager = JobManager()
        self.job_manager.populate_job_queue()


class Handler(BaseRequestHandler):
    """This class is used to handle new incoming connections."""

    def get_jobs(self, count):
        """Returns available jobs.

        Parameters
        ----------
        count: int
            number of requested jobs.

        Returns
        -------
        Tuple[None, None]
            if no more jobs are available.
        List[Tuple[str, str]]
            list of jobs.
        """
        jobs = []
        job = self.server.job_manager.get()
        if not any(job):
            return job
        jobs.append(job)
        for i in xrange(count - 1):
            job = self.server.job_manager.get()
            jobs.append(job) if any(job) else None
        return jobs

    def unparsed_recv(self):
        """Returns split received string."""
        msg = self.request.receive()
        if not msg:
            return None, None
        return msg.split(mysocket.DATA_SEPARATOR)

    def handle(self):
        """Handles a new incoming connection."""
        self.request = mysocket.MySocket(*self.client_address, _socket=self.request)
        msg_type, msg_data = self.unparsed_recv()
        if not msg_type:
            return
        print '{}:{} - \'{}\''.format(self.request.ip, self.request.port, ':'.join([msg_type, msg_data]))
        job_request = int(msg_data)
        jobs = self.get_jobs(job_request)
        if not any(jobs):
            return
        msg = mysocket.DATA_SEPARATOR.join([mysocket.RANGE_SEPARATOR.join(job) for job in jobs])
        self.request.send_msg(msg)
        self.request.settimeout(JOB_TIMEOUT)
        try:
            msg_type, msg_data = self.unparsed_recv()
        except socket.timeout:
            for job in jobs:
                self.server.job_manager.jobs.put(job)
            return
        if msg_type == mysocket.SUCCESS_REPLY:
            print 'FOUND:', msg_data
            self.server.shutdown()


def main():
    server = Server((SERVER_IP, SERVER_PORT), Handler)
    print 'Serving on {}:{} ...'.format(SERVER_IP, SERVER_PORT)
    server.serve_forever()


if __name__ == '__main__':
    main()
