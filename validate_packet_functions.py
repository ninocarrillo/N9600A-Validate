# validate_packet_functions.py
# Python3
# Support validate.py
# Nino Carrillo
# 20 Jan 2024

def StringCallsignToArray(input_string):
	output = [0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0]
	callsign_length = 0
	ssid_digits = 0
	ssid = [0,0]
	currently_reading = 'callsign'
	input_string = input_string.upper()
	input_string = bytes(input_string, 'UTF-8')
	for character in input_string:
		if currently_reading == 'callsign':
			if character == bytes('-', 'UTF-8')[0]:
				currently_reading = 'ssid'
			else:
				output[callsign_length] = int(character)
				callsign_length += 1
				if callsign_length == 6:
					currently_reading = 'hyphen'
				# print(output)
		elif currently_reading == 'hyphen':
			if character != bytes('-', 'UTF-8')[0]:
				pass
			currently_reading = 'ssid'
		elif currently_reading == 'ssid':
			ssid[ssid_digits] = character - bytes('0', 'UTF-8')[0]
			ssid_digits += 1
			# print(ssid)
	if ssid_digits == 1:
		ssid = ssid[0]
	elif ssid_digits == 2:
		ssid = ssid[0] * 10 + ssid[1]
	else:
		ssid = 0
	if ssid > 16:
		ssid = 16
	if ssid < 0:
		ssid = 0
	output[6] = ssid
	return output

def GenerateUIPacket(source_callsign_string, dest_callsign_string, length):
	source_callsign = StringCallsignToArray(source_callsign_string)
	dest_callsign = StringCallsignToArray(dest_callsign_string)
	FESC = int(0xDB).to_bytes(1,'big')
	FEND = int(0xC0).to_bytes(1,'big')
	TFESC = int(0xDD).to_bytes(1,'big')
	TFEND = int(0xDC).to_bytes(1,'big')
	KISS_PORT = 0
	KISS_COMMAND = 0
	KISS_TYPE_ID = (KISS_PORT * 16) + KISS_COMMAND
	KISS_TYPE_ID = KISS_TYPE_ID.to_bytes(1,'big')

	# Assemble KISS frame:
	kiss_frame = bytearray()
	# Add destination callsign, shifted left one bit:
	for j in range(6):
		kiss_frame.extend((dest_callsign[j]<<1).to_bytes(1,'big'))
	# Add destination SSID with CRR bits set
	kiss_frame.extend((((dest_callsign[6] & 0xF)<<1) | 0xE0).to_bytes(1,'big'))
	# Add source callsign, shifted left one bit:
	for k in range(6):
		kiss_frame.extend((source_callsign[k]<<1).to_bytes(1,'big'))
	# Add source SSID with Address Extension Bit and RR bits:
	kiss_frame.extend((((source_callsign[6] & 0xF) << 1) | 0x61).to_bytes(1,'big'))

	# Add Control field for UI:
	kiss_frame.extend((0x03).to_bytes(1,'big'))
	# Add PID for No Layer 3:
	kiss_frame.extend((0xF0).to_bytes(1,'big'))

	for j in range(0, length):
		rand = random.randint(32,126)
		kiss_frame.extend(bytearray(rand.to_bytes(1,'big')))

	print(f'\nFrame {i+1} CRC value: {crc.CalcCRC16(kiss_frame)}')

	frame_index = 0
	kiss_output_frame = bytearray()
	while(frame_index < len(kiss_frame)):
		kiss_byte = kiss_frame[frame_index]
		if kiss_byte.to_bytes(1,'big') == FESC:
			kiss_output_frame.extend(FESC)
			kiss_output_frame.extend(TFESC)
		elif kiss_byte.to_bytes(1, 'big') == FEND:
			kiss_output_frame.extend(FESC)
			kiss_output_frame.extend(TFEND)
		else:
			kiss_output_frame.extend(kiss_byte.to_bytes(1, 'big'))
		frame_index += 1
	kiss_output_frame = bytearray(FEND) + bytearray(KISS_TYPE_ID) + kiss_output_frame + bytearray(FEND)
	return kiss_output_frame
