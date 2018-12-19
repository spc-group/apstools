#1/usr/bin/env python

"""
record a snapshot of some PVs using Bluesky, ophyd, and databroker
"""


import os
from ophyd import EpicsSignal
from databroker import Broker
from bluesky import RunEngine
from bluesky import (
    plans as bp, 
    plan_patterns as bpp, 
    plan_stubs as bps, 
    plan_tools as bpt)
import time
from collections import OrderedDict
import pyRestTable
import datetime


def connect_pvlist(pvlist):
    obj_dict = OrderedDict()
    for item in pvlist:
        if len(item.strip()) == 0:
            continue
        pvname = item.strip()
        oname = "signal_{}".format(len(obj_dict))
        obj = EpicsSignal(pvname, name=oname)
        obj_dict[oname] = obj
    return obj_dict


def print_signals_in_table(obj_dict):
    t = pyRestTable.Table()
    t.addLabel("EPICS PV")
    t.addLabel("value")
    t.addLabel("timestamp")
    for oname, obj in obj_dict.items():
        r = obj.read()
        ts = r[oname]["timestamp"]
        value = r[oname]["value"]
        dt = datetime.datetime.fromtimestamp(ts).isoformat().replace("T", " ")
        row = [obj.pvname, value, dt]
        # print(obj.pvname, r[oname])
        t.addRow(row)
    print(t)


def snapshot(obj_list, stream="primary", md=None):
    """
    bluesky plan: record current value of list of ophyd signals
    """
    # we want this metadata to appear
    _md = dict(
        plan_name = "snapshot",
        plan_description = "archive snapshot of ophyd Signals (usually EPICS PVs)",
        iso8601 = str(datetime.datetime.now()),     # human-readable
        hints = {},
        )
    # caller may have given us additional metadata
    _md.update(md or {})

    def _snap(md=None):
        yield from bps.open_run(md)
        yield from bps.create(name=stream)
        for obj in obj_list:
            # passive observation: DO NOT TRIGGER, only read
            yield from bps.read(obj)
        yield from bps.save()
        yield from bps.close_run()

    return (yield from _snap(md=_md))


def callback(key, doc):
    print(key)
    for k, v in doc.items():
        print(f"\t{k}\t{v}")


def snapshot_cli():
    with open("pvlist.txt", "r") as f:
        pvlist = f.read().strip().splitlines()
    
    obj_dict = connect_pvlist(pvlist)
    time.sleep(2)   # FIXME: allow time to connect
    #print_signals_in_table(obj_dict)
    
    RE = RunEngine({})
    RE(snapshot(obj_dict.values()), callback)
    
    db = Broker.named("mongodb_config")
    RE.subscribe(db.insert)
    RE(snapshot(obj_dict.values()))
    
    h = db[-1]
    print(h.start)
    print(h.table())


if __name__ == "__main__":
    snapshot_cli()
