from tango import AttrWriteType, DevState, DevFloat, EncodedAttribute
from tango.server import Device, attribute, command, pipe
from slsdet import Moench, runStatus, timingMode, detectorSettings, frameDiscardPolicy
from _slsdet import IpAddr
import subprocess
import time
from multiprocessing import Process
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

    def get_dtype(self, dr):
        if isinstance(dr, str):
            dr = int(dr)
        if dr == 32:
            return np.uint32
        elif dr == 16:
            return np.uint16
        elif dr == 8:
            return np.uint8
        elif dr == 4:
            return np.uint8
        else:
            raise TypeError(f"Bit depth: {dr} is not supported")

    def get_frame(self):
        # Read one frame from the receiver zmq stream, can be extended
        # to multi frames
        header = json.loads(self.socket.recv())
        msg = self.socket.recv(copy=False)
        view = np.frombuffer(
            msg.buffer, dtype=self.get_dtype(header["bitmode"])
        ).reshape(header["shape"])
        return view.copy(), header

    def get_all_frames(self):
        pass

    def delete_receiver(self):
        try:
            self.context.destroy()
        except:
            print("Unable to destroy zmq context")
        if self.context.closed:
            print("Successfully closed zmq socket")


class MoenchDetectorAcquire(Device):
    def init_device(self):
        self.pc_util = ComputerSetup()
        if self.pc_util.is_pc_ready():
            self.device = Moench()
            try:
                st = self.device.status
                self.info_stream("Current device status %s" % st)
            except RuntimeError as e:
                self.info_stream("Unable to establish connection with detector\n%s" % e)
                self.delete_device()
            self.zmq_receiver = ZmqReceiver(
                self.device.rx_zmqip, self.device.rx_zmqport
            )

    def delete_device(self):
        pass

    @command
    def acquire(self):
        self.device.rx_zmqstream = True
        self.device.rx_zmqfreq = 1
        p = Process(target=self.device.acquire)
        p.start()

    @command
    def get_frame(self):
        image, header = self.zmq_receiver.get_frame()
        print(f"Image with dimensions {image.shape}")
        print(np.matrix(image))


if __name__ == "__main__":
    MoenchDetectorAcquire.run_server()
