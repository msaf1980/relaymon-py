from network import HostTcp

class CarbonCRelay:
    def __init__(self, config_path):
        self.config_path = config_path
        self.mtime = None
        self.backends = {}
        self.loadConfig()

    def loadConfig(self):
        backends = self.readConfig()

        for c in self.backends:
            cluster = self.backends[c]
            cluster_new = backends.get(c)
            for b in cluster:
                if backends is None or cluster_new is None or cluster_new.get(b) is None:
                    cluster[b].close()
                    del cluster[b]

            if cluster_new is None:
                del self.backends[c]

        if backends is None:
            return

        for c in backends:
            cluster_new = backends[c]
            cluster = self.backends.get(c)
            if cluster is None:
                cluster = []
                self.backends[c] = cluster

            for b in cluster_new:
                found = False
                for b_old in cluster:
                    if b == b_old:
                        found = True
                        break

                if not found:
                    cluster.append(b)

        print(self.backends)

    def readConfig(self):
        backends = {}
        with open(self.config_path) as f:
            config = []

            for line in f:
                line = line.strip()
                hash_position = line.find("#")
                if hash_position != -1:
                    line = line[0:hash_position]
                if line:
                    config.append(line)

            config_in_line = " ".join(config)
            parts = config_in_line.split(";")

            print(parts)

            for part in parts:
                part = part.strip()
                config_line_cluster = part.split()
                if config_line_cluster and config_line_cluster[0] == "cluster":
                    hosts = []
                    cluster_name = config_line_cluster[1]
                    cluster_type = config_line_cluster[2]
                    for host_str in config_line_cluster[3:]:
                        hostname, port = host_str.split(":")
                        host = HostTcp(hostname, int(port))
                        hosts.append(host)

                    backends[cluster_name] = hosts

            return backends