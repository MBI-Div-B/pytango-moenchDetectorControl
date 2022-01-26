from tango import AttrWriteType, DevState, DevFloat, EncodedAttribute, DeviceProxy
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
import computer_setup


class ZmqReceiver:
    def __init__(self, ip, port):
        # need to be initialized only in case if the zmq server is up
        port = port
        ip = ip
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        endpoint = f"tcp://{ip}:{port}"
        print(f"Connecting to: {endpoint}")
        self.socket.connect(endpoint)
        self.socket.setsockopt(zmq.SUBSCRIBE, b"")

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
        try:
            header = json.loads(self.socket.recv(flags=zmq.NOBLOCK))
            msg = self.socket.recv(copy=False, flags=zmq.NOBLOCK)
            view = np.frombuffer(
                msg.buffer, dtype=self.get_dtype(header["bitmode"])
            ).reshape(header["shape"])
            return view.copy(), header
        except:
            return None, None

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
        Device.init_device(self)
        self.set_state(DevState.INIT)
        MAX_ATTEMPTS = 5
        self.attempts_counter = 0
        self.zmq_receiver = None
        # TODO: HERE CAN BE REPLACED WITH MoenchControl deviceproxy and check flag
        while not computer_setup.is_pc_ready() and self.attempts_counter < MAX_ATTEMPTS:
            time.sleep(0.5)
            self.attempts_counter += 1
            self.info_stream("Waiting for PC...")
        if computer_setup.is_pc_ready():
            self.device = Moench()
            try:
                st = self.device.rx_status
                self.info_stream(f"Current device status {st}")
            except RuntimeError as e:
                self.info_stream(f"Unable to establish connection with detector\n{e}")
                self.delete_device()
            self.zmq_receiver = ZmqReceiver(
                self.device.rx_zmqip, self.device.rx_zmqport
            )
            self.set_state(DevState.ON)
            # TODO: virtual flag check is necessary
            self.tango_control_device = DeviceProxy("rsxs/moenchControl/bchip286")
        else:
            self.set_state(DevState.FAULT)
            self.info_stream("Control tango server is not available")
            self.delete_device()

    @command
    def delete_device(self):
        if self.zmq_receiver != None:
            self.zmq_receiver.delete_receiver()

    def acquire_and_write_path(self, device, tango_device, current_path):
        device.acquire()
        tango_device.tiff_fullpath_last = current_path

    @command
    def acquire(self):
        if self.device.status == runStatus.IDLE:
            tiff_fullpath_current = self.tango_control_device.tiff_fullpath_next
            # p = Process(target=self.device.acquire)
            p = Process(
                target=self.acquire_and_write_path,
                args=(
                    self.device,
                    self.tango_control_device,
                    tiff_fullpath_current,
                ),
            )
            p.start()
        elif self.device.status == runStatus.RUNNING:
            self.info_stream("Detector is acquiring")
        else:
            self.error_stream("Unable to acquire")

    @command
    def get_frame(self):
        image, header = self.zmq_receiver.get_frame()
        if image == None or header == None:
            self.info_stream("No acquired capture in the zmq queue")
        else:
            self.info_stream(f"Image with dimensions {image.shape}")
            print(image)


if __name__ == "__main__":
    MoenchDetectorAcquire.run_server()
