# validate_packet_functions.py
# Python3
# Support validate.py
# Nino Carrillo
# 20 Jan 2024

import random
import crc

def GetCRC(packet):
	return crc.CalcCRC16(packet)

def GetFrameMeta(packet):
	this = {}
	this['CRC'] = crc.CalcCRC16(packet)
	count = len(packet)
	index = 0
	if (count > 14):
		valid_header = 1
		address_extension_bit = 0
		index = 0
		subfield_character_index = 0
		subfield_index = 0
		while address_extension_bit == 0:
			working_character = int(packet[index])
			if (working_character & 0b1) == 1:
				address_extension_bit = 1
			working_character = working_character >> 1
			subfield_character_index = subfield_character_index + 1
			if (subfield_character_index == 1):
				buffer = ""
				if (subfield_index == 0):
					#print("To:", end='')
					tag = "DEST"
				elif (subfield_index == 1):
					tag = "SOURCE"
				else:
					tag = "VIA" + str(subfield_index - 1)
			if subfield_character_index < 7:
				# This is a callsign character
				if (working_character != 0) and (working_character != 0x20):
					buffer += chr(working_character)
			elif subfield_character_index == 7:
				# This is the SSID characters
				# Get bits
				buffer += '-'
				buffer += chr((working_character & 0b1111) + 0x30)
				if (working_character & 0b10000000):
					# C or H bit is set
					buffer += '*'
				# This field is complete
				this[f'{tag}'] = buffer
				subfield_character_index = 0
				subfield_index = subfield_index + 1
			index = index + 1
			if index > count:
				address_extension_bit = 1
		# Control and PID fields
		working_character = packet[index]
		this['Control'] = working_character
		poll_final_bit = (working_character & 0x10) >> 4
		# determine what type of packet this is
		if (working_character & 1) == 1:
			# either a Supervisory or Unnumbered packet
			frame_type = working_character & 3
		else:
			# Information packet
			frame_type = 0
			ax25_ns = (working_character >> 1) & 7
			ax25_nr = (working_character >> 5) & 7

		if frame_type == 1:
			# Supervisory packet
			ax25_nr = (working_character >> 5) & 7

		if frame_type == 3:
			# Unnumbered packet, determine what type
			ax25_u_control_field_type = working_character & 0xEF
		else:
			ax25_u_control_field_type = 0

		if (ax25_u_control_field_type == 0x6F):
			buffer = "SABME"
		elif (ax25_u_control_field_type == 0x2F):
			buffer = "SABM"
		elif (ax25_u_control_field_type == 0x43):
			buffer = "DISC"
		elif (ax25_u_control_field_type == 0x0F):
			buffer = "DM"
		elif (ax25_u_control_field_type == 0x63):
			buffer = "UA"
		elif (ax25_u_control_field_type == 0x87):
			buffer = "FRMR"
		elif (ax25_u_control_field_type == 0x03):
			buffer = "UI"
		elif (ax25_u_control_field_type == 0xAF):
			buffer = "XID"
		elif (ax25_u_control_field_type == 0xE3):
			buffer = "TEST"
		this['ControlString'] = buffer

		if (frame_type == 0) or (ax25_u_control_field_type == 3):
			# This is an Information packet, or an Unnumbered Information packet, so
			# there is a PID byte.
			index = index + 1
			working_character = packet[index]
			this['PID'] = working_character
			if (working_character == 1):
				buffer = "ISO 8208"
			if (working_character == 6):
				buffer = "Compressed TCP/IP"
			if (working_character == 7):
				buffer = "Uncompressed TCP/IP"
			if (working_character == 8):
				buffer = "Segmentation Fragment"
			if (working_character == 0xC3):
				buffer = "TEXNET"
			if (working_character == 0xC4):
				buffer = "Link Quality Protocol"
			if (working_character == 0xCA):
				buffer = "Appletalk"
			if (working_character == 0xCC):
				buffer = "ARPA Internet Protocol"
			if (working_character == 0xCD):
				pbuffer = "ARPA Address Resolution"
			if (working_character == 0xCF):
				buffer = "TheNET (NET/ROM)"
			if (working_character == 0xF0):
				buffer = "No Layer 3"
			if (working_character == 0xFF):
				buffer = "Escape"
			this['PIDString'] = buffer

		index = index + 1
		this['Payload'] = bytearray(packet[index:])
	return this


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

def EncodeKISSFrame(packet):
	FESC = int(0xDB).to_bytes(1,'big')
	FEND = int(0xC0).to_bytes(1,'big')
	TFESC = int(0xDD).to_bytes(1,'big')
	TFEND = int(0xDC).to_bytes(1,'big')
	KISS_PORT = 0
	KISS_COMMAND = 0
	KISS_TYPE_ID = (KISS_PORT * 16) + KISS_COMMAND
	KISS_TYPE_ID = KISS_TYPE_ID.to_bytes(1,'big')
	frame_index = 0
	kiss_output_frame = bytearray()
	while(frame_index < len(packet)):
		kiss_byte = packet[frame_index]
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

def GenerateUIPacket(source_callsign_string, dest_callsign_string, payload, length):
	source_callsign = StringCallsignToArray(source_callsign_string)
	dest_callsign = StringCallsignToArray(dest_callsign_string)

	# Assemble packet:
	packet = bytearray()
	# Add destination callsign, shifted left one bit:
	for j in range(6):
		packet.extend((dest_callsign[j]<<1).to_bytes(1,'big'))
	# Add destination SSID with CRR bits set
	packet.extend((((dest_callsign[6] & 0xF)<<1) | 0xE0).to_bytes(1,'big'))
	# Add source callsign, shifted left one bit:
	for k in range(6):
		packet.extend((source_callsign[k]<<1).to_bytes(1,'big'))
	# Add source SSID with Address Extension Bit and RR bits:
	packet.extend((((source_callsign[6] & 0xF) << 1) | 0x61).to_bytes(1,'big'))

	# Add Control field for UI:
	packet.extend((0x03).to_bytes(1,'big'))
	# Add PID for No Layer 3:
	packet.extend((0xF0).to_bytes(1,'big'))

	# convert payload string to byte array
	payload = bytes(payload, 'UTF-8')
	for character in payload:
		packet.extend(character.to_bytes(1, 'big'))

	random_count = length - len(payload)
	if random_count > 0:
		for j in range(0, length):
			rand = random.randint(32,126)
			packet.extend(bytearray(rand.to_bytes(1,'big')))

	return packet
