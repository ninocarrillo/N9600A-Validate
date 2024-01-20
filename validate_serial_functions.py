# validate_serial_functions.py
# Python3
# Support validate.py
# Nino Carrillo
# 20 Jan 2024

import serial

def ReadFromPort(serial_port, queue):
	kiss_state = "non-escaped"
	kiss_frame = []
	frame_count = 0
	while serial_port.isOpen():
		try:
			input_data = serial_port.read(1)
			if input_data:
				if kiss_state == "non-escaped":
					if ord(input_data) == 0xDB: # FESC
						kiss_state = "escaped"
					elif ord(input_data) == 0xC0: # FEND
						if len(kiss_frame) > 0:
							frame_count += 1
							queue.put(kiss_frame, frame_count)
							kiss_frame = []
						else:
							kiss_frame = []
					else:
						kiss_frame.append(ord(input_data))
				elif kiss_state == "escaped":
					if ord(input_data) == 0xDD: # TFESC
						kiss_frame.append(0xDB) # FESC
						kiss_state = "non-escaped"
					elif ord(input_data) == 0xDC: # TFEND
						kiss_frame.append(0xC0) # FEND
						kiss_state = "non-escaped"

		except:
			break

def OpenPort(port_name, port_baud, exit_error):
	try:
		port_object = serial.Serial(port_name, baudrate=port_baud, bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, timeout=3)
	except:
		print(f"Unable to open serial port {port_name}")
		sys.exit(exit_error)
	return port_object
