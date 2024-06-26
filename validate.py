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
soundcard_volume = "80%"
path_to_test_audio = "/home/pi/github/modem-test-audio/"
test_callsign = "0TEST0-5"
standard_callsign = "STNDRD-7"
reset_time = 2.0
pass_text = "......................................................................PASS"
fail_text = "......................................................................FAIL"

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

mode_bit_rate_list = [ 9600,
					9600,
					9600,
					4800,
					4800,
					2400,
					1200,
					1200,
					300,
					600,
					1200,
					2400,
					300,
					300,
					300,
					1200 ]

awgn_track_list = ["4_multiple_awgn/GFSK_9600_AX25_50b_50m_a1.wav",
			"4_multiple_awgn/GFSK_9600_IL2Pc_50b_50m_a1.wav",
			"4_multiple_awgn/GFSK_9600_IL2Pc_50b_50m_a1.wav",
			"4_multiple_awgn/GFSK_4800_IL2Pc_50b_50m_a2.wav",
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

burst_track_list = ["2_burst/GFSK_9600_AX25_255b_10x.wav",
			"2_burst/GFSK_9600_IL2P_255b_10x.wav",
			"2_burst/GFSK_9600_IL2Pc_255b_10x.wav",
			"2_burst/GFSK_4800_IL2P_255b_10x.wav",
			"2_burst/GFSK_4800_IL2Pc_255b_10x.wav",
			"2_burst/DAPSK_2400_IL2P_50b_10x.wav",
			"2_burst/AFSK_1200_AX25_50b_10x.wav",
			"2_burst/AFSK_1200_IL2P_50b_10x.wav",
			"2_burst/BPSK_300_IL2Pc_50b_10x.wav",
			"2_burst/QPSK_600_IL2Pc_50b_10x.wav",
			"2_burst/BPSK_1200_IL2Pc_50b_10x.wav",
			"2_burst/QPSK_2400_IL2Pc_50b_10x.wav",
			"2_burst/AFSK_300_AX25_50b_10x.wav",
			"2_burst/AFSK_300_IL2P_50b_10x.wav",
			"2_burst/AFSK_300_IL2Pc_50b_10x.wav",
			"2_burst/BPSK_1200_IL2P_50b_10x.wav" ]

beacon_mode_list = [ 6, # 0000 GFSK 9600 AX.25
					6, #  0001 GFSK 9600 IL2P
					6, #  0010 GFSK 9600 IL2Pc
					6, #  0011 GFSK 4800 IL2P
					6, #  0100 GFSK 4800 IL2Pc
					6, #  0101 DAPSK 2400 IL2P
					-1, # 0110 AFSK 1200 AX.25
					6, #  0111 AFSK 1200 IL2P
					12, # 1000 BPSK 300 IL2Pc
					12, # 1001 QPSK 600 IL2Pc
					12, # 1010 BPSK 1200 IL2Pc
					12, # 1011 QPSK 2400 IL2Pc
					-1, # 1100 AFSK 300 AX.25
					-1, # 1101 AFSK 300 IL2P
					-1, # 1110 AFSK 300 IL2Pc
					12 ] # 1111 BPSK 1200 IL2P

if sys.version_info < (3, 0):
	print("Python version should be 3.x, exiting")
	sys.exit(1)

"""
Initialize Raspberry Pi GPIO for manipulation of MODE switches on TEST device
and STANDARD device.
"""
print(f"{time.asctime()} Initializing Raspberry Pi GPIO.")
vgpio.SetupGPIO()
time.sleep(reset_time)

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
# Set the mode switches
mode = 1
vgpio.SetTestDeviceMode(mode)
vgpio.SetStandardDeviceMode(mode)
# Wait for device reset
time.sleep(reset_time)
# Clear serial queues
vthread.ClearQueue(standard_serial_queue)
vthread.ClearQueue(test_serial_queue)
packet = vpacket.GenerateUIPacket(test_callsign, standard_callsign, "nothing to see here ", 50)
tx_metadata = vpacket.GetFrameMeta(packet)
print(f"{time.asctime()} Packet CRC is {vpacket.GetCRC(packet)}.")
#print(f"{time.asctime()} Packet payload: {str(tx_metadata['Payload'])}")
test_serial_port_obj.write(vpacket.EncodeKISSFrame(0,packet))
time.sleep(1)
count = 0
start_time = time.time()
while not standard_serial_queue.empty():
	packet = standard_serial_queue.get()
	count += 1
	tx_metadata = vpacket.GetFrameMeta(packet)
	print(f'{time.asctime()} STANDARD device heard packet from {tx_metadata["SOURCE"]} to {tx_metadata["DEST"]} CRC {tx_metadata["CRC"]}.')
	#print(f"{time.asctime()} Packet payload: {str(tx_metadata['Payload'])}")

"""
Check the TEST_TX button transmits a packet with the correct callsign.
"""
print(f"{time.asctime()} Testing OWN DEVICE CALLSIGN ADOPTION.")
# Set the mode switches
mode = 1
vgpio.SetTestDeviceMode(mode)
vgpio.SetStandardDeviceMode(mode)
# Wait for device reset
time.sleep(reset_time)
# Clear serial queues
vthread.ClearQueue(standard_serial_queue)
vthread.ClearQueue(test_serial_queue)
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
	#print(f"{time.asctime()} Packet payload: {str(rx_metadata['Payload'])}")
try:
	if rx_metadata['SOURCE'][:-2] == tx_metadata['SOURCE'][:-2]:
		print(f"{time.asctime()}{pass_text}")
	else:
		print(f"{time.asctime()}{fail_text}")
except:
		print(f"{time.asctime()}{fail_text}")

"""
Check that the TEST_TX button sends a packet to the host over USB, and loopback works in each mode.
"""
print(f"{time.asctime()} Testing USB TEST PACKET and LOOPBACK TEST in each mode.")
for mode in range(16):
	print(mode_list[mode])
	# Set the mode switches
	vgpio.SetTestDeviceMode(mode)
	vgpio.SetStandardDeviceMode(mode)
	# Wait for device reset
	time.sleep(reset_time)
	# Clear serial queues
	vthread.ClearQueue(standard_serial_queue)
	vthread.ClearQueue(test_serial_queue)
	repeat_count = 3
	for repeat in range(repeat_count):
		vgpio.AssertTestTXButton()
		time.sleep(1)
		vgpio.ReleaseTestTXButton()
		time.sleep(1 + (100 * 8 / mode_bit_rate_list[mode]))
	count = 0
	while not test_serial_queue.empty():
		packet = test_serial_queue.get()
		count += 1
		rx_metadata = vpacket.GetFrameMeta(packet)
		print(f'{time.asctime()} TEST device heard packet from {rx_metadata["SOURCE"]} to {rx_metadata["DEST"]} CRC {rx_metadata["CRC"]}.')
		#print(f"{time.asctime()} Packet payload: {str(rx_metadata['Payload'])}")
	if count > repeat_count:
		print(f"{time.asctime()}{pass_text}")
	else:
		print(f"{time.asctime()}{fail_text}")


"""
Check BURST track performance.
"""
print(f"{time.asctime()} Testing BURST TRACK PERFORMANCE.")
vthread.ClearQueue(standard_serial_queue)
vthread.ClearQueue(test_serial_queue)
subprocess.run(["amixer", "sset", "'Master'", f"{soundcard_volume}"], stdout=subprocess.DEVNULL)
for mode in range(16):
	print(f"Playing {burst_track_list[mode]} for mode {mode_list[mode]}.")
	# Set the mode switches
	vgpio.SetTestDeviceMode(mode)
	vgpio.SetStandardDeviceMode(mode)
	# Wait for device reset
	time.sleep(reset_time)
	# Empty the serial queues
	while not test_serial_queue.empty():
		packet = test_serial_queue.get()
	while not standard_serial_queue.empty():
		packet = standard_serial_queue.get()
	# Play the appropriate track:
	subprocess.run(["aplay", "-q", path_to_test_audio + burst_track_list[mode]], stdout=subprocess.DEVNULL)
	time.sleep(1)
	# Count the received packets from each device:
	test_count = 0
	standard_count = 0
	while not test_serial_queue.empty():
		packet = test_serial_queue.get()
		test_count += 1
	print(f"Test device heard {test_count} packets.")
	while not standard_serial_queue.empty():
		packet = standard_serial_queue.get()
		standard_count += 1
	print(f"Standard device heard {standard_count} packets.")
	if test_count > (standard_count - ((test_count + standard_count) * 0.07)):
		print(f"{time.asctime()}{pass_text}")
	else:
		print(f"{time.asctime()}{fail_text}")

"""
Check AWGN track performance.
"""
print(f"{time.asctime()} Testing AWGN TRACK PERFORMANCE.")
vthread.ClearQueue(standard_serial_queue)
vthread.ClearQueue(test_serial_queue)
subprocess.run(["amixer", "sset", "'Master'", f"{soundcard_volume}"], stdout=subprocess.DEVNULL)
for mode in range(16):
	print(f"Playing {awgn_track_list[mode]} for mode {mode_list[mode]}.")
	# Set the mode switches
	vgpio.SetTestDeviceMode(mode)
	vgpio.SetStandardDeviceMode(mode)
	# Wait for device reset
	time.sleep(reset_time)
	# Empty the serial queues
	while not test_serial_queue.empty():
		packet = test_serial_queue.get()
	while not standard_serial_queue.empty():
		packet = standard_serial_queue.get()
	# Play the appropriate track:
	subprocess.run(["aplay", "-q", path_to_test_audio + awgn_track_list[mode]], stdout=subprocess.DEVNULL)
	time.sleep(1)
	# Count the received packets from each device:
	test_count = 0
	standard_count = 0
	while not test_serial_queue.empty():
		packet = test_serial_queue.get()
		test_count += 1
	print(f"Test device heard {test_count} packets.")
	while not standard_serial_queue.empty():
		packet = standard_serial_queue.get()
		standard_count += 1
	print(f"Standard device heard {standard_count} packets.")
	if test_count > (standard_count - ((test_count + standard_count) * 0.07)):
		print(f"{time.asctime()}{pass_text}")
	else:
		print(f"{time.asctime()}{fail_text}")



"""
Check BEACON PACKET function.
"""
print(f"{time.asctime()} Testing BEACON FUNCTION in all applicable modes.")
vthread.ClearQueue(standard_serial_queue)
vthread.ClearQueue(test_serial_queue)
for mode in range(16):
	if beacon_mode_list[mode] > 0:
		print(f"{time.asctime()} Mode {mode_list[mode]}.")
		vgpio.SetTestDeviceMode(mode)
		vgpio.SetStandardDeviceMode(beacon_mode_list[mode])
		time.sleep(reset_time)
		test_serial_port_obj.write(vpacket.EncodeKISSFrame(0x09, [0xF0, 0x01])) # Set beacon interval to 1 minute
		packet = vpacket.GenerateUIPacket(test_callsign, standard_callsign, "nothing to see here ", 0)
		#tx_metadata = vpacket.GetFrameMeta(packet)
		#print(f"{time.asctime()} Packet CRC is {vpacket.GetCRC(packet)}.")
		#print(f"{time.asctime()} Packet payload: {str(tx_metadata['Payload'])}")
		test_serial_port_obj.write(vpacket.EncodeKISSFrame(0,packet))
		time.sleep(60)
		test_serial_port_obj.write(vpacket.EncodeKISSFrame(0,packet))
		time.sleep(60)
		count = 0
		while not standard_serial_queue.empty():
			packet = standard_serial_queue.get()
			rx_metadata = vpacket.GetFrameMeta(packet)
			print(f'{time.asctime()} STANDARD device heard packet from {rx_metadata["SOURCE"]} to {rx_metadata["DEST"]} CRC {rx_metadata["CRC"]}.')
			print(f"{time.asctime()} Packet payload: {str(rx_metadata['Payload'])}")
			count += 1
		print(f"Standard device heard {count} packets.")
		if count > 0:
			print(f"{time.asctime()}{pass_text}")
		else:
			print(f"{time.asctime()}{fail_text}")

"""
Check BEACON PACKET DISABLE function.
"""
print(f"{time.asctime()} Testing BEACON DISABLE FUNCTION.")
vthread.ClearQueue(standard_serial_queue)
vthread.ClearQueue(test_serial_queue)
mode = 1
print(f"{time.asctime()} Mode {mode_list[mode]}.")
vgpio.SetTestDeviceMode(mode)
vgpio.SetStandardDeviceMode(beacon_mode_list[mode])
time.sleep(reset_time)
test_serial_port_obj.write(vpacket.EncodeKISSFrame(0x09, [0xF0, 0x00])) # Set beacon interval to off
packet = vpacket.GenerateUIPacket(test_callsign, standard_callsign, "nothing to see here ", 0)
#tx_metadata = vpacket.GetFrameMeta(packet)
#print(f"{time.asctime()} Packet CRC is {vpacket.GetCRC(packet)}.")
#print(f"{time.asctime()} Packet payload: {str(tx_metadata['Payload'])}")
test_serial_port_obj.write(vpacket.EncodeKISSFrame(0,packet))
time.sleep(60)
test_serial_port_obj.write(vpacket.EncodeKISSFrame(0,packet))
time.sleep(60)
count = 0
while not standard_serial_queue.empty():
	packet = standard_serial_queue.get()
	rx_metadata = vpacket.GetFrameMeta(packet)
	print(f'{time.asctime()} STANDARD device heard packet from {rx_metadata["SOURCE"]} to {rx_metadata["DEST"]} CRC {rx_metadata["CRC"]}.')
	print(f"{time.asctime()} Packet payload: {str(rx_metadata['Payload'])}")
	count += 1
print(f"Standard device heard {count} packets.")
if count > 0:
	print(f"{time.asctime()}{fail_text}")
else:
	print(f"{time.asctime()}{pass_text}")

"""
Check TARPNstat auto host meta-frame over USB
"""
print(f"{time.asctime()} Testing TARPNstat auto host meta-frame.")
vthread.ClearQueue(standard_serial_queue)
vthread.ClearQueue(test_serial_queue)
mode = 1
print(f"{time.asctime()} Mode {mode_list[mode]}.")
vgpio.SetTestDeviceMode(mode)
vgpio.SetStandardDeviceMode(beacon_mode_list[mode])
time.sleep(reset_time)
packet = vpacket.GenerateUIPacket(test_callsign, standard_callsign, " TARPNstat", 0)
metadata = vpacket.GetFrameMeta(packet)
print(f'{time.asctime()} TEST device sending {metadata["SOURCE"]} to {metadata["DEST"]} CRC {metadata["CRC"]}.')
print(f"{time.asctime()} Packet payload: {str(metadata['Payload'])}")
test_serial_port_obj.write(vpacket.EncodeKISSFrame(0,packet))
time.sleep(1)
count = 0
while not test_serial_queue.empty():
	packet = test_serial_queue.get()
	metadata = vpacket.GetFrameMeta(packet)
	print(f'{time.asctime()} TEST device heard packet from {metadata["SOURCE"]} to {metadata["DEST"]} CRC {metadata["CRC"]}.')
	print(f"{time.asctime()} Packet payload: {str(metadata['Payload'])}")
	count += 1
print(f"TEST device heard {count} packets.")
if count > 0:
	print(f"{time.asctime()}{pass_text}")
else:
	print(f"{time.asctime()}{fail_text}")





test_serial_port_obj.close()
standard_serial_port_obj.close()
test_serial_thread.join()
standard_serial_thread.join()

vgpio.Cleanup()

sys.exit(0)
