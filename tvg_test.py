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
import numpy as np  # numpy 1.26 may break on RPI (4 or 5) arm architecture
import lbtools_l  # requires pyusb github.com/pyusb/pyusb

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

# other
from dataclasses import dataclass  # Python3.7, think struct
from enum import Enum  # Python's Enum type
from time import sleep 

# initialize FPGA
snap_ip = "127.0.0.1"
snap_port = 7147
fpga = CasperFpga(host=snap_ip, port=snap_port, transport=KatcpTransport)
print(f"Fpga is programmed and running: {fpga.is_running()}")
fpg_file = (
    "/home/pi/steve/albatros_dual_input_gbe_4bitTVG_2024_01_23_2024-01-30_1703.fpg"
)
cooldowntime = 3 #180  # seconds(?)

# Try to program FPGA a few times
for i in range(5):
    try:
        result = fpga.upload_to_ram_and_program(fpg_file)
        if result is True:
            print(f"Successfully programmed result={result}")
            break
        if i == 4:
            print(f"Unable to upload bitstream after {5} tries")
    except KatcpRequestFail:
        print(f"Shutting down SNAP board for {cooldowntime} seconds")
        snap_reset(cooldowntime)
        print("SNAP reset complete")
# Initialize the ADC
ref_clock = 10 # synthesizer_clock_ref from config.ini
snap_name = "SNAP_adc" # default snap name
# in previous versions of casperfpga.snapadc, snap_info were params passed to init()
# which was an initialization function distinct from __init__(), in py310 they packed 
# both into __init__()
snap_info = {
    'adc_resolution':8, # 8-bit ADC
    'sample_rate':250, # 250 MHz
    'snap_inputs':4, # number of channels to activate(??)
}
snap_adc = casperfpga.snapadc.SnapAdc(host=fpga, device_name=snap_name, device_info=snap_info, ref_clock=ref_clock)
snap_adc.init(sample_rate=snap_info['sample_rate'], numChannel=4)
fpga.registers.packetiser_tvg4bit_enable.write_int(1) # Enable the TVG
fpga.registers.packetiser_bytes_per_spec.write_int(128) # number of channels
fpga.registers.packetiser_sel.write_int(2) # Mux out the 4bit line
fpga.registers.in_sw_sync.write_int(0) # sync pulse
sleep(0.1) # dogmatically sleep between pulse reset
fpga.registers.in_sw_sync.write_int(1) 
sleep(0.1) # dogmatically sleep between pulse reset
fpga.registers.in_sw_sync.write_int(0) 
print("Done")

## An idea I was toying with:
## Enum
#class BitfieldType(Enum):
#    UFIX = 0
#    FIX = 1
#    BOOL = 2
#
## For reading/writing to register
#@dataclass
#class Register:
#    name: str  # the name of the register, e.g. "packetizer_tvg_enable"
#    val: int # value to write
#
#@dataclass
#class TVG:  # block of memory for Test Vector Generator
#    name: str  # the name of the memory block, e.g. "packetizer_tvg_enable"
#    data_width: int  # bit_depth of data, corresponds to Simulink block parameter
#    address_width: int  # e.g. 12 for 2^12 addresses
#    values: list  # a list of values of len 2^address_width