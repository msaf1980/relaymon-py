class Host:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __hash__(self):
        return hash((self.host, self.port))

    def __eq__(self, other):
        return (
                self.__class__ == other.__class__ and
                self.host == other.host and
                self.port == other.port
        )

    def __str__(self):
        return "%s:%s" % (self.host, self.port)

    __repr__ = __str__


class HostTcp(Host):
    def __init__(self, host, port):
        Host.__init__(self, host, port)
        self.sock = None
        self.failed = False

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.close()
        except:
            pass

    def __str__(self):
        state = " disconnected"
        if self.failed:
            state = " failed"
        elif not self.sock is None:
            state = " connected"

        return "\"%s:%s%s\"" % (self.host, self.port, state)

    __repr__ = __str__

    def close(self):
        if not self.sock is None:
            self.sock.close()
            self.sock = None
