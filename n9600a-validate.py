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


def SetupGPIO():
	# Test Device MODE3 Switch
	gpio.setup(17,gpio.OUT)
	gpio.output(17, gpio.LOW)
	# Test Device MODE2 Switch
	gpio.setup(18,gpio.OUT)
	gpio.output(18,gpio.LOW)
	# Test Device MODE1 Switch
	gpio.setup(27,gpio.OUT)
	gpio.output(27,gpio.LOW)
	# Test Device MODE0 Switch
	gpio.setup(22,gpio.OUT)
	gpio.output(22,gpio.LOW)
	# Test Device Test_TX Button
	gpio.setup(23,gpio.OUT)
	gpio.output(23,gpio.LOW)
	# Standard Device MODE3 Switch
	gpio.setup(24,gpio.OUT)
	gpio.output(24,gpio.LOW)
	# Standard Device MODE2 Switch
	gpio.setup(25,gpio.OUT)
	gpio.output(25,gpio.LOW)
	# Standard Device MODE1 Switch
	gpio.setup(5,gpio.OUT)
	gpio.output(5,gpio.LOW)
	# Standard Device MODE0 Switch
	gpio.setup(6,gpio.OUT)
	gpio.output(6,gpio.LOW)
	return

def SetTestDeviceMode(mode_pattern):
	if mode_pattern & 8:
		gpio.output(17,gpio.HIGH)
	else:
		gpio.output(17,gpio.LOW)
	if mode_pattern & 4:
		gpio.output(18,gpio.HIGH)
	else:
		gpio.output(18,gpio.LOW)
	if mode_pattern & 2:
		gpio.output(27,gpio.HIGH)
	else:
		gpio.output(27,gpio.LOW)
	if mode_pattern & 1:
		gpio.output(22,gpio.HIGH)
	else:
		gpio.output(22,gpio.LOW)
	return

def SetStandardDeviceMode(mode_pattern):
	if mode_pattern & 8:
		gpio.output(24,gpio.HIGH)
	else:
		gpio.output(24,gpio.LOW)
	if mode_pattern & 4:
		gpio.output(25,gpio.HIGH)
	else:
		gpio.output(25,gpio.LOW)
	if mode_pattern & 2:
		gpio.output(5,gpio.HIGH)
	else:
		gpio.output(5,gpio.LOW)
	if mode_pattern & 1:
		gpio.output(6,gpio.HIGH)
	else:
		gpio.output(6,gpio.LOW)
	return

def AssertTestTXButton():
	gpio.output(23,gpio.HIGH)
	return

def ReleaseTestTXButton():
	gpio.output(23,gpio.LOW)
	return

if sys.version_info < (3, 0):
	print("Python version should be 3.x, exiting")
	sys.exit(1)

gpio.setmode(gpio.BCM)

SetupGPIO()

for mode in range(16):
	SetTestDeviceMode(mode)
	SetStandardDeviceMode(mode)
	time.sleep(2)

	AssertTestTXButton()
	time.sleep(.1)
	ReleaseTestTXButton()
	time.sleep(5)
gpio.cleanup()

sys.exit(0)
