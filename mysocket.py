"""This module contains a custom socket class.

It is used to increase readability, modularity and ease of usage of socket-related functions.
Some constants are used as default values for the `MySocket` class.

Attributes
----------
SUCCESS_REPLY: str
    the starter (identifier) of a successful brute force attempt.
DATA_SEPARATOR: str
    a string used to separate message components.
EOD: str
    a string representing the End-Of-Data flag.
BUFSIZE: int
    the maximum amount of data to be received at once.
RANGE_SEPARATOR: str
    the separator of 2 numbers which represent a range.

"""

import socket

REQUEST = 'request'
SUCCESS_REPLY = 'success'
DATA_SEPARATOR = ':'
RANGE_SEPARATOR = '-'


# default values for `MySocket`
EOD = '\n\n'
BUFSIZE = 1024*8


class MySocket(socket.socket):
    """This class extends the usage of a python socket.
    It's used to hold info regarding the socket, in
    addition to having custom methods, redefining the usage
    of the socket.
    """
    def __init__(self, ip, port, bufsize=BUFSIZE, eod=EOD,
                 _socket=None):
        """The class constructor.

        Parameters
        ----------
        ip: str
            the ip the socket uses (e.g. '0.0.0.0').
        port: int
            the port the socket uses (e.g. 9900).
        eod: str
            a string representing the End-Of-Data flag.
        bufsize: int
            the maximum amount of data to be received at once.
        _socket: socket
            an existing socket object.

        """
        self.ip = ip
        self.port = port
        self.bufsize = bufsize
        self.eod = eod
        if _socket:
            super(MySocket, self).__init__(_sock=_socket)
        else:
            super(MySocket, self).__init__()

    def connect(self):
        """Connects to a remote socket."""
        super(MySocket, self).connect((self.ip, self.port))

    def receive(self):
        """Receives data from the socket.

        Returns
        -------
        str
            the received data.

        """
        data = ''
        while True:
            try:
                buf = super(MySocket, self).recv(self.bufsize)
            except socket.error as e:
                print e
                return ''
            if not buf:
                return ''
            if buf == self.eod:
                return data
            if buf.endswith(self.eod):
                return data + buf[:-len(self.eod)]
            data += buf

    def send_msg(self, string):
        """Sends data to the socket.

        Parameters
        ----------
        string: str
            the data to send.

        """
        super(MySocket, self).sendall(string)
        super(MySocket, self).sendall(self.eod)

    def accept(self):
        """Accepts a connection.

        Returns
        -------
        MySocket
            an accepted connection.

        """
        sock, (ip, port) = super(MySocket, self).accept()
        return MySocket(ip, port, _socket=sock)
