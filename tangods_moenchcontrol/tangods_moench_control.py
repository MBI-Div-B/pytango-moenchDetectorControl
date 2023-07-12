from tango import (
    AttrWriteType,
    DevState,
    DispLevel,
    GreenMode,
    AttrDataFormat,
    Except,
    DeviceProxy,
)
from tango.server import Device, attribute, command, pipe, device_property
from slsdet import Moench, runStatus, timingMode, detectorSettings, frameDiscardPolicy
from _slsdet import IpAddr
import time
import re
from .computer_setup import (
    init_pc,
    kill_all_pc_processes,
    is_sls_running,
    deactivate_pc,
)
from enum import IntEnum
import asyncio
import numpy as np
from bidict import bidict
import sys
from os.path import join


class MoenchDetectorControl(Device):
    green_mode = GreenMode.Asyncio

    class TimingMode(IntEnum):
        # the values are the same as in slsdet.timingMode so no bidict table is required
        AUTO_TIMING = 0
        TRIGGER_EXPOSURE = 1

    class DetectorSettings(IntEnum):
        # [G1_HIGHGAIN, G1_LOWGAIN, G2_HIGHCAP_HIGHGAIN, G2_HIGHCAP_LOWGAIN, G2_LOWCAP_HIGHGAIN, G2_LOWCAP_LOWGAIN, G4_HIGHGAIN, G4_LOWGAIN]
        G1_HIGHGAIN = 0
        G1_LOWGAIN = 1
        G2_HIGHCAP_HIGHGAIN = 2
        G2_HIGHCAP_LOWGAIN = 3
        G2_LOWCAP_HIGHGAIN = 4
        G2_LOWCAP_LOWGAIN = 5
        G4_HIGHGAIN = 6
        G4_LOWGAIN = 7

    detectorSettings_bidict = bidict(
        {
            DetectorSettings.G1_HIGHGAIN: detectorSettings.G1_HIGHGAIN,
            DetectorSettings.G1_LOWGAIN: detectorSettings.G1_LOWGAIN,
            DetectorSettings.G2_HIGHCAP_HIGHGAIN: detectorSettings.G2_HIGHCAP_HIGHGAIN,
            DetectorSettings.G2_HIGHCAP_LOWGAIN: detectorSettings.G2_HIGHCAP_LOWGAIN,
            DetectorSettings.G2_LOWCAP_HIGHGAIN: detectorSettings.G2_LOWCAP_HIGHGAIN,
            DetectorSettings.G2_LOWCAP_LOWGAIN: detectorSettings.G2_LOWCAP_LOWGAIN,
            DetectorSettings.G4_HIGHGAIN: detectorSettings.G4_HIGHGAIN,
            DetectorSettings.G4_LOWGAIN: detectorSettings.G4_LOWGAIN,
        }
    )

    status_dict = {
        runStatus.IDLE: DevState.ON,
        runStatus.ERROR: DevState.FAULT,
        runStatus.WAITING: DevState.STANDBY,
        runStatus.RUN_FINISHED: DevState.ON,
        runStatus.TRANSMITTING: DevState.RUNNING,
        runStatus.RUNNING: DevState.RUNNING,
        runStatus.STOPPED: DevState.ON,
    }

    class FrameDiscardPolicy(IntEnum):
        # the values are the same as in slsdet.timingMode so no bidict table is required
        NO_DISCARD = 0
        DISCARD_EMPTY_FRAMES = 1
        DISCARD_PARTIAL_FRAMES = 2

    SLS_RECEIVER_PATH = device_property(
        dtype=str,
        doc="full path to slsReceiver executable",
        default_value=join(sys.prefix, "bin", "slsReceiver"),
    )
    SLS_RECEIVER_PORT = device_property(
        dtype="str",
        doc="port of the slsReceiver instance, must match the config",
        default_value="1954",
    )
    PROCESSING_RX_IP = device_property(
        dtype="str",
        doc='ip of 10gbe "PC <-> detector" lane of PC, must match the config',
        default_value="192.168.2.200",
    )
    PROCESSING_RX_PORT = device_property(
        dtype="str",
        doc='port for 10gbe "PC <-> detector" lane of PC, must match the config',
        default_value="50003",
    )
    PROCESSING_TX_IP = device_property(
        dtype="str",
        doc="ip for 1gbe lane (lab local network) of PC, must match the config",
        default_value="192.168.1.118",
    )
    PROCESSING_TX_PORT = device_property(
        dtype="str",
        doc="port for 1gbe (lab local network) lane of PC, must match the config",
        default_value="50001",
    )
    CONFIG_PATH_REAL = device_property(
        dtype="str",
        doc="path for the config file for a real detector",
        default_value="/home/moench/detector/moench_2021.config",
    )
    CONFIG_PATH_VIRTUAL = device_property(
        dtype="str",
        doc="path for the config file for a virtual detector",
        default_value="/home/moench/detector/moench_2021_virtual.config",
    )
    IS_VIRTUAL_DETECTOR = device_property(
        dtype="bool",
        doc="the flag whether a virtual detector need to be used",
        mandatory=True,
    )
    ROOT_PASSWORD = device_property(
        dtype="str",
        doc="password of specified root user. required since slsReceiver should be started with root privileges",
        mandatory=True,
    )
    VIRTUAL_DETECTOR_BIN = device_property(
        dtype="str",
        doc="path for virtualDetector executable",
        default_value="/opt/moench-slsDetectorGroup/build/bin/moenchDetectorServer_virtual",
    )
    ZMQ_SERVER_DEVICE = device_property(
        dtype=str,
        doc="TangoDS address of zmq server",
        default_value="rsxs/moenchZmqServer/bchip286",
    )

    exposure = attribute(
        label="exposure",
        dtype="float",
        unit="s",
        format="%6.2e",
        min_value=25e-9,
        max_value=1e2,
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        fisallowed="isWriteAvailable",
        doc="single frame exposure time",
    )

    delay = attribute(
        label="delay",
        dtype="float",
        unit="s",
        format="%6.2e",
        min_value=0.0,
        max_value=1e2,
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        fisallowed="isWriteAvailable",
        doc="delay after trigger signal",
    )
    timing_mode = attribute(
        label="trigger mode",
        dtype=TimingMode,
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        fisallowed="isWriteAvailable",
        doc="[AUTO_TIMING - internal trigger, TRIGGER_EXPOSURE - external]",
    )
    triggers = attribute(
        label="triggers",
        dtype="int",
        access=AttrWriteType.READ_WRITE,
        memorized=False,
        hw_memorized=False,
        fisallowed="isWriteAvailable",
        doc="number of triggers for an acquire session",
    )
    frames = attribute(
        label="number of frames",
        dtype="int",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        memorized=True,
        hw_memorized=True,
        doc="amount of frames made per acquisition",
    )
    highvoltage = attribute(
        display_level=DispLevel.EXPERT,
        label="bias voltage on sensor",
        dtype="int",
        unit="V",
        min_value=60,
        max_value=200,
        memorized=True,
        hw_memorized=True,
        fisallowed="isWriteAvailable",
        access=AttrWriteType.READ_WRITE,
    )
    period = attribute(
        label="period",
        unit="s",
        dtype="float",
        min_value=600e-6,
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        fisallowed="isWriteAvailable",
        doc="period between acquisitions",
    )
    settings = attribute(
        display_level=DispLevel.EXPERT,
        label="gain settings",
        dtype=DetectorSettings,
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        memorized=True,
        hw_memorized=True,
        doc="[G1_HIGHGAIN, G1_LOWGAIN, G2_HIGHCAP_HIGHGAIN, G2_HIGHCAP_LOWGAIN, G2_LOWCAP_HIGHGAIN, G2_LOWCAP_LOWGAIN, G4_HIGHGAIN, G4_LOWGAIN]",
    )  # converted from enums
    zmqip = attribute(
        display_level=DispLevel.EXPERT,
        label="zmq ip address",
        dtype="str",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        doc="ip to listen to zmq data streamed out from receiver or intermediate process",
    )
    zmqport = attribute(
        display_level=DispLevel.EXPERT,
        label="zmq port",
        dtype="int",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        doc="port number to listen to zmq data",
    )  # can be either a single int or list (or tuple) of ints
    rx_discardpolicy = attribute(
        display_level=DispLevel.EXPERT,
        label="discard policy",
        dtype=FrameDiscardPolicy,
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        doc="discard policy of corrupted frames [NO_DISCARD/DISCARD_EMPTY_FRAMES/DISCARD_PARTIAL_FRAMES]",
    )  # converted from enums
    rx_hostname = attribute(
        display_level=DispLevel.EXPERT,
        label="receiver hostname",
        dtype="str",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        doc="receiver hostname or IP address",
    )
    rx_tcpport = attribute(
        display_level=DispLevel.EXPERT,
        label="tcp rx_port",
        dtype="int",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        doc="port for for client-receiver communication via TCP",
    )
    rx_status = attribute(
        display_level=DispLevel.EXPERT,
        label="receiver rx/tx status",
        dtype="str",
        access=AttrWriteType.READ,
        fisallowed="isWriteAvailable",
    )
    detector_status = attribute(
        label="detector tango state",
        dtype="DevState",
        access=AttrWriteType.READ,
    )
    rx_zmqstream = attribute(
        display_level=DispLevel.EXPERT,
        label="data streaming via zmq",
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        doc="enable/disable streaming via zmq",
    )  # will be further required for preview direct from stream

    raw_detector_status = attribute(
        display_level=DispLevel.EXPERT,
        label="detector status",
        dtype="str",
        access=AttrWriteType.READ,
        doc="raw status of detector",
    )

    def init_device(self):
        Device.init_device(self)
        self.set_state(DevState.INIT)
        self.get_device_properties(self.get_device_class())
        self.zmq_tango_device = DeviceProxy(self.ZMQ_SERVER_DEVICE)
        MAX_ATTEMPTS = 5
        self.attempts_counter = 0
        kill_all_pc_processes(self.ROOT_PASSWORD)
        init_pc(
            virtual=self.IS_VIRTUAL_DETECTOR,
            SLS_RECEIVER_PATH=self.SLS_RECEIVER_PATH,
            SLS_RECEIVER_PORT=self.SLS_RECEIVER_PORT,
            VIRTUAL_DETECTOR_BIN=self.VIRTUAL_DETECTOR_BIN,
            ROOT_PASSWORD=self.ROOT_PASSWORD,
        )
        while not is_sls_running() and self.attempts_counter < MAX_ATTEMPTS:
            time.sleep(0.5)
            self.attempts_counter += 1
        if not is_sls_running():
            self.delete_device()
            self.info_stream("Unable to start PC")
        self.info_stream("PC is ready")
        self.moench_device = Moench()
        config = (
            self.CONFIG_PATH_VIRTUAL
            if self.IS_VIRTUAL_DETECTOR
            else self.CONFIG_PATH_REAL
        )
        self.moench_device.config = config
        try:
            st = self.moench_device.rx_status
            self.info_stream("Current device status: %s" % st)
            self.set_state(DevState.ON)
        except RuntimeError as e:
            self.set_state(DevState.FAULT)
            self.info_stream("Unable to establish connection with detector\n%s" % e)
            self.delete_device()
        self.function_loop = asyncio.new_event_loop()

    def isWriteAvailable(self, value):
        # slsdet.runStatus.IDLE, ERROR, WAITING, RUN_FINISHED, TRANSMITTING, RUNNING, STOPPED
        return self.moench_device.status in (
            runStatus.IDLE,
            runStatus.WAITING,
            runStatus.STOPPED,
        )

    def read_exposure(self):
        return self.moench_device.exptime

    def write_exposure(self, value):
        self.moench_device.exptime = value

    def read_delay(self):
        return self.moench_device.delay

    def write_delay(self, value):
        self.moench_device.delay = value

    def read_timing_mode(self):
        return self.TimingMode(self.moench_device.timing.value)

    def write_timing_mode(self, value):
        self.moench_device.timing = timingMode(value)

    def read_triggers(self):
        return self.moench_device.triggers

    def write_triggers(self, value):
        self.moench_device.triggers = value

    def read_filename(self):
        return self.moench_device.fname

    def read_frames(self):
        return self.moench_device.frames

    def write_frames(self, value):
        self.moench_device.frames = value

    def read_highvoltage(self):
        return self.moench_device.highvoltage

    def write_highvoltage(self, value):
        try:
            self.moench_device.highvoltage = value
        except RuntimeError:
            self.error_stream("not allowed highvoltage")

    def read_period(self):
        return self.moench_device.period

    def write_period(self, value):
        self.moench_device.period = value

    def read_settings(self):
        return self.detectorSettings_bidict.inverse[self.moench_device.settings]

    def write_settings(self, value):
        self.moench_device.settings = self.detectorSettings_bidict[
            self.DetectorSettings(value)
        ]

    def read_zmqip(self):
        return str(self.moench_device.rx_zmqip)

    def write_zmqip(self, value):
        if bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", value)):
            self.moench_device.rx_zmqip = IpAddr(value)
        else:
            self.error_stream("not valid ip address")

    def read_zmqport(self):
        return self.moench_device.rx_zmqport

    def write_zmqport(self, value):
        self.moench_device.rx_zmqport = value

    def read_rx_discardpolicy(self):
        return self.FrameDiscardPolicy(self.moench_device.rx_discardpolicy.value)

    def write_rx_discardpolicy(self, value):
        self.moench_device.rx_discardpolicy = frameDiscardPolicy(value)

    def read_rx_hostname(self):
        return self.moench_device.rx_hostname

    def write_rx_hostname(self, value):
        self.moench_device.rx_hostname = value

    def read_rx_tcpport(self):
        return self.moench_device.rx_tcpport

    def write_rx_tcpport(self, value):
        self.moench_device.rx_tcpport = value

    def read_rx_status(self):
        return str(self.moench_device.rx_status)

    def write_rx_status(self, value):
        pass

    def read_detector_status(self):
        tango_state = self.status_dict.get(self.moench_device.status)
        return tango_state

    def write_detector_status(self, value):
        pass

    def read_rx_zmqstream(self):
        return self.moench_device.rx_zmqstream

    def write_rx_zmqstream(self, value):
        self.moench_device.rx_zmqstream = value

    def read_raw_detector_status(self):
        return str(self.moench_device.status)

    def write_raw_detector_status(self):
        pass

    def delete_device(self):
        try:
            deactivate_pc(self.ROOT_PASSWORD)
            self.info_stream("slsReceiver process was killed.")
        except Exception:
            self.info_stream("Unable to kill slsReceiver. Please kill it manually.")

    def _block_acquire(self):
        self.zmq_tango_device.start_receiver()
        self.moench_device.startReceiver()
        self.info_stream("start receiver")
        self.moench_device.startDetector()
        self.info_stream("start detector")
        """
        A detector takes a while after startDetector() execution to change its state.
        So if there is no delay after startDetector() and self.get_state() check it's very probable that
        detector will be still in ON mode (even not started to acquire.)
        """
        time.sleep(0.1)
        while self.read_detector_status() != DevState.ON:
            time.sleep(0.1)
        self.moench_device.stopReceiver()
        self.zmq_tango_device.stop_receiver()
        self.info_stream("stop receiver")

    @command
    async def start_acquire(self):
        if self.moench_device.status == runStatus.IDLE:
            asyncio.set_event_loop(self.function_loop)
            self.function_loop.run_in_executor(None, self._block_acquire)
        elif self.moench_device.status == runStatus.RUNNING:
            self.info_stream("Detector is acquiring")
        else:
            self.error_stream("Unable to acquire")

    @command
    def stop_acquire(self):
        self.moench_device.stopDetector()
        self.zmq_tango_device.stop_receiver()
