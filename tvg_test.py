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
import numpy as np  # numpy 1.26 may break on RPI (4 or 5) arm architecture, try 1.25 instead
import lbtools_l  # requires pyusb github.com/pyusb/pyusb

# config_fpga imports
import argparse
#from configparser import ConfigParser
import configparser
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
import albatros_daq_utils as utils

# other
from dataclasses import dataclass  # Python3.7, think struct
from enum import Enum  # Python's Enum type
from time import sleep 

# utility
def str2ip(ip_str):
    octets=list(map(int, ip_str.split(".")))
    ip=(octets[0]<<24)+(octets[1]<<16)+(octets[2]<<8)+(octets[3])
    return ip

# Define some consts
class BitMode(Enum):
    BITS_1 = 0
    BITS_2 = 1
    BITS_4 = 2

bits = 1
bit_mode = BitMode[f'BITS_{bits}']

# For now, just load a few things from config.ini into vars
config_file=configparser.ConfigParser()
config_file.read("config.ini")
channels=config_file.get("albatros3","channels")
chans=utils.get_channels_from_str(channels, bits) # TODO: tidy bits convention
channels_coeffs=config_file.get("albatros3","channel_coeffs")
coeffs=utils.get_coeffs_from_str(channels_coeffs) # TODO: decide on bits convention
coeffs=coeffs[:1<<6] # hack
dest_ip, dest_port, dest_mac = utils.read_ifconfig(interface="eth0")
if dest_port is not None:
    dest_port = int(dest_port)
print("dest_ip", dest_ip, "dest_port", dest_port, "dest_mac", dest_mac)

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
    print(f"i={i}")
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
    'snap_inputs':4, # number of ADCs to activate(??)
}

## SNAP ADC
#print("Configuring SnapAdc...",end=" ")
#snap_adc = casperfpga.snapadc.SnapAdc(
#        host=fpga, device_name=snap_name, device_info=snap_info, ref_clock=ref_clock
#        )
#snap_adc.init(
#    sample_rate=snap_info['sample_rate'], 
#    numChannel=4
#    ) # unlike python2 version, doesn't do tests
## Test the snap_adc
## 1. LMX is already tested, will throw error if failed
## 2. ERROR_MMCM 
#assert(snap_adc.getWord("ADC16_LOCKED"),"MMCM not locked")
## 3. ERROR_LINE
#assert({} == snap_adc.alignLineClock(),"line clock not aligned")
## 4. ERROR_FRAME
#failed_chips = snap_adc.alignFrameClock()
#assert({} == failed_chips,"frame clock not aligned")
#del(failed_chips) # garbage collect
## 5. ERROR_RAMP
#results = snap_adc.test_patterns(mode='ramp')
#print(results)
#if not np.all(np.array([adc.values() for adc in results.values()])==0):
#    raise Exception("Failed ramp test")
#del results
#print("Done")

# Set channel coeffs
def set_channel_coeffs(fpga, coeffs, bit_mode:BitMode):
    # TODO: check coeffs make sense
    if bit_mode is BitMode.BITS_1:
        print("No need to set coeffs in 1-bit mode")
        return True
    elif bit_mode is BitMode.BITS_2:
        coeffs_bram_name="two_bit_quant_coeffs"
    elif bit_mode is BitMode.BITS_4:
        coeffs_bram_name="four_bit_quant_coeffs"
    else:
        raise Exception("Bit_mode not valid.") # logically impossible
    print(f"Setting coeffs in {bit_mode.name} bit-mode")
    #fpga.write(coeffs_bram_name, coeffs.tostring(), offset=0)
    print(coeffs)
    fpga.write(coeffs_bram_name, coeffs.tobytes(), offset=0)
    return True

# Set channel order
def set_channel_order(fpga, chans, bit_mode:BitMode):
    if bit_mode is BitMode.BITS_1:
        channel_map="packetiser_one_bit_reorder_map1"
    elif bit_mode is BitMode.BITS_2:
        channel_map="packetiser_two_bit_reorder_map1" # does not exist
    elif bit_mode is BitMode.BITS_4:
        channel_map="packetiser_four_bit_reorder_map1"
    else:
        raise Exception("Bit mode invalid.")
    #fpga.write(channel_map, chans.astype(">H").tostring(), offset=0)
    print("chans:",chans)
    fpga.write(channel_map, chans.astype(">H").tobytes(), offset=0)
    return True

# REGISTERS -- enable stuff
print("Enable TVG, packetizer sel, dest_port, dest_ip...",end=" ")
fpga.registers.packetiser_tvg4bit_enable.write_int(1) # Enable the TVG
fpga.registers.packetiser_sel.write_int(bit_mode.value) # Select bit mode0:1bit, 1:2bit, 2:4bit 
fpga.registers.dest_ip.write_int(str2ip(dest_ip))
fpga.registers.dest_port.write_int(dest_port)
print("Done")
print("tvg4bit_enable:", fpga.registers.packetiser_tvg4bit_enable.read()['data']['reg'])
print("packetiser_sel:", fpga.registers.packetiser_sel.read()['data']['reg'])
print("dest_ip:", fpga.registers.dest_ip.read()['data']['reg'])
print("dest_port:", fpga.registers.dest_port.read()['data']['reg'])
print()

fpga.write("packetiser_four_bit_reorder_map1", np.array([0,1,2,3,4,5,6,7]).astype(">H").tobytes(), offset=0)
#fpga.write("packetiser_four_bit_reorder_map1", 
#        (np.arange(0,256)//2).astype(">H").tobytes(), 
#        offset=0)

# CHANNELS -- set channel order
set_channel_order(fpga, chans, bit_mode)
set_channel_coeffs(fpga, coeffs, bit_mode)

# Packet reset
print("Packet counter reset LOW, HIGH, LOW...",end=" ")
fpga.registers.in_packet_reset.write_int(0)
sleep(0.1)
fpga.registers.in_packet_reset.write_int(1)
sleep(0.1)
fpga.registers.in_packet_reset.write_int(0)
print("Done")

# REGISTERS -- Sync pulse (resets stuff)
print("Sync pulse LOW, HIGH, LOW...",end=" ")
fpga.registers.in_sw_sync.write_int(0) # sync pulse
sleep(0.1) # dogmatically sleep between pulse reset
fpga.registers.in_sw_sync.write_int(1) 
sleep(0.1) # dogmatically sleep between pulse reset
fpga.registers.in_sw_sync.write_int(0) 
print("Done")

print("Sleep 3...",end=" ")
sleep(3)
print("Done")

# REGISTERS -- disable GBE
print("Disabling GBE: LOW",end=" ")
fpga.registers.in_gbe_enable.write_int(0)
print("Done")
sleep(1)

# REGISTERS -- Set spec per packet and bytes per spec
print("\nspec per pkt",fpga.registers.packetiser_spec_per_pkt.read()['data']['reg']) # hack
print("bytes per spec",fpga.registers.packetiser_bytes_per_spec.read()['data']['reg']) # hack
print("Setting spec per pkt and bytes per spec...",end=" ")
fpga.registers.packetiser_spec_per_pkt.write_int(10)
fpga.registers.packetiser_bytes_per_spec.write_int(len(chans)) # TODO: verify this
print("done")
print("spec per pkt",fpga.registers.packetiser_spec_per_pkt.read()['data']['reg']) # hack
print("bytes per spec",fpga.registers.packetiser_bytes_per_spec.read()['data']['reg']) # hack

# REGISTERS -- Reset GBE
print("Reset GBE: LOW, HIGH, LOW...",end=" ")
fpga.registers.in_gbe_reset.write_int(0) 
sleep(1)
fpga.registers.in_gbe_reset.write_int(1) 
sleep(1)
fpga.registers.in_gbe_reset.write_int(0) 
sleep(1)
print("Done")

# REGISTERS -- Enable GBE
print("Enabling GBE: HIGH (must stay high)...",end=" ")
fpga.registers.in_gbe_enable.write_int(1)
print("Done")
sleep(1)






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
