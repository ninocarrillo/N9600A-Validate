# validate.py
# Python3
# Validate N9600A firmware
# Nino Carrillo
# 19 Jan 2024
# Exit codes
# 1 Wrong python version
# 2 Not enough command line arguments
# 3 Unable to open test serial port
# 4 Unable to open standard serial port

import serial
import sys
import time
import subprocess
import validate_gpio_functions as vgpio
impoprt validate_threading_functions as vthread

if sys.version_info < (3, 0):
	print("Python version should be 3.x, exiting")
	sys.exit(1)


vgpio.SetupGPIO()

vgpio.SetTestDeviceMode(4)
vgpio.SetStandardDeviceMode(4)
time.sleep(2)

#subprocess.run(["aplay", "/home/pi/github/modem-test-audio/1_single/GFSK_4800_IL2Pc_50b_1x.wav"])

vthread.popen_and_call(print("Thread Done!"), ["aplay", "/home/pi/github/modem-test-audio/1_single/GFSK_4800_IL2Pc_50b_1x.wav"])

time.sleep(5)

for mode in range(16):
	vgpio.SetTestDeviceMode(mode)
	print("Test Mode: ", mode)
	vgpio.SetStandardDeviceMode(mode)
	print("Standard Mode: ", mode)
	time.sleep(2)

	vgpio.AssertTestTXButton()
	time.sleep(.1)
	vgpio.ReleaseTestTXButton()
	time.sleep(5)

vgpio.Cleanup()

sys.exit(0)
