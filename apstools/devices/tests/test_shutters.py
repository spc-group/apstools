"""
Test the shutter classes.
"""

import pytest
from ophyd import Component
from ophyd import EpicsSignal

from ...tests import IOC
from ...tests import timed_pause
from .. import shutters

PV_BIT = f"{IOC}gp:bit20"
PV_MOTOR = f"{IOC}m16"


def set_and_assert_signal(signal, value):
    if signal.get() != value:
        signal.put(value)
        timed_pause()
    assert signal.get() == value


def operate_shutter(shutter):
    shutter.open()
    timed_pause()
    assert shutter.state == "open"
    assert shutter.isOpen
    assert not shutter.isClosed

    shutter.close()
    timed_pause()
    assert shutter.state == "close"
    assert not shutter.isOpen
    assert shutter.isClosed


@pytest.mark.parametrize(
    "close_pv, open_pv",
    [
        [None, None],
        ["alternative:close", None],
        ["alternative:close_epics", None],
        ["alternative:aaa", None],
        [None, "alternative:open"],
        [None, "alternative:open_epics"],
        [None, "alternative:bbb"],
        ["second:aaa", "third:bbb"],
    ],
)
def test_ApsPssShutter(close_pv, open_pv):
    """
    Structure tests only.

    Cannot connect or operate! We don't have the APS when testing!
    """
    prefix = "TEST:"
    shutter = shutters.ApsPssShutter(prefix, name="shutter", close_pv=close_pv, open_pv=open_pv)
    close_pv = close_pv or f"{prefix}Close"
    open_pv = open_pv or f"{prefix}Open"
    assert shutter.open_signal.pvname == open_pv
    assert shutter.close_signal.pvname == close_pv


@pytest.mark.parametrize(
    "state_pv, close_pv, open_pv",
    [
        [None, None, None],
        ["the:state:pv", None, None],
        ["the:state:EPICS_PV", "a:close:pv", "that:open:pvname"],
    ],
)
def test_ApsPssShutterWithStatus(state_pv, close_pv, open_pv):
    """
    Structure tests only.

    Cannot connect or operate! We don't have the APS when testing!
    """
    prefix = "TEST:"
    shutter = shutters.ApsPssShutterWithStatus(
        prefix, state_pv, name="shutter", close_pv=close_pv, open_pv=open_pv
    )
    # state_pv = state_pv or f"{prefix}Close"
    assert shutter.pss_state.pvname == str(state_pv)


def test_EpicsMotorShutter():
    shutter = shutters.EpicsMotorShutter(PV_MOTOR, name="shutter")
    shutter.wait_for_connection()
    shutter.close_value = 1.0  # default
    shutter.open_value = 0.0  # default
    shutter.tolerance = 0.01  # default

    # put the shutter into known state
    set_and_assert_signal(shutter.signal.user_setpoint, shutter.close_value)
    operate_shutter(shutter)


def test_EpicsOnOffShutter():
    shutter = shutters.EpicsOnOffShutter(PV_BIT, name="shutter")
    shutter.close_value = 0  # default
    shutter.open_value = 1  # default

    # put the shutter into known state
    set_and_assert_signal(shutter.signal, shutter.close_value)
    operate_shutter(shutter)


def test_OneEpicsSignalShutter():
    class OneEpicsSignalShutter(shutters.OneSignalShutter):
        signal = Component(EpicsSignal, "")

    shutter = OneEpicsSignalShutter(PV_BIT, name="shutter")
    shutter.wait_for_connection()
    assert shutter.connected

    # put the shutter into known state
    set_and_assert_signal(shutter.signal, shutter.close_value)
    operate_shutter(shutter)


def test_OneSignalShutter():
    shutter = shutters.OneSignalShutter(name="shutter")
    operate_shutter(shutter)


def test_SimulatedApsPssShutterWithStatus():
    shutter = shutters.SimulatedApsPssShutterWithStatus(name="shutter")
    operate_shutter(shutter)
