from tango import AttrWriteType, DevState, DevFloat, EncodedAttribute
from tango.server import Device, attribute, command, pipe
from slsdet import Moench, runStatus, timingMode, detectorSettings, frameDiscardPolicy
from _slsdet import IpAddr
import subprocess
import time
import os, socket
import re
import signal
import zmq, json
import numpy as np
from computer_setup import ComputerSetup


class ZmqReceiver:
    def __init__(self, ip, port):
        port = port
        ip = ip
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        endpoint = f"tcp://{ip}:{port}"
        print(f"Connecting to: {endpoint}")
        self.socket.connect(endpoint)
        self.socket.setsockopt(zmq.SUBSCRIBE, b"")

    def init_receiver(self):
        pass

    def get_frame(self):
        # Read one frame from the receiver zmq stream, can be extended
        # to multi frames
        header = json.loads(self.socket.recv())
        msg = self.socket.recv(copy=False)
        view = np.frombuffer(msg.buffer, dtype=get_dtype(header["bitmode"])).reshape(
            header["shape"]
        )
        return view.copy(), header

    def get_all_frames(self):
        pass


class MoenchDetectorAcquire(Device):
    def init_device(self):
        if ComputerSetup.is_pc_ready():
            self.device = Moench()
            try:
                st = self.device.status
                self.zmq_receiver = ZmqReceiver(
                    self.device.rx_zmqip.str(), self.device.rx_zmqport
                )
                self.info_stream("Current device status %s" % st)
            except RuntimeError as e:
                self.info_stream("Unable to establish connection with detector\n%s" % e)
                self.delete_device()

    def delete_device(self):
        pass


if __name__ == "__main__":
    MoenchDetectorAcquire.run_server()
