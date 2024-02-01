import RPi.GPIO as GPIO
import time
import argparse
import subprocess
import muxtools
import os
import albatros_daq_utils as utils

MODELS = utils.get_config_parameter("/home/pi/albatros2_daq/new_daq/config.ini", "drive_models")

def snap_reset(cooldowntime, pin=20):
    # SNAP reset behaves oddly when GPIO12 (MUXEN) and GPIO16 (POWEREN) are enabled so set both pins to 0 before resetting SNAP.
    muxtools.init_mux()
    drives = utils.list_drives_to_write_too(MODELS)
    for drive in drives:
        MOUNTPOINT = drive["Mounted on"]
        try:
            utils.safe_unmount(MOUNTPOINT)
            time.sleep(5)
        except:
            print("Drive found but couldn't unmount.")
    muxtools.poweren(0)
    muxtools.muxen(0)

    # Reset SNAP powercontrollers
    # Wait to let SNAP cooldown from overheated state, then toggle GPIO20 pin.
    time.sleep(cooldowntime)
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 1)
    time.sleep(1)
    GPIO.output(pin, 0)
    # Wait several seconds to let SNAP fully power up
    time.sleep(5)

def snap_off(pin=20):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 1)

def snap_on(pin=20, toggle=False):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)
    if toggle:
        GPIO.output(pin, 1)
    GPIO.output(pin, 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to reset SNAP Board")
    parser.add_argument("-t", "--cooldowntime", type=float, default=10, help="Time in seconds to let SNAP Board cool before turning it back on")
    parser.add_argument("-a", "--action", type=str, default="reset", help="Action to perform using the SNAP GPIO reset mode (reset, on, or off)")
    parser.add_argument("-p", "--pin", type=int, default=20, help="RPi GPIO pin used for resetting SNAP Board")
    args = parser.parse_args()

    if args.action == 'reset':
        print("Shutting down SNAP for {} second(s).".format(args.cooldowntime))
        snap_reset(args.cooldowntime, pin=args.pin)
        print("SNAP reset complete.")

    if args.action == 'on':
        snap_on()

    if args.action == 'off':
        snap_off()
