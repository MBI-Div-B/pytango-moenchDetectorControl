import subprocess
import time
import os, socket, sys
import re
import signal
from pathlib import PosixPath


class ComputerSetup:
    def init_pc(self, virtual=False):
        SLS_RECEIVER_PORT = "1954"
        PROCESSING_RX_IP_PORT = "192.168.3.200 50003"
        PROCESSING_TX_IP_PORT = "192.168.1.118 50001"
        PROCESSING_CORES = "20"
        if virtual:
            CONFIG_PATH = "/home/moench/detector/moench_2021_virtual.config"  # for virtual detector
            self.start_virtual_detector = subprocess.Popen(
                "exec moenchDetectorServer_virtual",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(5)
            print("configured for virtual detector")

        else:
            CONFIG_PATH = "/home/moench/detector/moench_2021.config"  # for real (hardware) detector
            print("configured for real detector")
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
            "exec sls_detector_put config {path}".format(path=CONFIG_PATH),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.sls_running = self.slsDetectorProc.poll() == None
        self.zmq_running = self.zmqDataProc.poll() == None
        time.sleep(5)
        print("Both processses are running")
        if virtual:
            put_config = subprocess.Popen(
                "exec sls_detector_put config {path}".format(path=CONFIG_PATH),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            print("Uploaded the config the 2nd time for virtual")
        print("Both processses are running")
        return self.sls_running & self.zmq_running

    def deactivate_pc(self, virtual=False):
        self.slsDetectorProc.kill()
        self.zmqDataProc.kill()
        if virtual:
            self.start_virtual_detector.kill()
            self.kill_processes_by_name("moenchDetectorServer_virtual")

    def is_sls_running(self):
        return self.is_process_running("slsReceiver")

    def is_zmq_running(self):
        return self.is_process_running("moench04ZmqProcess")

    def is_pc_ready(self):
        if self.is_sls_running() and self.is_zmq_running():
            return True
        else:
            return False

    def is_process_running(self, name):
        try:
            lines = os.popen("pgrep -f %s" % name)
            if not list(lines):
                return False
            else:
                return True
        except:
            print("Error occurred while process running check")

    def kill_processes_by_name(self, name):
        try:
            for line in os.popen("pgrep -f %s" % name):
                pid = int(line)
                os.kill(pid, signal.SIGKILL)
        except:
            print("Error occurred while killing process")
