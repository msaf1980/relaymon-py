from network import NetworkTcpSock

class CarbonCRelay:
    def __init__(self, config_path):
        self.config_path = config_path
        self.mtime = None
        self.backends = dict()
        self.loadConfig()


    def loadConfig(self):
        backends = self.readConfig()
        #for b in self.backends:
        #    if backends is None or backends.get(b) is None:
        #        self.backends[b].close()
        #        del self.backends[b]

        #self.backends = dict()
        pass

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
                        host = NetworkTcpSock(hostname, int(port))
                        hosts.append(host)
                        print("%s %s:%s" % (cluster_name, hostname, port))
            #         if cluster_type == "forward":
            #             cluster_type = Backends.STRATEGY_ALL
            #         backends.append(Backends(cluster_name, cluster_type, hosts))

                    #print(hosts)

            return backends