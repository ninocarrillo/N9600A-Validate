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

import sys
import time
import subprocess
import threading
import queue
import validate_gpio_functions as vgpio
import validate_threading_functions as vthread
import validate_serial_functions as vserial
import validate_packet_functions as vpacket

test_serial_port = "/dev/ttyACM0"
test_serial_port_baud = "57600"
standard_serial_port = "/dev/ttyACM1"
standard_serial_port_baud = "57600"
path_to_test_audio = "/home/pi/github/modem-test-audio/"
test_callsign = "0TEST0"
standard_callsign = "STNDRD"

if sys.version_info < (3, 0):
	print("Python version should be 3.x, exiting")
	sys.exit(1)

"""
Initialize Raspberry Pi GPIO for manipulation of MODE switches on TEST device
and STANDARD device.
"""
print(f"{time.asctime()} Initializing Raspberry Pi GPIO.")
vgpio.SetupGPIO()
time.sleep(2)
print(f"{time.asctime()} Done.")

"""
Open serial port for TEST device and STANDARD device.
Use threading to read serial data and parse KISS frames outside main thread.
"""
print(f"{time.asctime()} Opening TEST and STANDARD device serial ports, starting KISS reader threads.")
test_serial_port_obj = vserial.OpenPort(test_serial_port, test_serial_port_baud, 3)
standard_serial_port_obj = vserial.OpenPort(standard_serial_port, standard_serial_port_baud, 4)
test_serial_queue = queue.Queue()
test_serial_thread = threading.Thread(target=vserial.ParseKISSFromPort, args=([test_serial_port_obj, test_serial_queue]))
test_serial_thread.start()
standard_serial_queue = queue.Queue()
standard_serial_thread = threading.Thread(target=vserial.ParseKISSFromPort, args=([standard_serial_port_obj, standard_serial_queue]))
standard_serial_thread.start()
print(f"{time.asctime()} Done.")

"""
Generate a UI frame to assign callsign to TEST device.
"""
print(f"{time.asctime()} Sending a UI Packet from {test_callsign} to {standard_callsign} to set TEST device callsign.")
test_serial_port_obj.write(vpacket.GenerateUIPacket(test_callsign, standard_callsign, 50))
time.sleep(1)
print(f"{time.asctime()} Done.")
count = 0
start_time = time.time()
while not standard_serial_queue.empty():
	standard_serial_queue.get()
	count += 1
	print(test_serial_queue.get())
	if time.time() - start_time > 2:
		break
print(f"STANDARD device heard {count} frames.")

vgpio.SetTestDeviceMode(4)
vgpio.SetStandardDeviceMode(4)
subprocess.run(["aplay", path_to_test_audio + "2_burst/GFSK_4800_IL2Pc_50b_10x.wav"])

#vthread.popen_and_call(vthread.end_do_nothing, ["aplay", "/home/pi/github/modem-test-audio/2_burst/GFSK_4800_IL2Pc_50b_10x.wav"])

time.sleep(2)

count = 0
while not test_serial_queue.empty():
	test_serial_queue.get()
	count += 1
	#print(test_serial_queue.get())
print(f"Test device heard {count} frames.")

for mode in range(16):
	vgpio.SetTestDeviceMode(mode)
	vgpio.SetStandardDeviceMode(mode)
	print(f"Generating test packet in MODE {format(mode, '04b')}")
	time.sleep(2)

	vgpio.AssertTestTXButton()
	time.sleep(.1)
	vgpio.ReleaseTestTXButton()
	time.sleep(5)


count = 0
while not standard_serial_queue.empty():
	standard_serial_queue.get()
	count += 1


test_serial_port_obj.close()
standard_serial_port_obj.close()
test_serial_thread.join()
standard_serial_thread.join()

print(f"Standard device heard {count} frames.")

vgpio.Cleanup()

sys.exit(0)
