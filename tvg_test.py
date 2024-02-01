# python3.10.12 environment, /home/pi/venv_casperfpga310

# IMPORTS
# albatrosdigitizer imports
from casperfpga import CasperFpga, KatcpTransport
from casperfpga.transport_katcp import KatcpRequestFail
import casperfpga.snapadc 
import sys 
import struct 
import time
import math
import numpy as np # numpy 1.26 may break on RPI (4 or 5) arm architecture
import lbtools_l # requires pyusb github.com/pyusb/pyusb
# config_fpga imports
import argparse 
from configparser import ConfigParser 
import logging
import os
import datetime 
# albatros_daq_utils imports
import subprocess
import operator
import stat
import datetime
import time
import re
from snap_reset import snap_reset

# initialize FPGA
snap_ip = "127.0.0.1"
snap_port = 7147
fpga = CasperFpga(host=snap_ip, port=snap_port, transport=KatcpTransport)
print(f"Fpga is programmed and running: {fpga.is_running()}")
fpg_file = "/home/pi/steve/albatros_dual_input_gbe_4bitTVG_2024_01_23_2024-01-30_1703.fpg"
cooldowntime = 3 # seconds
# try to program i a few times
for i in range(5):
    try: 
        if fpga.upload_to_ram_and_program(fpg_file):
            print("Successfully programmed")
            break
        if i==4:
            print(f"Unable to upload bitstream after {5} tries")
    except KatcpRequestFail:
        print(f"Shutting down SNAP board for {cooldowntime} seconds")
        snap_reset(cooldowntime)
        print("SNAP reset complete")
    

