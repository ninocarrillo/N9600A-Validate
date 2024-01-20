# validate_packet_functions.py
# Python3
# Support validate.py
# Nino Carrillo
# 20 Jan 2024

import random
import crc

def GetCRCFromKISS(frame):
	return crc.CalcCRC16(frame[1:])

def GetKISSFrameMeta(frame):
	this = {}
	this['CRC'] = crc.CalcCRC16(frame[1:])
	count = len(frame)
	index = 0
	if (count > 15):
		valid_header = 1
		address_extension_bit = 0
		index = 1
		subfield_character_index = 0
		subfield_index = 0
		# print("- AX.25 Decode:")
		# Print address information
		while address_extension_bit == 0:
			working_character = int(frame[index])
			if (working_character & 0b1) == 1:
				address_extension_bit = 1
			working_character = working_character >> 1
			subfield_character_index = subfield_character_index + 1
			if (subfield_character_index == 1):
				buffer = ""
				if (subfield_index == 0):
					#print("To:", end='')
					tag = "SOURCE"
				elif (subfield_index == 1):
					tag = "DEST"
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
				buffer += chr(working_character & 0b1111)
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
		working_character = frame[index]
		print(", Control: ", end='')
		print(f'{hex(working_character)} ', end='')
		poll_final_bit = (working_character & 0x10) >> 4
		# determine what type of frame this is
		if (working_character & 1) == 1:
			# either a Supervisory or Unnumbered frame
			frame_type = working_character & 3
		else:
			# Information frame
			frame_type = 0
			ax25_ns = (working_character >> 1) & 7
			ax25_nr = (working_character >> 5) & 7

		if frame_type == 1:
			# Supervisory frame
			ax25_nr = (working_character >> 5) & 7

		if frame_type == 3:
			# Unnumbered frame, determine what type
			ax25_u_control_field_type = working_character & 0xEF
		else:
			ax25_u_control_field_type = 0

		if (ax25_u_control_field_type == 0x6F):
			print("SABME", end='')
		elif (ax25_u_control_field_type == 0x2F):
			print("SABM", end='')
		elif (ax25_u_control_field_type == 0x43):
			print("DISC", end='')
		elif (ax25_u_control_field_type == 0x0F):
			print("DM", end='')
		elif (ax25_u_control_field_type == 0x63):
			print("UA", end='')
		elif (ax25_u_control_field_type == 0x87):
			print("FRMR", end='')
		elif (ax25_u_control_field_type == 0x03):
			print("UI", end='')
		elif (ax25_u_control_field_type == 0xAF):
			print("XID", end='')
		elif (ax25_u_control_field_type == 0xE3):
			print("TEST", end='')

		if (frame_type == 0) or (ax25_u_control_field_type == 3):
			# This is an Information frame, or an Unnumbered Information frame, so
			# there is a PID byte.
			index = index + 1
			working_character = frame[index]
			print(", PID: ", end='')
			print(f'{hex(working_character)} ', end='')
			if (working_character == 1):
				print("ISO 8208", end='')
			if (working_character == 6):
				print("Compressed TCP/IP", end='')
			if (working_character == 7):
				print("Uncompressed TCP/IP", end='')
			if (working_character == 8):
				print("Segmentation Fragment", end='')
			if (working_character == 0xC3):
				print("TEXNET", end='')
			if (working_character == 0xC4):
				print("Link Quality Protocol", end='')
			if (working_character == 0xCA):
				print("Appletalk", end='')
			if (working_character == 0xCC):
				print("ARPA Internet Protocol", end='')
			if (working_character == 0xCD):
				print("ARPA Address Resolution", end='')
			if (working_character == 0xCF):
				print("TheNET (NET/ROM)", end='')
			if (working_character == 0xF0):
				print("No Layer 3", end='')
			if (working_character == 0xFF):
				print("Escape", end='')

		index = index + 1

		# return the index of the start of payload data
		print(" ")
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

	print(f'Frame CRC value: {crc.CalcCRC16(kiss_frame)}')

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
