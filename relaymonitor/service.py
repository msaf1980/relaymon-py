import datetime
import re
import subprocess
import collections

# $ systemctl status carbonapi
# Unit carbonapi.service could not be found.
#
#
# $ systemctl status bioyino
#  bioyino.service - High performance and high-precision multithreaded StatsD server
#    Loaded: loaded (/etc/systemd/system/bioyino.service; disabled; vendor preset: disabled)
#    Active: failed (Result: exit-code) since Mon 2018-12-03 16:27:03 +05; 24h ago
#  Main PID: 23417 (code=exited, status=101)
#
# Dec 03 16:27:03 safronov.kontur systemd[1]: Started High performance and high-precision multithreaded StatsD server.
# Dec 03 16:27:03 safronov.kontur bioyino[23417]: thread 'main' panicked at 'opening config file at /etc/bioyino.toml: Os { code: 2, kind: NotFound, message: "No such file or directory" }', libcore/result.rs:1009>
# Dec 03 16:27:03 safronov.kontur bioyino[23417]: note: Run with `RUST_BACKTRACE=1` for a backtrace.
# Dec 03 16:27:03 safronov.kontur systemd[1]: bioyino.service: Main process exited, code=exited, status=101/n/a
# Dec 03 16:27:03 safronov.kontur systemd[1]: bioyino.service: Failed with result 'exit-code'.

# Systemd Service Status
class ServiceStatus:
    ACTIVE = 0
    INACTIVE = 1
    FAILED = 2
    NOT_FOUND = 3
    RESTARTED = 4
    UNKNOWN = -1

    rSince = re.compile(r'since [A-Za-z]+ ([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2}) ([\+-][0-9]+);')

    rPID = re.compile(r' PID: +([0-9]+) +')

    @staticmethod
    def toStr(status):
        if status == ServiceStatus.ACTIVE:
            return "active"
        elif status == ServiceStatus.RESTARTED:
            return "restarted"
        elif status == ServiceStatus.INACTIVE:
            return "inactive"
        elif status == ServiceStatus.FAILED:
            return "failed"
        elif status == ServiceStatus.NOT_FOUND:
            return "not found"
        else:
            return "unknown"

    @staticmethod
    def parse_datetime(s):
        match = ServiceStatus.rSince.findall(s)
        try:
            dateTime = datetime.datetime(int(match[0][0]), int(match[0][1]), int(match[0][2]), hour=int(match[0][3]), minute=int(match[0][4]), second=int(match[0][5]))
            return dateTime
        except Exception as e:
            #print str(e)
            return None

    @staticmethod
    def parse_pid(s):
        match = ServiceStatus.rPID.findall(s)
        try:
            return int(match[0])
        except Exception as e:
            #print str(e)
            return None

    @staticmethod
    def getStatus(service):
        cmd = '/bin/systemctl status %s.service' % service
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        stdout_list = out.split('\n')
        stderr_list = err.split('\n')
        rc = proc.returncode

        #print(stdout_list)
        #print(stderr_list)
        #print(rc)
        status = ServiceStatus.UNKNOWN
        startTime = None
        mainPid = None
        if rc == 0:
            for line in stdout_list:
                if 'Active: active ' in line:
                    status = ServiceStatus.ACTIVE
                    startTime = ServiceStatus.parse_datetime(line)
                elif 'Main PID: ' in line:
                    mainPid = ServiceStatus.parse_pid(line)
        else:
            for line in stdout_list:
                if 'Active: failed ' in line:
                    status = ServiceStatus.FAILED
                    startTime = ServiceStatus.parse_datetime(line)
                elif 'Active: inactive ' in line:
                    status = ServiceStatus.INACTIVE
                    startTime = ServiceStatus.parse_datetime(line)

            for line in stderr_list:
                if 'service could not be found' in line:
                    status = ServiceStatus.NOT_FOUND

        return status, startTime, mainPid

# Service State
class Service:
    def __init__(self, service, config, checkCount, maxFailCount, resetCount):
        self.service = service
        self.config = config
        self.status = collections.deque(maxlen=checkCount)
        self.startTime = None
        self.fail = False
        self.maxFailCount = maxFailCount
        self.checkCount = checkCount
        self.resetCount = resetCount

    def check_fail(self):
        (status, startTime, mainPid) = ServiceStatus.getStatus(self.service)
        if status ==  ServiceStatus.NOT_FOUND:
            raise ValueError("service %s is unknown" % self.service)
        elif status == ServiceStatus.ACTIVE and startTime != self.startTime:
            # try to detect restart service
            if len(self.status) > 0:
                self.status.append(ServiceStatus.RESTARTED)
            else:
                # first check
                self.status.append(status)
            self.startTime = startTime
        else:
            self.status.append(status)


        if len(self.status) == self.checkCount:
            # Detect service flap
            failCount = 0
            activeCount = 0
            for s in self.status:
                if s == ServiceStatus.ACTIVE:
                    activeCount += 1
                    # Reset fail counter
                    if activeCount >= self.resetCount:
                        if failCount > 0:
                            failCount = 0
                            self.fail = False
                else:
                    failCount += 1
                    activeCount = 0

            # Fail service
            if failCount >= self.maxFailCount:
                err = None
                if not self.fail:
                    self.fail = True
                    err = "service %s failed" % self.service
                return True, err

        return False, None

    def last_status(self):
        if len(self.status) == 0:
            return ServiceStatus.UNKNOWN
        else:
            return self.status[-1]
