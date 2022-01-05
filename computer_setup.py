def init_pc(tango_device, virtual=False):
    SLS_RECEIVER_PORT = "1954"
    PROCESSING_RX_IP_PORT = "192.168.2.200 50003"
    PROCESSING_TX_IP_PORT = "192.168.1.200 50001"
    PROCESSING_CORES = "20"

    if virtual:
        CONFIG_PATH = "/home/lrlunin/moench_2021_virtual.config"  # for virtual detector
        start_virtual_detector = subprocess.Popen(
            "exec moenchDetectorServer_virtual",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("configured for virtual detector")

    else:
        CONFIG_PATH = (
            "/home/moench/detector/moench_2021.config"  # for real (hardware) detector
        )
        print("configured for real detector")

    # CONFIG_PATH = "/home/moench/detector/moench_2021.config" #for real detector
    # configured for moench pc only
    slsDetectorProc = subprocess.Popen(
        "exec slsReceiver -t {}".format(SLS_RECEIVER_PORT),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    )
    zmqDataProc = subprocess.Popen(
        "exec moench04ZmqProcess {} {} {}".format(
            PROCESSING_RX_IP_PORT, PROCESSING_TX_IP_PORT, PROCESSING_CORES
        ),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    )
    put_config = subprocess.Popen(
        "exec sls_detector_put config {path}".format(path=CONFIG_PATH),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if virtual:
        subprocess.Popen(
            "exec sls_detector_put config {path}".format(path=CONFIG_PATH),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    sls_running = slsDetectorProc.poll() == None
    zmq_running = zmqDataProc.poll() == None
    print("Both processses are running")
    return sls_running & zmq_running
