# validate_serial_functions.py
# Python3
# Support validate.py
# Nino Carrillo
# 20 Jan 2024

import serial

def HandleSerialData(data):
	print(data)
	
def ReadFromPort(serial_port):
	while serial_port.isOpen():
		input_data = serial_port.read(1)
		if input_data:
			HandleSerialData(input_data)

def OpenPort(port_name, port_baud, exit_error):
	try:
		port_object = serial.Serial(port_name, baudrate=port_baud, bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, timeout=3)
	except:
		print(f"Unable to open serial port {port_name}")
		sys.exit(exit_error)
	return port_object