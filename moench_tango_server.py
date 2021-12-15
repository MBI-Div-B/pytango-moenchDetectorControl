from tango import AttrWriteType, DevState, DevFloat, EncodedAttribute
from tango.server import Device, attribute, command, pipe
from slsdet import Moench, runStatus, timingMode
import subprocess
import time
import os
import signal


class MoenchDetector(Device):
    exposure = attribute(
        label="exposure [sec]",
        dtype="float",
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
        polling_period=polling,
    )
    timing_mode = attribute(
        label="trigger mode [AUTO/EXT]", dtype="str"
    )  # see property timing in pydetector docs
    triggers = attribute(label="number of triggers per aquire", dtype="int")
    filename = attribute(label="file name for output data file", dtype="str")
    filepath = attribute(label="dir where data files will be written", dtype="str")
    frames = attribute(
        label="number of frames per acquisition/per trigger", dtype="int"
    )
    filewrite = attribute(label="enable or disable file writing", dtype="bool")
    highvoltage = attribute(
        label="high voltage on sensor, from 60 up to 200 [V]", dtype="int"
    )
    exptime = attribute(label="exposure time", dtype="float")
    period = attribute(label="period between frames [sec]", dtype="float")
    samples = attribute(label="number of samples (analog only)", dtype="int")
    settings = attribute(
        label="gain settings [G1_HIGHGAIN, G1_LOWGAIN, G2_HIGHCAP_HIGHGAIN, G2_HIGHCAP_LOWGAIN, G2_LOWCAP_HIGHGAIN, G2_LOWCAP_LOWGAIN, G4_HIGHGAIN, G4_LOWGAIN]",
        dtype="str",
    )  # converted from enums
    zmqip = attribute(
        label="ip address to listen to zmq data streamed out from receiver or intermediate process",
        dtype="str",
    )
    zmqport = attribute(
        label="port number to listen to zmq data", dtype="str"
    )  # can be either a single int or list (or tuple) of ints
    rx_discardpolicy = attribute(
        label="discard policy of corrupted frames [NO_DISCARD/DISCARD_EMPTY/DISCARD_PARTIAL]",
        dtype="str",
    )  # converted from enums
    rx_missingpackets = attribute(
        "number of missing packets for each port in receiver", dtype="list<int>"
    )  # need to be checked
    rx_hostname = attribute(label="receiver hostname or IP address", dtype="str")
    rx_tcpport = attribute(
        label="TCP port for client-receiver communication", dtype="int"
    )
    rx_status = attribute(label="receiver listener status", dtype="str")
    rx_zmqstream = attribute(
        label="enable/disable data streaming from receiver via zmq", dtype="bool"
    )  # will be further required for preview direct from stream
    rx_version = attribute(label="receiver version in format [0xYYMMDD]", dtype="str")

    firmware_version = attribute(label="detector firmware version", dtype="str")

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
                "Unnable to start slsReceiver or zmq socket. Check firewall process and already running instances."
            )
        time.sleep(1)
        device = Moench()
        try:
            st = device.status
            self.info_stream("Current device status: %s" % st)
        except RuntimeError as e:
            self.set_state(DevState.FAULT)
            self.info_stream("Unnable to establish connection with detector\n%s" % e)
            self.delete_device()

    @command
    def delete_device(self):
        try:
            self.slsDetectorProc.kill()
            self.zmqDataProc.kill()
            self.info_stream("SlsReceiver or zmq socket processes were killed.")
        except Exception:
            self.info_stream(
                "Unnable to kill slsReceiver or zmq socket. Please kill it manually."
            )

    @command
    def start(self):
        device.start()

    @command
    def rx_start(self):
        device.rx_start()

    @command
    def rx_stop(self):
        device.rx_stop()


if __name__ == "__main__":
    MoenchDetector.run_server()
