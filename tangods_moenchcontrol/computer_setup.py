import subprocess
import time
import os


def init_pc(
    virtual,
    SLS_RECEIVER_PATH,
    SLS_RECEIVER_PORT,
    VIRTUAL_DETECTOR_BIN,
    ROOT_PASSWORD,
):
    if virtual:
        subprocess.Popen(
            VIRTUAL_DETECTOR_BIN,
            shell=False,
        )
        time.sleep(5)
        print("configured for virtual detector")

    else:
        print("configured for real detector")
    # CONFIG_PATH = "/home/moench/detector/moench_2021.config" #for real detector
    # configured for moench pc only
    print("starting slsReceiver instance")
    print("change")
    subprocess.Popen(
        f'sudo -S <<< "{ROOT_PASSWORD}" {SLS_RECEIVER_PATH} -t {SLS_RECEIVER_PORT}',
        shell=True,
    )
    print("started slsReceiver")
    time.sleep(2)
    print("Setup is ready")
    return is_sls_running()


def kill_all_pc_processes(ROOT_PASSWORD):
    for process_name in ["slsReceiver", "moenchDetectorServer_virtual"]:
        kill_processes_by_name(
            process_name,
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
