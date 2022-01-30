import sys
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
        self.tango_control_device = DeviceProxy("rsxs/moenchControl/bchip286")
        while self.attempts_counter < MAX_ATTEMPTS:
            try:
                control_state = self.tango_control_device.state()
            except:
                control_state = DevState.OFF
            else:
                break
            self.attempts_counter += 1
            self.info_stream(f"Control device status: {control_state}")
            self.info_stream(f"Attempts left: {MAX_ATTEMPTS - self.attempts_counter}")
            time.sleep(1)
        if control_state == DevState.ON:
            self.device = Moench()
            self.zmq_receiver = ZmqReceiver(
                self.device.rx_zmqip, self.device.rx_zmqport
            )
            self.set_state(DevState.ON)
            # TODO: virtual flag check is necessary

        else:
            self.set_state(DevState.FAULT)
            self.info_stream("Control tango server is not available")
            self.delete_device()

    def _block_acquire(self):
        exptime = self.device.exptime
        frames = self.device.frames
        self.device.startDetector()
        self.device.startReceiver()
        time.sleep(exptime * frames)
        while self.device.status != runStatus.IDLE:
            time.sleep(0.1)
        self.device.stopReceiver()

    async def _async_acquire(self, loop):
        self.set_state(DevState.RUNNING)
        await loop.run_in_executor(None, self._block_acquire)
        self.set_state(DevState.ON)

    @command
    async def acquire(self):
        if self.device.status == runStatus.IDLE:
            loop = asyncio.get_event_loop()
            future = loop.create_task(self._async_acquire(loop))
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

    @command
    def delete_device(self):
        if self.zmq_receiver != None:
            self.zmq_receiver.delete_receiver()


if __name__ == "__main__":
    MoenchDetectorAcquire.run_server()
