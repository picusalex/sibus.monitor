#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import sys
import time

from sqlalchemy import Column, Integer, String, Float, desc, or_

from sibus_lib import BusElement, MessageObject
from sibus_lib import CoreDBBase, CoreDatabase
from sibus_lib import mylogger
from sibus_lib.utils import float_to_datetime, datetime_now_float

SERVICE_NAME = "bus.monitor"
logger = mylogger(SERVICE_NAME)

class BusElementDB(CoreDBBase):
    __tablename__ = 'current_bus_elements'
    id = Column(Integer, primary_key=True)
    bus_uid = Column(String(36))
    bus_origin_host = Column(String(50))
    bus_origin_service = Column(String(50))
    status = Column(String(20))
    first_event_date = Column(Float(precision=32))
    last_event_date = Column(Float(precision=32))

database = CoreDatabase()

def check_dead():
    session = database.get_session()
    for bus_elem in session.query(BusElementDB).order_by(desc(BusElementDB.last_event_date)):

        dtmp = datetime_now_float()
        if (dtmp - bus_elem.last_event_date > 60) and (bus_elem.status <> "dead") and (bus_elem.status <> "terminated"):
            bus_elem.status = "dead"
            session.add(bus_elem)
        elif (dtmp - bus_elem.last_event_date > 60*5) and (bus_elem.status <> "terminated"):
            bus_elem.status = "terminated"
            session.add(bus_elem)

    session.commit()

def publish_status():
    session = database.get_session()

    check_dead()

    status = {
        "elements_alive" : 0,
        "elements_list" : []
    }
    for bus_elem in session.query(BusElementDB).filter(or_(BusElementDB.status == 'alive', BusElementDB.status == 'dead')).order_by(desc(BusElementDB.last_event_date)):

        tmp = {
            "bus_origin_host": bus_elem.bus_origin_host,
            "bus_origin_service": bus_elem.bus_origin_service,
            "status": bus_elem.status,
            "started_since": float_to_datetime(bus_elem.first_event_date).isoformat(),
            "last_event": float_to_datetime(bus_elem.last_event_date).isoformat()
        }
        status["elements_list"].append(tmp)
        if bus_elem.status == "alive":
            status["elements_alive"] += 1

    message = MessageObject(data=status, topic="admin.bus.status")
    logger.info("Bus Monitoring status: %s" % str(message.get_data()))
    monitor_busclient.publish(message)


def on_busmessage(message):
    session = database.get_session()

    bus_elem = session.query(BusElementDB).filter_by(bus_uid=message.origin_uid).one_or_none()

    if bus_elem is None:
        bus_elem = BusElementDB(bus_uid=message.origin_uid,
                                bus_origin_host=message.origin_host,
                                bus_origin_service=message.origin_service,
                                status="alive",
                                first_event_date=message.date_creation,
                                last_event_date=message.date_creation)
    bus_elem = None

    if message.topic == "admin.terminated":
        bus_elem.status = "terminated"
    else:
        bus_elem.status = "alive"
    bus_elem.last_event_date = message.date_creation

    session.add(bus_elem)
    session.commit()

    if message.topic == "admin.start" or message.topic == "admin.terminated":
        publish_status()
    elif message.topic == "request.bus.status":
        publish_status()


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

