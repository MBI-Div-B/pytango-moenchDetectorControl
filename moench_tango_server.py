from tango import AttrWriteType, DevState,  DevFloat, EncodedAttribute
from tango.server import Device, attribute, command, pipe
from slsdet import Moench, runStatus, timingMode
import subprocess

class MoenchDetector(Device):
	def init_pc(self):
		SLS_RECEIVER_PORT = "1954"
		PROCESSING_RX_IP_PORT = "192.168.2.200 50003"
		PROCESSING_TX_IP_PORT = "192.168.1.200 50001"
		PROCESSING_CORES = "20"
		CONFIG_PATH = "/home/moench/detector/moench_2021.config"
		#configured for moench pc only
		self.slsDetectorProc = subprocess.Popen("slsReceiver -t {}".format(SLS_RECEIVER_PORT))
		self.zmqDataProc = subprocess.Popen("moench04ZmqProcess {} {} {}".format(PROCESSING_RX_IP_PORT, PROCESSING_TX_IP_PORT, PROCESSING_CORES))
		sls_running = slsDetectorProc.poll() == None
		zmq_running = zmqDataProc() == None
		return (sls_running & zmq_running)
	def init_device(self):
		self.set_state(DevState.INIT)
		if (!self.init_pc()):
			self.set_state(DevState.FAULT)
			self.info_stream("Unnable to start slsReceiver or zmq socket. Check firewall process and already running instances.")
		device = Moench()
		try:
			st = device.status
			self.info_stream("Current device status: %s" % st)
		except RuntimeError as e:
			self.set_state(DevState.FAULT)
			self.info_stream("Unnable to establish connection with detector\n%s" % e)
			try:
				self.slsDetectorProc.kill()
				self.zmqDataProc.kill()
				self.info_stream("SlsReceiver or zmq socket processes were killed.")
			expect Exception:
				self.info_stream("Unnable to kill slsReceiver or zmq socket. Please kill it manually.")

if __name__ == "__main__":
	MoenchDetector.run_server()
