from tango import AttrWriteType, DevState, DevFloat, EncodedAttribute
from tango.server import Device, attribute, command, pipe
from slsdet import Moench, runStatus, timingMode, detectorSettings, frameDiscardPolicy
from _slsdet import IpAddr
import subprocess
import time
import os, socket
import re
import signal
import zmq
import numpy as np


class ZmqReceiver:
    def init_receiver(self):
        pass

    def get_frame(self):
        pass

    def get_all_frames(self):
        pass


class MoenchDetectorAcquire(Device):
    def init_device(self):
        pass

    def delete_device(self):
        pass


if __name__ == "__main__":
    MoenchDetectorAcquire.run_server()
