#!/usr/bin/python

import sys
import argparse
import yaml
import logging

from service import ServiceStatus, ServiceMon
from carbon_c_relay import CarbonCRelayMon


def parseArgs():
    parser = argparse.ArgumentParser(
        description='Monitor graphite relay processes and run reconfigure task on failure/recovery')
    parser.add_argument("--config", help='config', default="/etc/relaymon.yml")
    return parser.parse_args()


def parseLogLevel(s):
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
    try:

        #FORMAT = '%(asctime)-15s %(message)s'
        FORMAT = "%(asctime)s '%(name)s' %(levelname)s: %(message)s"
        logging.basicConfig(format=FORMAT)

        args = parseArgs()
        # print(args)

        with open(args.config, 'r') as ymlfile:
            cfg = yaml.load(ymlfile)

        logger = logging.getLogger('relaymon')
        logger.setLevel(parseLogLevel(cfg.get('log_level')))

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

    try:
        # print(cfg)

        services = []

        for s in cfg['services']:
            service = None
            type = s.get('type')
            if type is None:
                type = s['name']
            if type == "carbon-c-relay":
                service = CarbonCRelayMon(s['name'], s.get('config'))
            else:
                service = ServiceMon(s['name'], s.get('config'))

            services.append(service)
    except Exception as e:
        logger.error("parse config: %s" % str(e))
        sys.exit(0)

    error = False
    for s in services:
        status, startTime = s.getStatus()
        #print("%s '%s' %s" % (s.service, status, startTime))
        if status.code == ServiceStatus.NOT_FOUND:
            logger.error("service not found: %s" % s.service)
            error = True

    if error:
        sys.exit(0)


if __name__ == "__main__":
    main()
