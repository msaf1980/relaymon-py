from service import ServiceStatus, Service

class CarbonCRelay:
    def __init__(self, config):
        self.config = config
        self.mtime = None
        self.clusters = dict()
        self.loadConfig()


    def loadConfig(self):
        clusters = self.readConfig()
        for s in self.clusters:
            self.clusters_sock[s].close()
            del self.clusters_sock[s]

        self.clusters = dict()
        pass

    def readConfig(self):
        return None