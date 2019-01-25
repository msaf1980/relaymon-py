#!/usr/bin/python

import sys
import argparse
import yaml
import logging
import time
import subprocess

from . import version
from .service import ServiceStatus, Service
from .carbon_c_relay import CarbonCRelay

def GetExceptionLoc():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    return (filename, lineno)

def parseArgs():
    parser = argparse.ArgumentParser(
        description='Monitor graphite relay processes and run reconfigure task on failure/recovery')
    parser.add_argument("--config", help='config', default="/etc/relaymon.yml")
    parser.add_argument("--debug", help='debug', default=False, action='store_true')
    parser.add_argument("--version", help='version', default=False, action='store_true')
    return parser.parse_args()

def parseLogLevel(s, debug):
    if debug:
        return logging.DEBUG
    if s is None:
        return logging.INFO
    l = s.lower()
    if l == "info":
        return logging.INFO
    elif l == "critical":
        return logging.CRITICAL
    elif l == "error":
        return logging.ERROR
    elif l == "warning":
        return logging.WARNING
    elif l == "debug":
        return logging.DEBUG
    else:
        raise ValueError("invalid log_level %s" % s)

def main():
    logger = None
    recovery_cmd = None
    error_cmd = None
    recovery_interval = 0
    relay = None

    name = "relaymon"
    args = parseArgs()
    if args.version:
        print("%s %s" % (name, version.version))
        sys.exit(0)

    try:
        FORMAT = "%(asctime)s '%(name)s' %(levelname)s: %(message)s"
        logging.basicConfig(format=FORMAT)

        with open(args.config, 'r') as ymlfile:
            cfg = yaml.load(ymlfile)

        logger = logging.getLogger(name)
        logger.setLevel(parseLogLevel(cfg.get('log_level'), args.debug))

        logfile = cfg.get('log_file')
        if logfile:
            # Add file handler
            fh = logging.FileHandler(logfile)
            formatter = logging.Formatter(FORMAT)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

            # Disable logging to stdout
            logger.propagate = False
    except Exception as e:
        sys.stderr.write("init error: %s\n" % str(e))
        sys.exit(0)

    interval = 0
    try:
        error_cmd = cfg['error_cmd']
        recovery_cmd = cfg['recovery_cmd']
        recovery_interval = int(cfg.get('recovery_interval', '0'))

        check_interval = int(cfg.get('check_interval', '30'))
        check_count = int(cfg.get('check_count', '20'))
        fail_count = int(cfg.get('fail_count', '10'))
        reset_count = int(cfg.get('reset_count', '10'))

        net_timeout = int(cfg.get('net_timeout', '10'))

        services = []

        for s in cfg['services']:
            service = Service(s, check_count, fail_count, reset_count)
            services.append(service)
    except Exception as e:
        (filename, linenum) = GetExceptionLoc()
        logger.error("%s:%s parse config: %s" % (filename, linenum, str(e)))
        sys.exit(0)

    carbon_c_relay_conf = cfg.get('carbon_c_relay')
    if not carbon_c_relay_conf is None:
        relay = CarbonCRelay(carbon_c_relay_conf, net_timeout, check_count, fail_count, reset_count)

    error = False
    last_ok_t = None
    while True:
        error_trigger = False
        error_step = False
        for s in services:
            last_fail = s.fail
            (fail, err) = s.check_fail()
            if not err is None:
                logger.info(err)
            if fail:
                error_step = True
                if not err is None:
                    error_trigger = True

            if args.debug:
                logger.debug("service %s is %s (%s)%s" % (s.service,
                                 ServiceStatus.toStr(s.last_status()),
                                 s.start_time,
                                 (", failed state" if fail else ""))
                            )

        if not relay is None:
            current_t = int(time.time())
            # Run network check
            relay.try_connect()
            for cluster in relay.backends:
                for b in cluster.hosts:
                    if b.fail != b.prev_fail:
                        logger.info("cluster node %s %s" % (cluster.name, b))

                if cluster.fail != cluster.prev_fail:
                    logger.info("cluster %s %s" % (cluster.name, (" failed" if cluster.fail else "")))

            (fail, err) = relay.check_fail_status()
            if not err is None:
                logger.info(err)
            if fail:
                error_step = True
                if not err is None:
                    error_trigger = True

            if args.debug:
                logger.debug("relay backends %s" % ("failed" if fail else "ok"))
                #logger.debug(str(relay.fail_status) + " %d" % relay.check_count)

            sleep_t = check_interval + current_t - int(time.time())
        else:
            sleep_t = check_interval

        # Check for recovery
        if not error_trigger:
            if recovery_interval > 0 and not recovery_cmd is None:
                current_t = int(time.time())
                if error_step:
                    last_ok_t = None
                elif last_ok_t is None:
                    last_ok_t = current_t
                elif error and current_t - last_ok_t >= recovery_interval:
                    # Run recovery command
                    try:
                        proc = subprocess.Popen(recovery_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        out = proc.communicate()[0]
                        rc = proc.returncode
                        logger.info("error event (%d): %s" % (rc, out))
                    except Exception as e:
                        logger.error("recovery event: " + str(e))

                    error = False

                if not last_ok_t is None:
                    logger.debug("interval: %d (%d - %d)", current_t - last_ok_t, current_t, last_ok_t)
        elif not error:
            last_ok_t = None
            try:
                proc = subprocess.Popen(error_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out = proc.communicate()[0]
                rc = proc.returncode
                logger.info("error event (%d): %s" % (rc, out))
            except Exception as e:
                logger.error("error event: " + str(e))

            error = True

        if sleep_t > 0:
            time.sleep(sleep_t)
