import subprocess
import time
import os, socket, sys
import re
import signal
from pathlib import PosixPath


class ComputerSetup:
    def init_pc(self, virtual=False):
        SLS_RECEIVER_PORT = "1954"
        PROCESSING_RX_IP = "192.168.2.200"
        PROCESSING_RX_PORT = "50003"
        PROCESSING_TX_IP = "192.168.1.118"
        PROCESSING_TX_PORT = "50001"
        PROCESSING_CORES = "20"
        if virtual:
            CONFIG_PATH = "/home/moench/detector/moench_2021_virtual.config"  # for virtual detector
            self.start_virtual_detector = subprocess.Popen(
                "moenchDetectorServer_virtual", shell=False,
            )
            time.sleep(5)
            print("configured for virtual detector")

        else:
            CONFIG_PATH = "/home/moench/detector/moench_2021.config"  # for real (hardware) detector
            print("configured for real detector")
        # CONFIG_PATH = "/home/moench/detector/moench_2021.config" #for real detector
        # configured for moench pc only
        self.slsDetectorProc = subprocess.Popen(
            ["slsReceiver", "-t", SLS_RECEIVER_PORT], preexec_fn=os.setsid,
        )
        self.zmqDataProc = subprocess.Popen(
            [
                "moench04ZmqProcess",
                PROCESSING_RX_IP,
                PROCESSING_RX_PORT,
                PROCESSING_TX_IP,
                PROCESSING_TX_PORT,
                PROCESSING_CORES,
            ],
            preexec_fn=os.setsid,
        )
        subprocess.call(["sls_detector_put", "config", CONFIG_PATH])
        self.sls_running = self.slsDetectorProc.poll() == None
        self.zmq_running = self.zmqDataProc.poll() == None
        time.sleep(5)
        print("Both processses are running")
        if virtual:
            subprocess.call(["sls_detector_put", "config", CONFIG_PATH])
            print("Uploaded the config the 2nd time for virtual")
        print("Both processses are running")
        return self.sls_running & self.zmq_running

    def deactivate_pc(self, virtual=False):
        self.slsDetectorProc.kill()
        self.zmqDataProc.kill()
        if virtual:
            kill_processes_by_name("moenchDetectorServer_virtual")


def is_sls_running():
    return is_process_running("slsReceiver")


def is_zmq_running():
    return is_process_running("moench04ZmqProcess")


def is_pc_ready():
    if is_sls_running() and is_zmq_running():
        return True
    else:
        return False


def is_process_running(name):
    try:
        lines = os.popen("pgrep -f %s" % name)
        if not list(lines):
            return False
        else:
            return True
    except:
        print("Error occurred while process running check")


def kill_processes_by_name(name):
    try:
        for line in os.popen("pgrep -f %s" % name):
            pid = int(line)
            os.kill(pid, signal.SIGKILL)
    except:
        print("Error occurred while killing process")
