from tango import AttrWriteType, DevState, DevFloat, EncodedAttribute
from tango.server import Device, attribute, command, pipe
from slsdet import Moench, runStatus, timingMode, detectorSettings
from _slsdet import IpAddr
import subprocess
import time
import os
import re
import signal
from pathlib import PosixPath


class MoenchDetector(Device):
    polling = 1000
    exposure = attribute(
        label="exposure",
        dtype="float",
        unit="s",
        min_value=0.0,
        max_value=1e2,
        min_warning=1e-6,  # check the smallest exposure when packetloss occurs
        max_warning=0.7e2,  # check too long exposures
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        polling_period=polling,
        doc="single frame exposure time",
    )
    timing_mode = attribute(
        label="trigger mode",
        dtype="str",
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        doc="AUTO - internal trigger, EXT - external]",
    )  # see property timing in pydetector docs
    triggers = attribute(
        label="triggers", dtype="int", doc="number of triggers for an acquire session"
    )
    filename = attribute(
        label="filename",
        dtype="str",
        doc="File name: [filename]_d0_f[sub_file_index]_[acquisition/file_index].raw",
    )
    filepath = attribute(
        label="filepath", dtype="str", doc="dir where data files will be written"
    )
    frames = attribute(
        label="number of frames",
        dtype="int",
        doc="amount of frames made per acquisition",
    )
    filewrite = attribute(label="enable or disable file writing", dtype="bool")
    highvoltage = attribute(
        label="high voltage on sensor",
        dtype="int",
        unit="V",
        min_value=60,
        max_value=200,
        min_warning=70,
        max_warning=170,
    )
    period = attribute(
        label="period", unit="s", dtype="float", doc="period between acquisitions"
    )
    samples = attribute(label="samples amount", dtype="int", doc="in analog mode only")
    settings = attribute(
        label="gain settings",
        dtype="str",
        doc="[G1_HIGHGAIN, G1_LOWGAIN, G2_HIGHCAP_HIGHGAIN, G2_HIGHCAP_LOWGAIN, G2_LOWCAP_HIGHGAIN, G2_LOWCAP_LOWGAIN, G4_HIGHGAIN, G4_LOWGAIN]",
    )  # converted from enums
    zmqip = attribute(
        label="zmq ip address",
        dtype="str",
        doc="ip to listen to zmq data streamed out from receiver or intermediate process",
    )
    zmqport = attribute(
        label="zmq port", dtype="str", doc="port number to listen to zmq data"
    )  # can be either a single int or list (or tuple) of ints
    rx_discardpolicy = attribute(
        label="discard policy",
        dtype="str",
        doc="discard policy of corrupted frames [NO_DISCARD/DISCARD_EMPTY/DISCARD_PARTIAL]",
    )  # converted from enums
    rx_missingpackets = attribute(
        label="missed packets",
        dtype="int",
        doc="number of missing packets for each port in receiver",
    )  # need to be checked, here should be a list of ints
    rx_hostname = attribute(
        label="receiver hostname", dtype="str", doc="receiver hostname or IP address"
    )
    rx_tcpport = attribute(
        label="tcp rx_port",
        dtype="int",
        doc="port for for client-receiver communication via TCP",
    )
    rx_status = attribute(label="receiver status", dtype="str")
    rx_zmqstream = attribute(
        label="data streaming via zmq",
        dtype="bool",
        doc="enable/disable streaming via zmq",
    )  # will be further required for preview direct from stream
    rx_version = attribute(
        label="rec. version",
        dtype="str",
        doc="version of receiver formatatted as [0xYYMMDD]",
    )

    firmware_version = attribute(
        label="det. version", dtype="str", doc="version of detector software"
    )

    def init_pc(self):
        SLS_RECEIVER_PORT = "1954"
        PROCESSING_RX_IP_PORT = "192.168.2.200 50003"
        PROCESSING_TX_IP_PORT = "192.168.1.200 50001"
        PROCESSING_CORES = "20"
        CONFIG_PATH = (
            "/home/moench/detector/moench_2021_virtual.config"  # for virtual detector
        )
        # CONFIG_PATH = "/home/moench/detector/moench_2021.config" #for real detector
        # configured for moench pc only
        self.slsDetectorProc = subprocess.Popen(
            "exec slsReceiver -t {}".format(SLS_RECEIVER_PORT),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )
        self.zmqDataProc = subprocess.Popen(
            "exec moench04ZmqProcess {} {} {}".format(
                PROCESSING_RX_IP_PORT, PROCESSING_TX_IP_PORT, PROCESSING_CORES
            ),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )
        self.put_config = subprocess.Popen(
            "exec sls_detector_put config {}".format(CONFIG_PATH),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        sls_running = self.slsDetectorProc.poll() == None
        zmq_running = self.zmqDataProc.poll() == None
        self.info_stream("Both processses are running")
        return sls_running & zmq_running

    def init_device(self):
        Device.init_device(self)
        self.set_state(DevState.INIT)
        if not self.init_pc():
            self.set_state(DevState.FAULT)
            self.info_stream(
                "Unable to start slsReceiver or zmq socket. Check firewall process and already running instances."
            )
        time.sleep(1)
        self.device = Moench()
        try:
            st = self.device.status
            self.info_stream("Current device status: %s" % st)
        except RuntimeError as e:
            self.set_state(DevState.FAULT)
            self.info_stream("Unable to establish connection with detector\n%s" % e)
            self.delete_device()

    def read_exposure(self):
        return self.device.exptime

    def write_exposure(self, value):
        self.device.exptime = value

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
        return self.device.filename

    def write_filename(self, value):
        self.device.filename = value

    def read_filepath(self):
        return str(self.device.fpath)

    def write_filepath(self, value):
        try:
            self.device.fpath = PosixPath(value)
        except TypeError:
            self.error_stream("not valid filepath")

    def read_frames(self):
        return self.device.frames

    def write_frames(self, value):
        self.device.frames = value

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
        pass

    def write_rx_discardpolicy(self, value):
        pass

    def read_rx_missingpackets(self):
        pass

    def write_rx_missingpackets(self, value):
        pass

    def read_rx_hostname(self):
        pass

    def write_rx_hostname(self, value):
        pass

    def read_rx_tcpport(self):
        pass

    def write_rx_tcpport(self, value):
        pass

    def read_rx_status(self):
        pass

    def write_rx_status(self, value):
        pass

    def read_rx_zmqstream(self):
        pass

    def write_rx_zmqstream(self, value):
        pass

    def read_rx_version(self):
        pass

    def write_rx_version(self, value):
        pass

    def read_firmware_version(self):
        pass

    def write_firmware_version(self, value):
        pass

    @command
    def delete_device(self):
        try:
            self.slsDetectorProc.kill()
            self.zmqDataProc.kill()
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
    MoenchDetector.run_server()
