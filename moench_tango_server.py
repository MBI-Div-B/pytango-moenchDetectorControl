from tango import AttrWriteType, DevState,  DevFloat, EncodedAttribute
from tango.server import Device, attribute, command, pipe
from slsdet import Moench, runStatus, timingMode	
import subprocess
import time
import os
import signal

class MoenchDetector(Device):
	exposure = attribute(label = "exposure [in seconds]", dtype = "float",
                   access = AttrWriteType.READ_WRITE, memorized = True,
                   hw_memorized = True, polling_period = polling)
    trigger_mode = attribute(label = "trigger mode [auto/external trigger]")
    filename = attribute(label = "file name for output data file", dtype = "str")
    filepath = attribute(label = "dir where data files will be written", dtype = "str")
    frames = attribute(label = "number of frames per acquisition", dtype = "int")
    filewrite = attribute(label = "enable or disable file writing", dtype = "bool")
    highvoltage = attribute(label = "high voltage on sensor [60-200V]", dtype = "int")
        
	def init_pc(self):
		SLS_RECEIVER_PORT = "1954"
		PROCESSING_RX_IP_PORT = "192.168.2.200 50003"
		PROCESSING_TX_IP_PORT = "192.168.1.200 50001"
		PROCESSING_CORES = "20"
		CONFIG_PATH = "/home/moench/detector/moench_2021_virtual.config" #for virtual detector
		#CONFIG_PATH = "/home/moench/detector/moench_2021.config" #for real detector
		#configured for moench pc only
		self.slsDetectorProc = subprocess.Popen("exec slsReceiver -t {}".format(SLS_RECEIVER_PORT), shell=True, stdout=subprocess.PIPE, stderr = subprocess.PIPE, preexec_fn = os.setsid)
		self.zmqDataProc = subprocess.Popen("exec moench04ZmqProcess {} {} {}".format(PROCESSING_RX_IP_PORT, PROCESSING_TX_IP_PORT, PROCESSING_CORES), shell = True, stdout = subprocess.PIPE, stderr =s ubprocess.PIPE, preexec_fn = os.setsid)
		self.put_config = subprocess.Popen("exec sls_detector_put config {}".format(CONFIG_PATH), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		sls_running = self.slsDetectorProc.poll() == None
		zmq_running = self.zmqDataProc.poll() == None
		print("Both processses are running")
		return (sls_running & zmq_running)
		
	def init_device(self):
		Device.init_device(self)
		self.set_state(DevState.INIT)
		if (not self.init_pc()):
			self.set_state(DevState.FAULT)
			print("Unnable to start slsReceiver or zmq socket. Check firewall process and already running instances.")
		time.sleep(1)
		device = Moench()
		try:
			st = device.status
			print("Current device status: %s" % st)
		except RuntimeError as e:
			self.set_state(DevState.FAULT)
			print("Unnable to establish connection with detector\n%s" % e)
			self.delete_device()
	@command
	def delete_device(self):
		try:
			self.slsDetectorProc.kill()
			self.zmqDataProc.kill()
			print("SlsReceiver or zmq socket processes were killed.")
		except Exception:
			print("Unnable to kill slsReceiver or zmq socket. Please kill it manually.")
	
	def exptime(self):
		
if __name__ == "__main__":
	MoenchDetector.run_server()
