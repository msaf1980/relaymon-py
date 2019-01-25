import socket
import collections

class Host:
    def __init__(self, host, port):
        self.address = (host, port)
        self.prev_fail = False
        self.fail = None
        self.error = None

    def try_connect(self, net_timeout):
        fail = True
        try:
            sock = socket.create_connection(self.address, timeout=10)
            sock.close()
            fail = False
            if not self.error is None:
                self.error = None
        except Exception as e:
            self.error = str(e)

        if self.fail != self.prev_fail:
            self.prev_fail = self.fail

        if fail != self.fail:
            self.fail = fail

        return not self.fail

    def __hash__(self):
        return hash(self.address)

    def __eq__(self, other):
        return (
                self.__class__ == other.__class__ and
                self.address == other.address
        )

    def __str__(self):
        if self.fail is None:
            status = ""
        elif self.fail:
            status = " failed: %s" % self.error
        else:
            status = " connected"

        return "%s:%s%s" % (self.address[0], self.address[1], status)

    def __repr__(self):
        return "'%s'" % self


class Cluster:
    def __init__(self, name):
        self.name = name
        self.hosts = []
        self.prev_fail = False
        self.fail = False

    def add(self, hostname, port):
        self.hosts.append(Host(hostname, int(port)))

    def try_connect(self, net_timeout):
        fail = True
        for b in self.hosts:
            if b.try_connect(net_timeout):
                fail = False

        if self.fail != self.prev_fail:
            self.prev_fail = self.fail

        if fail != self.fail:
            self.fail = fail

        return not self.fail


class ClusterGroup:
    def __init__(self, name, net_timeout, check_count, max_fail_count, reset_count):
        self.name = name
        self.net_timeout = net_timeout
        self.fail_status = collections.deque(maxlen=check_count)
        self.max_fail_count = max_fail_count
        self.check_count = check_count
        self.reset_count = reset_count
        self.fail = False
        self.backends = []

    def try_connect(self):
        connected = False
        for cluster in self.backends:
            if cluster.try_connect(self.net_timeout):
                connected = True

        self.fail_status.append(not connected)
        return connected

    def check_fail_status(self):
        if len(self.fail_status) == self.check_count:
            # Detect service flap
            fail_count = 0
            active_count = 0
            for s in self.fail_status:
                if s:
                    fail_count += 1
                    active_count = 0
                else:
                    active_count += 1
                    # Reset fail counter
                    if active_count >= self.reset_count:
                        if fail_count > 0:
                            fail_count = 0
                            self.fail = False
                            err = "cluster group %s recovered" % self.name

            # Fail service
            if fail_count >= self.max_fail_count:
                err = None
                if not self.fail:
                    self.fail = True
                    err = "cluster group %s failed" % self.name
                return True, err

        return False, None

    def last_status(self):
        if len(self.status) == 0:
            return None
        else:
            return self.status[-1]
