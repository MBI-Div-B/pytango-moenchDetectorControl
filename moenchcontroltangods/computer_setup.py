import subprocess
import time
import os, socket, sys
import re
import signal
from pathlib import PosixPath


def init_pc(
    virtual=False,
    SLS_RECEIVER_PORT="1954",
    VIRTUAL_DETECTOR_BIN="/opt/moench-slsDetectorGroup/build/bin/moenchDetectorServer_virtual",
    CONFIG_PATH_REAL="/opt/moench-slsDetectorGroup/moench03_hardware.config",
    CONFIG_PATH_VIRTUAL="/opt/moench-slsDetectorGroup/moench03_virtual.config",
    ROOT_PASSWORD="dummy_password",
):
    start_10g_interface(ROOT_PASSWORD)
    if virtual:
        CONFIG_PATH = CONFIG_PATH_VIRTUAL  # for virtual detector
        subprocess.Popen(
            VIRTUAL_DETECTOR_BIN,
            shell=False,
        )
        time.sleep(5)
        print("configured for virtual detector")

    else:
        CONFIG_PATH = CONFIG_PATH_REAL  # for  real (hardware) detector
        print("configured for real detector")
    # CONFIG_PATH = "/home/moench/detector/moench_2021.config" #for real detector
    # configured for moench pc only
    print("starting slsReceiver instance")
    subprocess.Popen(
        f'sudo -S <<< "{ROOT_PASSWORD}" slsReceiver -t {SLS_RECEIVER_PORT}',
        shell=True,
    )
    print(f"Loading config {CONFIG_PATH} to the detector")
    subprocess.call([f"sls_detector_put", "config", CONFIG_PATH])
    time.sleep(2)
    print("Setup is ready")
    # otherwise it doesn't work for virtual detector
    if virtual:
        subprocess.call(["sls_detector_put", "config", CONFIG_PATH])
        print("Uploaded the config the 2nd time for virtual.")
    return is_sls_running()


def kill_all_pc_processes(ROOT_PASSWORD):
    kill_processes_by_name(
        "slsReceiver",
        root_password=ROOT_PASSWORD,
    )
    kill_processes_by_name(
        "moenchDetectorServer_virtual",
        root_password=ROOT_PASSWORD,
    )


def deactivate_pc(ROOT_PASSWORD):
    kill_all_pc_processes(ROOT_PASSWORD)


def is_sls_running():
    return is_process_running("slsReceiver")


def is_process_running(name):
    try:
        lines = os.popen("pgrep -f %s" % name)
        if not list(lines):
            return False
        else:
            return True
    except:
        print("Error occurred while process running check")


def kill_processes_by_name(name, root_password):
    try:
        for line in os.popen("pgrep -f %s" % name):
            pid = int(line)
            subprocess.call(
                f'sudo -S <<< "{root_password}" kill -9 {pid}',
                shell=True,
            )
    except:
        print("Error occurred while killing process")


def start_10g_interface(root_password):
    subprocess.call(
        f'sudo -S <<< "{root_password}" ifup eno2',
        shell=True,
    )
