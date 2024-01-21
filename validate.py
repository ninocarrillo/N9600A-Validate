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
import crc

test_serial_port = "/dev/ttyACM0"
test_serial_port_baud = "57600"
standard_serial_port = "/dev/ttyACM1"
standard_serial_port_baud = "57600"
path_to_test_audio = "/home/pi/github/modem-test-audio/"
test_callsign = "0TEST0-5"
standard_callsign = "STNDRD-7"
pass_text = "...................................PASS"
fail_text = "...................................FAIL"

mode_list = ["GFSK_9600_AX25",
			"GFSK_9600_IL2P",
			"GFSK_9600_IL2Pc",
			"GFSK_4800_IL2P",
			"GFSK_4800_IL2Pc",
			"DAPSK_2400_IL2P",
			"AFSK_1200_AX25",
			"AFSK_1200_IL2P",
			"BPSK_300_IL2Pc",
			"QPSK_600_IL2Pc",
			"BPSK_1200_IL2Pc",
			"QPSK_2400_IL2Pc",
			"AFSK_300_AX25",
			"AFSK_300_IL2P",
			"AFSK_300_IL2Pc",
			"BPSK_1200_IL2P" ]
			
awgn_track_list = ["4_multiple_awgn/GFSK_9600_AX25_50b_50m_a1.wav",
			"4_multiple_awgn/GFSK_9600_IL2P_50b_50m_a1.wav",
			"4_multiple_awgn/GFSK_9600_IL2Pc_50b_50m_a1.wav",
			"4_multiple_awgn/GFSK_4800_IL2P_50b_50m_a2.wav",
			"4_multiple_awgn/GFSK_4800_IL2Pc_50b_50m_a2.wav",
			"4_multiple_awgn/DAPSK_2400_IL2P_50b_50m_a2.wav",
			"4_multiple_awgn/AFSK_1200_AX25_50b_50m_a3.wav",
			"4_multiple_awgn/AFSK_1200_IL2P_50b_50m_a3.wav",
			"4_multiple_awgn/BPSK_300_IL2Pc_50b_50m_a4.wav",
			"4_multiple_awgn/QPSK_600_IL2Pc_50b_50m_a4.wav",
			"4_multiple_awgn/BPSK_1200_IL2Pc_50b_50m_a3.wav",
			"4_multiple_awgn/QPSK_2400_IL2Pc_50b_50m_a5.wav",
			"4_multiple_awgn/AFSK_300_AX25_50b_50m_a4.wav",
			"4_multiple_awgn/AFSK_300_IL2P_50b_50m_a4.wav",
			"4_multiple_awgn/AFSK_300_IL2Pc_50b_50m_a4.wav",
			"4_multiple_awgn/BPSK_1200_IL2P_50b_50m_a3.wav" ]

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

"""
Generate a UI frame to assign callsign to TEST device.
"""
print(f"{time.asctime()} Sending a UI Packet from {test_callsign} to {standard_callsign} to set TEST device callsign.")
packet = vpacket.GenerateUIPacket(test_callsign, standard_callsign, 50)
tx_metadata = vpacket.GetFrameMeta(packet)
print(f"{time.asctime()} Packet CRC is {vpacket.GetCRC(packet)}.")
print(f"{time.asctime()} Packet payload: {str(tx_metadata['Payload'])}")
test_serial_port_obj.write(vpacket.EncodeKISSFrame(packet))
time.sleep(1)
count = 0
start_time = time.time()
while not standard_serial_queue.empty():
	packet = standard_serial_queue.get()
	count += 1
	tx_metadata = vpacket.GetFrameMeta(packet)
	print(f'{time.asctime()} STANDARD device heard packet from {tx_metadata["SOURCE"]} to {tx_metadata["DEST"]} CRC {tx_metadata["CRC"]}.')
	print(f"{time.asctime()} Packet payload: {str(tx_metadata['Payload'])}")


"""
Check that the TEST_TX button generates a packet with the correct callsign.
"""
print(f"{time.asctime()} Testing OWN DEVICE CALLSIGN ADOPTION.")
vgpio.AssertTestTXButton()
time.sleep(.1)
vgpio.ReleaseTestTXButton()
time.sleep(1)
count = 0
while not standard_serial_queue.empty():
	packet = standard_serial_queue.get()
	count += 1
	rx_metadata = vpacket.GetFrameMeta(packet)
	print(f'{time.asctime()} STANDARD device heard packet from {rx_metadata["SOURCE"]} to {rx_metadata["DEST"]} CRC {rx_metadata["CRC"]}.')
	print(f"{time.asctime()} Packet payload: {str(rx_metadata['Payload'])}")
try:
	if rx_metadata['SOURCE'][:-2] == tx_metadata['SOURCE'][:-2]:
		print(f"{time.asctime()}{pass_text}")
	else:
		print(f"{time.asctime()}{fail_text}")
except:
		print(f"{time.asctime()}{fail_text}")




vgpio.SetTestDeviceMode(4)
vgpio.SetStandardDeviceMode(4)
while not test_serial_queue.empty():
	packet = test_serial_queue.get()
time.sleep(2)
subprocess.run(["aplay", path_to_test_audio + "2_burst/GFSK_4800_IL2Pc_50b_10x.wav"])

#vthread.popen_and_call(vthread.end_do_nothing, ["aplay", "/home/pi/github/modem-test-audio/2_burst/GFSK_4800_IL2Pc_50b_10x.wav"])



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
