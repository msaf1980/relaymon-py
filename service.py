import datetime
import re
import subprocess

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


class ServiceStatus:
    ACTIVE = 0
    INACTIVE = 1
    FAILED = 2
    NOT_FOUND = 3
    UNSTABLE = 4
    UNKNOWN = -1

    def __init__(self, code):
        self.code = code

    def __str__(self):
        if self.code == ServiceStatus.ACTIVE:
            return "active"
        elif self.code == ServiceStatus.INACTIVE:
            return "inactive"
        elif self.code == ServiceStatus.FAILED:
            return "failed"
        elif self.code == ServiceStatus.NOT_FOUND:
            return "not found"
        elif self.code == ServiceStatus.UNSTABLE:
            return "unstable"
        else:
            return "unknown"

    def __int__(self):
        return self.code

    rSince = re.compile(r'since [A-Za-z]+ ([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2}) ([\+-][0-9]+);')

    rPID = re.compile(r' PID: +([0-9]+) +')

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
        status = ServiceStatus(ServiceStatus.UNKNOWN)
        startTime = None
        mainPid = None
        if rc == 0:
            for line in stdout_list:
                if 'Active: active ' in line:
                    status = ServiceStatus(ServiceStatus.ACTIVE)
                    startTime = ServiceStatus.parse_datetime(line)
                elif 'Main PID: ' in line:
                    mainPid = ServiceStatus.parse_pid(line)
        else:
            for line in stdout_list:
                if 'Active: failed ' in line:
                    status = ServiceStatus(ServiceStatus.FAILED)
                    startTime = ServiceStatus.parse_datetime(line)
                elif 'Active: inactive ' in line:
                    status = ServiceStatus(ServiceStatus.INACTIVE)
                    startTime = ServiceStatus.parse_datetime(line)

            for line in stderr_list:
                if 'service could not be found' in line:
                    status = ServiceStatus(ServiceStatus.NOT_FOUND)

        return status, startTime, mainPid

class Service:
    def __init__(self, service, config):
        self.service = service
        self.config = config
        self.status = None
        self.changeTime = None
        self.flapCount = 0
        self.flapStartTime = None

