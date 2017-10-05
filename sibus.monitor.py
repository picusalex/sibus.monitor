#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import sys
import time

from sibus_lib import BusElement, MessageObject, sibus_init
from sibus_lib.utils import datetime_now_float

SERVICE_NAME = "bus.monitor"
logger, cfg_data = sibus_init(SERVICE_NAME)

BUS_ELEMENTS = {}

def check_dead():
    for host_name in BUS_ELEMENTS:
        host = BUS_ELEMENTS[host_name]
        for service_name in host:
            service = host[service_name]
            if datetime_now_float() - service["last_communication"] > 60:
                BUS_ELEMENTS[host_name][service_name]["status"] = "zombie"

            if datetime_now_float() - service["last_communication"] > 300:
                del BUS_ELEMENTS[host_name][service_name]


def on_busmessage(message):
    host = message.origin_host
    service = message.origin_service
    topic = message.topic

    if host not in BUS_ELEMENTS:
        BUS_ELEMENTS[host] = {}

    if service not in BUS_ELEMENTS[host]:
        BUS_ELEMENTS[host][service] = {
            "last_communication": None,
            "topic": None,
            "status": None
        }

    BUS_ELEMENTS[host][service]["last_communication"] = datetime_now_float()
    BUS_ELEMENTS[host][service]["topic"] = topic
    BUS_ELEMENTS[host][service]["status"] = "alive"

    check_dead();

    if topic == "admin.terminated":
        del BUS_ELEMENTS[host][service]

    if topic == "admin.request.bus.elements":
        publish_status()

    return

def publish_status():
    message = MessageObject(data=BUS_ELEMENTS, topic="admin.info.bus.elements")
    monitor_busclient.publish(message)

monitor_busclient = BusElement(SERVICE_NAME, callback=on_busmessage, ignore_my_msg=False)
monitor_busclient.register_topic("*")
monitor_busclient.start()

def sigterm_handler(_signo=0, _stack_frame=None):
    monitor_busclient.stop()
    logger.info("Program terminated correctly")
    sys.exit(_signo)

signal.signal(signal.SIGTERM, sigterm_handler)

try:
    while 1:
        publish_status()
        time.sleep(30)
except (KeyboardInterrupt):
    logger.info("Ctrl+C detected !")
except Exception as e:
    monitor_busclient.stop()
    logger.exception("Exception in program detected ! \n"+str(e))
    sys.exit(1)

sigterm_handler()

