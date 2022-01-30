from tango import AttrWriteType, DevState
from tango.server import Device, attribute, command, pipe, device_property
from slsdet import Moench, runStatus, timingMode, detectorSettings, frameDiscardPolicy
from _slsdet import IpAddr
import time
import os, sys
import re
from computer_setup import ComputerSetup
import computer_setup
from pathlib import PosixPath

# TODO: FISALLOWED TO ALL ATTRIBUTES
class MoenchDetectorControl(Device):
    _tiff_fullpath_last = ""

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
    PROCESSING_CORES = device_property(
        dtype="str",
        doc="number of cores for zmq on-time processing",
        default_value="20",
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
    exposure = attribute(
        label="exposure",
        dtype="float",
        unit="s",
        format="%2.3e",
        min_value=0.0,
        max_value=1e2,
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        fisallowed="isWriteAvailable",
        doc="single frame exposure time",
    )
    timing_mode = attribute(
        label="trigger mode",
        dtype="str",
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        fisallowed="isWriteAvailable",
        doc="AUTO - internal trigger, EXT - external]",
    )
    triggers = attribute(
        label="triggers",
        dtype="int",
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        fisallowed="isWriteAvailable",
        doc="number of triggers for an acquire session",
    )
    filename = attribute(
        label="filename",
        dtype="str",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        memorized=True,
        hw_memorized=True,
        doc="File name: [filename]_d0_f[sub_file_index]_[acquisition/file_index].raw",
    )
    filepath = attribute(
        label="filepath",
        dtype="str",
        fisallowed="isWriteAvailable",
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        doc="dir where data files will be written",
    )
    fileindex = attribute(
        label="file_index",
        dtype="int",
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        fisallowed="isWriteAvailable",
        doc="File name: [filename]_d0_f[sub_file_index]_[acquisition/file_index].raw",
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
    framemode = attribute(
        label="frameMode",
        dtype="str",
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        fisallowed="isWriteAvailable",
        doc="framemode of detector [frame, pedestal, newPedestal]",
    )
    detectormode = attribute(
        label="detectorMode",
        dtype="str",
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        fisallowed="isWriteAvailable",
        doc="detectorMode [counting, analog, interpolating]",
    )
    filewrite = attribute(
        label="enable or disable file writing",
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        fisallowed="isWriteAvailable",
        doc="turn of/off writing file to disk",
    )
    highvoltage = attribute(
        label="high voltage on sensor",
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
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        fisallowed="isWriteAvailable",
        doc="period between acquisitions",
    )
    samples = attribute(
        label="samples amount",
        dtype="int",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        doc="in analog mode only",
    )
    settings = attribute(
        label="gain settings",
        dtype="str",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        memorized=True,
        hw_memorized=True,
        doc="[G1_HIGHGAIN, G1_LOWGAIN, G2_HIGHCAP_HIGHGAIN, G2_HIGHCAP_LOWGAIN, G2_LOWCAP_HIGHGAIN, G2_LOWCAP_LOWGAIN, G4_HIGHGAIN, G4_LOWGAIN]",
    )  # converted from enums
    zmqip = attribute(
        label="zmq ip address",
        dtype="str",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        doc="ip to listen to zmq data streamed out from receiver or intermediate process",
    )
    zmqport = attribute(
        label="zmq port",
        dtype="int",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        doc="port number to listen to zmq data",
    )  # can be either a single int or list (or tuple) of ints
    rx_discardpolicy = attribute(
        label="discard policy",
        dtype="str",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        doc="discard policy of corrupted frames [NO_DISCARD/DISCARD_EMPTY_FRAMES/DISCARD_PARTIAL_FRAMES]",
    )  # converted from enums
    rx_missingpackets = attribute(
        label="missed packets",
        dtype="int",
        access=AttrWriteType.READ,
        fisallowed="isWriteAvailable",
        doc="number of missing packets for each port in receiver",
    )  # need to be checked, here should be a list of ints
    rx_hostname = attribute(
        label="receiver hostname",
        dtype="str",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        doc="receiver hostname or IP address",
    )
    rx_tcpport = attribute(
        label="tcp rx_port",
        dtype="int",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        doc="port for for client-receiver communication via TCP",
    )
    rx_status = attribute(
        label="receiver rx/tx status",
        dtype="str",
        access=AttrWriteType.READ,
        fisallowed="isWriteAvailable",
    )
    rx_zmqstream = attribute(
        label="data streaming via zmq",
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
        fisallowed="isWriteAvailable",
        doc="enable/disable streaming via zmq",
    )  # will be further required for preview direct from stream
    rx_version = attribute(
        label="rec. version",
        dtype="str",
        access=AttrWriteType.READ,
        fisallowed="isWriteAvailable",
        doc="version of receiver formatatted as [0xYYMMDD]",
    )

    firmware_version = attribute(
        label="det. version",
        dtype="str",
        access=AttrWriteType.READ,
        fisallowed="isWriteAvailable",
        doc="version of detector software",
    )
    detector_status = attribute(
        label="detector status",
        dtype="DevState",
        access=AttrWriteType.READ,
        doc="status of detector",
    )
    tiff_fullpath_next = attribute(
        label="next capture path",
        dtype="str",
        access=AttrWriteType.READ,
        fisallowed="isWriteAvailable",
        doc="full path of the next capture",
    )
    tiff_fullpath_last = attribute(
        label="last capture path",
        dtype="str",
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        doc="full path of the last capture",
    )
    tiff_fullpath_last_formatted = attribute(
        label="path for lavue",
        dtype="str",
        access=AttrWriteType.READ,
        doc="full path of the last capture with file:",
    )

    def init_device(self):
        Device.init_device(self)
        self.set_state(DevState.INIT)
        self.get_device_properties(self.get_device_class())
        MAX_ATTEMPTS = 5
        self.attempts_counter = 0
        self.pc_util = ComputerSetup()
        self.VIRTUAL = (
            True if "--virtual" in sys.argv else False
        )  # check whether server started with "--virtual" flag
        self.pc_util.init_pc(
            virtual=self.VIRTUAL,
            SLS_RECEIVER_PORT=self.SLS_RECEIVER_PORT,
            PROCESSING_RX_IP=self.PROCESSING_RX_IP,
            PROCESSING_RX_PORT=self.PROCESSING_RX_PORT,
            PROCESSING_TX_IP=self.PROCESSING_TX_IP,
            PROCESSING_TX_PORT=self.PROCESSING_TX_PORT,
            PROCESSING_CORES=self.PROCESSING_CORES,
            CONFIG_PATH_REAL=self.CONFIG_PATH_REAL,
            CONFIG_PATH_VIRTUAL=self.CONFIG_PATH_VIRTUAL,
        )
        while not computer_setup.is_pc_ready() and self.attempts_counter < MAX_ATTEMPTS:
            time.sleep(0.5)
            self.attempts_counter += 1
        if not computer_setup.is_pc_ready:
            self.delete_device()
            self.info_stream("Unable to start PC")
        self.info_stream("PC is ready")
        self.device = Moench()
        try:
            st = self.device.rx_status
            self.info_stream("Current device status: %s" % st)
            self.set_state(DevState.ON)
        except RuntimeError as e:
            self.set_state(DevState.FAULT)
            self.info_stream("Unable to establish connection with detector\n%s" % e)
            self.delete_device()

    def isWriteAvailable(self, value):
        # slsdet.runStatus.IDLE, ERROR, WAITING, RUN_FINISHED, TRANSMITTING, RUNNING, STOPPED
        if self.device.status in (runStatus.IDLE, runStatus.WAITING, runStatus.STOPPED):
            return True
        return False

    def read_exposure(self):
        return self.device.exptime

    def write_exposure(self, value):
        self.device.exptime = value

    def read_fileindex(self):
        return self.device.findex

    def write_fileindex(self, value):
        self.device.findex = value

    def read_timing_mode(self):
        if self.device.timing == timingMode.AUTO_TIMING:
            return "AUTO"
        elif self.device.timing == timingMode.TRIGGER_EXPOSURE:
            return "EXT"
        else:
            self.info_stream("The timing mode is not assigned correctly.")

    def write_timing_mode(self, value):
        if type(value) == str:
            if value.lower() == "auto":
                self.info_stream("Setting auto timing mode")
                self.device.timing = timingMode.AUTO_TIMING
            elif value.lower() == "ext":
                self.info_stream("Setting external timing mode")
                self.device.timing = timingMode.TRIGGER_EXPOSURE
        else:
            self.info_stream('Timing mode should be "AUTO/EXT" string')

    def read_triggers(self):
        return self.device.triggers

    def write_triggers(self, value):
        self.device.triggers = value

    def read_filename(self):
        return self.device.fname

    def write_filename(self, value):
        self.device.fname = value

    def read_filepath(self):
        return str(self.device.fpath)

    def write_filepath(self, value):
        try:
            self.device.fpath = value
        except:
            self.error_stream("not valid filepath")

    def read_frames(self):
        return self.device.frames

    def write_frames(self, value):
        self.device.frames = value

    def read_framemode(self):
        try:
            framemode = self.device.rx_jsonpara["frameMode"]
        except:
            framemode = ""
            self.error_stream("no framemode set")
        return framemode

    def write_framemode(self, value):
        if type(value) == str:
            if value in ("frame", "pedestal", "newPedestal"):
                self.device.rx_jsonpara["frameMode"] = value
            else:
                self.error_stream("not allowed framemode")
        else:
            self.error_stream("value must be string")

    def read_detectormode(self):
        try:
            detectormode = self.device.rx_jsonpara["detectorMode"]
        except:
            detectormode = ""
            self.error_stream("no detectormode set")
        return detectormode

    def write_detectormode(self, value):
        if type(value) == str:
            if value in ("counting", "analog", "interpolating"):
                self.device.rx_jsonpara["detectorMode"] = value
            else:
                self.error_stream("not allowed framemode")
        else:
            self.error_stream("value must be string")

    def read_filewrite(self):
        return self.device.fwrite

    def write_filewrite(self, value):
        self.device.fwrite = value

    def read_highvoltage(self):
        return self.device.highvoltage

    def write_highvoltage(self, value):
        try:
            self.device.highvoltage = value
        except RuntimeError:
            self.error_stream("not allowed highvoltage")

    def read_period(self):
        return self.device.period

    def write_period(self, value):
        self.device.period = value

    def read_samples(self):
        return self.device.samples

    def write_samples(self, value):
        self.device.samples = value

    def read_settings(self):
        return str(self.device.settings)

    def write_settings(self, value):
        settings_dict = {
            "G1_HIGHGAIN": 13,
            "G1_LOWGAIN": 14,
            "G2_HIGHCAP_HIGHGAIN": 15,
            "G2_HIGHCAP_LOWGAIN": 16,
            "G2_LOWCAP_HIGHGAIN": 17,
            "G2_LOWCAP_LOWGAIN": 18,
            "G4_HIGHGAIN": 19,
            "G4_LOWGAIN": 20,
        }
        if value in list(settings_dict.keys()):
            self.device.settings = detectorSettings(settings_dict[value])

    def read_zmqip(self):
        return str(self.device.rx_zmqip)

    def write_zmqip(self, value):
        if bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", value)):
            self.device.rx_zmqip = IpAddr(value)
        else:
            self.error_stream("not valid ip address")

    def read_zmqport(self):
        return self.device.rx_zmqport

    def write_zmqport(self, value):
        self.device.rx_zmqport = value

    def read_rx_discardpolicy(self):
        return str(self.device.rx_discardpolicy)

    def write_rx_discardpolicy(self, value):
        disard_dict = {
            "NO_DISCARD": 0,
            "DISCARD_EMPTY_FRAMES": 1,
            "DISCARD_PARTIAL_FRAMES": 2,
        }
        if value in list(disard_dict.keys()):
            self.device.rx_discardpolicy = frameDiscardPolicy(disard_dict[value])

    def read_rx_missingpackets(self):
        return str(self.device.rx_missingpackets)

    def write_rx_missingpackets(self, value):
        pass

    def read_rx_hostname(self):
        return self.device.rx_hostname

    def write_rx_hostname(self, value):
        self.device.rx_hostname = value

    def read_rx_tcpport(self):
        return self.device.rx_tcpport

    def write_rx_tcpport(self, value):
        self.device.rx_tcpport = value

    def read_rx_status(self):
        return str(self.device.rx_status)

    def write_rx_status(self, value):
        pass

    def read_rx_zmqstream(self):
        return self.device.rx_zmqstream

    def write_rx_zmqstream(self, value):
        self.device.rx_zmqstream = value

    def read_rx_version(self):
        return self.device.rx_version

    def write_rx_version(self, value):
        pass

    def read_firmware_version(self):
        return self.device.firmwareversion

    def write_firmware_version(self, value):
        pass

    def read_tiff_fullpath_next(self):
        # [filename]_d0_f[sub_file_index]_[acquisition/file_index].raw"
        filename = self.read_filename()
        file_index = self.read_fileindex()
        savepath = self.read_filepath()
        fullpath = os.path.join(savepath, f"{filename}_{file_index}.tiff")
        return fullpath

    def write_tiff_fullpath_next(self, value):
        pass

    def read_tiff_fullpath_last(self):
        return self._tiff_fullpath_last

    def write_tiff_fullpath_last(self, value):
        self._tiff_fullpath_last = value

    def read_tiff_fullpath_last_formatted(self):
        return "file:" + self._tiff_fullpath_last

    def write_tiff_fullpath_last_formatted(self, value):
        pass

    # TODO: rewrite
    # slsdet.runStatus.IDLE, ERROR, WAITING, RUN_FINISHED, TRANSMITTING, RUNNING, STOPPED
    #  using DevState
    # static DevState	ALARM
    # static DevState	CLOSE
    # static DevState	DISABLE
    # static DevState	EXTRACT
    # static DevState	FAULT
    # static DevState	INIT
    # static DevState	INSERT
    # static DevState	MOVING
    # static DevState	OFF
    # static DevState	ON
    # static DevState	OPEN
    # static DevState	RUNNING
    # static DevState	STANDBY
    # static DevState	UNKNOWN

    def read_detector_status(self):
        # TODO: check behavior and statuses' identities
        statuses = {
            runStatus.IDLE: DevState.ON,
            runStatus.ERROR: DevState.FAULT,
            runStatus.WAITING: DevState.STANDBY,
            runStatus.RUN_FINISHED: DevState.ON,
            runStatus.TRANSMITTING: DevState.RUNNING,
            runStatus.RUNNING: DevState.RUNNING,
            runStatus.STOPPED: DevState.ON,
        }
        det_status_devstate = statuses.get(self.device.status)
        if det_status_devstate == None:
            return DevState.UNKNOWN
        else:
            return det_status_devstate

    def write_detector_status(self):
        pass

    @command
    def delete_device(self):
        try:
            self.pc_util.deactivate_pc(self.VIRTUAL)
            self.info_stream("SlsReceiver or zmq socket processes were killed.")
        except Exception:
            self.info_stream(
                "Unable to kill slsReceiver or zmq socket. Please kill it manually."
            )

    @command
    def start(self):
        self.device.start()

    @command
    def rx_start(self):
        self.device.rx_start()

    @command
    def rx_stop(self):
        self.device.rx_stop()


if __name__ == "__main__":
    MoenchDetectorControl.run_server()
