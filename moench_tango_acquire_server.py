#!/bin/python3
from tango import DevState, DeviceProxy, GreenMode, DispLevel
from tango.server import Device, attribute, command, pipe, device_property
from slsdet import Moench, runStatus, timingMode
import time
import json
import numpy as np
import asyncio


class MoenchDetectorAcquire(Device):
    green_mode = GreenMode.Asyncio

    MAX_ATTEMPTS = device_property(
        dtype=int,
        doc="number of attempts to establish connection with control device",
        default_value=10,
    )
    CONNECT_COOLDOWN = device_property(
        dtype=int,
        doc="delay before the next connection attempt with control device",
        default_value=2,
    )

    status_dict = {
        runStatus.IDLE: DevState.ON,
        runStatus.ERROR: DevState.FAULT,
        runStatus.WAITING: DevState.STANDBY,
        runStatus.RUN_FINISHED: DevState.ON,
        runStatus.TRANSMITTING: DevState.RUNNING,
        runStatus.RUNNING: DevState.RUNNING,
        runStatus.STOPPED: DevState.ON,
    }

    def init_device(self):
        Device.init_device(self)
        self.get_device_properties(self.get_device_class())
        attempts_counter = 0
        self.tango_control_device = DeviceProxy("rsxs/moenchControl/bchip286")
        while attempts_counter < self.MAX_ATTEMPTS:
            try:
                control_state = self.tango_control_device.state()
            except:
                control_state = DevState.OFF
            else:
                break
            attempts_counter += 1
            self.info_stream(f"Control device status: {control_state}")
            self.info_stream(f"Attempts left: {self.MAX_ATTEMPTS - attempts_counter}")
            time.sleep(self.CONNECT_COOLDOWN)
        if control_state == DevState.ON:
            self.device = Moench()
            self.set_state(DevState.ON)
        else:
            self.set_state(DevState.FAULT)
            self.info_stream("Control tango server is not available")
            self.delete_device()

    @command(display_level=DispLevel.EXPERT, polling_period=100)
    def update_tango_state(self):
        tango_state = self.status_dict.get(self.device.status)
        if tango_state is not None:
            self.set_state(tango_state)
        else:
            self.set_state(DevState.UNKNOWN)

    def _block_acquire(self):
        exptime = self.device.exptime
        frames = self.device.frames
        self.device.startDetector()
        self.device.startReceiver()
        # in case detector is stopped we want to leave this section earlier
        # time.sleep(exptime * frames)
        while self.get_state() != DevState.ON:
            time.sleep(0.1)
        self.device.stopReceiver()

    async def _async_acquire(self, loop):
        tiff_fullpath_current = self.tango_control_device.tiff_fullpath_next
        filewriteEnabled = self.tango_control_device.filewrite
        await loop.run_in_executor(None, self._block_acquire)
        if filewriteEnabled:
            self.tango_control_device.fileindex += 1
        self.tango_control_device.tiff_fullpath_last = tiff_fullpath_current

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
    def stop_acquire(self):
        self.device.stop()

    @command
    def delete_device(self):
        Device.delete_device(self)


if __name__ == "__main__":
    MoenchDetectorAcquire.run_server()
