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
        return self.sls_running & self.zmq_running

    def deactivate_pc(self, virtual=False):
        self.slsDetectorProc.kill()
        self.zmqDataProc.kill()
        if virtual:
            self.start_virtual_detector.kill()
            self.kill_processes_by_name("moenchDetectorServer_virtual")

    def is_sls_running(self):
        pass

    def is_pc_ready(self):
        if True:
            return True
        else:
            return False

    def is_detector_available(self):
        if True:
            return True
        else:
            return False

    def is_process_running(self, name):
        pass

    def kill_processes_by_name(self, name):
        try:
            for line in os.popen("ps ax | grep %s" % name):
                fields = line.split()
                pid = int(fields[0])
                os.kill(pid, signal.SIGKILL)
        except:
            print("Error occurred")
