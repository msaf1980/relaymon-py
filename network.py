class Host:
    def __init__(self, host, port):
        self.host = host
        self.port = port


class NetworkTcpSock(Host):
    def __init__(self, host, port):
        Host.__init__(self, host, port)
        self.sock = None

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.close()
        except:
            pass

    def close(self):
        if not self.sock is None:
            self.sock.close()
            self.sock = None
