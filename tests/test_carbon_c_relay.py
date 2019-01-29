import time
import os
import signal
import unittest

from relaymonitor.carbon_c_relay import CarbonCRelay
import servers


class CarbonCRelayTest(unittest.TestCase):
    def test_relay_backends(self):
        check_interval = 10
        check_count = 6
        fail_count = 3
        reset_count = 2
        recovery_interval = 80

        relay = CarbonCRelay('carbon-c-relay.conf', 10, check_count, fail_count, reset_count)
        cluster_count = 0
        backend_count = 0
        for cluster in relay.backends:
            cluster_count += 1
            for b in cluster.hosts:
                backend_count += 1

        self.assertEqual(cluster_count, 2)
        self.assertEqual(backend_count, 4)

        servers_list = {}
        try:
            for i in range(1, check_count):
                self.assertEqual(relay.try_connect(), False)
                (fail, msg) = relay.check_fail_status()
                self.assertEqual(fail, False)
                self.assertEqual(msg, None)
                for cluster in relay.backends:
                    for b in cluster.hosts:
                        self.assertEqual(b.fail, True)

            self.assertEqual(relay.try_connect(), False)
            # fail_count reached. msg must be set
            (fail, msg) = relay.check_fail_status()
            self.assertEqual(fail, True)
            self.assertEqual(msg, 'cluster group relay failed')

            (fail, msg) = relay.check_fail_status()
            self.assertEqual(fail, True)
            self.assertEqual(msg, None)

            # Start backends
            for cluster in relay.backends:
                for b in cluster.hosts:
                    server = servers.SimpleTCPServer(b.address[0], b.address[1])
                    server.start_listening()
                    servers_list[b.address] = server

            for i in range(1, reset_count):
                self.assertEqual(relay.try_connect(), True)
                (fail, msg) = relay.check_fail_status()
                self.assertEqual(fail, True)
                self.assertEqual(msg, None)
                for cluster in relay.backends:
                    for b in cluster.hosts:
                        self.assertEqual(b.fail, False)

            self.assertEqual(relay.try_connect(), True)
            # reset_count reached. msg must be set
            (fail, msg) = relay.check_fail_status()
            self.assertEqual(fail, False)
            self.assertEqual(msg, 'cluster group relay recovered')

            self.assertEqual(relay.try_connect(), True)
            (fail, msg) = relay.check_fail_status()
            self.assertEqual(fail, False)
            self.assertEqual(msg, None)

            for cluster in relay.backends:
                for b in cluster.hosts:
                    self.assertEqual(b.fail, False)

        finally:
            for a in servers_list:
                servers_list[a].stop()
            for a in servers_list:
                servers_list[a].terminate()


if __name__ == '__main__':
    unittest.main()
