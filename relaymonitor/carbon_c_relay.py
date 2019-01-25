from .network import Cluster
from .network import ClusterGroup

class CarbonCRelay(ClusterGroup):
    def __init__(self, config_path, net_timeout, check_count, max_fail_count, reset_count):
        ClusterGroup.__init__(self, "relay", net_timeout, check_count, max_fail_count, reset_count)
        self.config_path = config_path
        #self.mtime = None
        self.backends = self.readConfig()

    def readConfig(self):
        backends = []
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

            for part in parts:
                part = part.strip()
                config_line_cluster = part.split()
                if config_line_cluster and config_line_cluster[0] == "cluster":
                    cluster_name = config_line_cluster[1]
                    #cluster_type = config_line_cluster[2]
                    cluster = Cluster(cluster_name)
                    for host_str in config_line_cluster[3:]:
                        hostname, port = host_str.split(":")
                        cluster.add(hostname, port)

                    backends.append(cluster)

            return backends

