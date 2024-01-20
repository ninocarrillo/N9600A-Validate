# n9600a-validate
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
import RPi.GPIO as gpio
import subprocess
import validate-functions as val



if sys.version_info < (3, 0):
	print("Python version should be 3.x, exiting")
	sys.exit(1)

gpio.setmode(gpio.BCM)

val.SetupGPIO()

val.SetTestDeviceMode(4)
val.SetStandardDeviceMode(4)
time.sleep(2)

subprocess.run(["aplay", "/home/pi/github/modem-test-audio/1_single/GFSK_4800_IL2Pc_50b_1x.wav"])

time.sleep(1)

for mode in range(16):
	val.SetTestDeviceMode(mode)
	print("Test Mode: ", mode)
	val.SetStandardDeviceMode(mode)
	print("Standard Mode: ", mode)
	time.sleep(2)

	val.AssertTestTXButton()
	time.sleep(.1)
	val.ReleaseTestTXButton()
	time.sleep(5)
gpio.cleanup()

sys.exit(0)
