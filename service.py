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


class ServiceMon:
    rSince = re.compile(r'since [A-Za-z]+ ([0-9]{4})-([0-9]{2})-([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2}) ([\+-][0-9]+);')

    @staticmethod
    def parse_datetime(s):
        match = ServiceMon.rSince.findall(s)
        try:
            dateTime = datetime.datetime(int(match[0][0]), int(match[0][1]), int(match[0][2]), hour=int(match[0][3]), minute=int(match[0][4]), second=int(match[0][5]))
            return dateTime
        except Exception as e:
            #print str(e)
            return None

    def __init__(self, service, config):
        self.service = service
        self.config = config
        self.status = None
        self.main_pid = None
        self.last_status = None
        self.startTime = None

    def getStatus(self):
        cmd = '/bin/systemctl status %s.service' % self.service
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        stdout_list = out.split('\n')
        stderr_list = err.split('\n')
        rc = proc.returncode

        #print(stdout_list)
        #print(stderr_list)
        #print(rc)
        if rc == 0:
            for line in stdout_list:
                if 'Active: active ' in line:
                    return ServiceStatus(ServiceStatus.ACTIVE), ServiceMon.parse_datetime(line)
        else:
            for line in stdout_list:
                if 'Active: failed ' in line:
                    return ServiceStatus(ServiceStatus.FAILED), ServiceMon.parse_datetime(line)
                elif 'Active: inactive ' in line:
                    return ServiceStatus(ServiceStatus.INACTIVE), ServiceMon.parse_datetime(line)

            for line in stderr_list:
                if 'service could not be found' in line:
                    return ServiceStatus(ServiceStatus.NOT_FOUND), None

            return ServiceStatus(ServiceStatus.UNKNOWN), None
