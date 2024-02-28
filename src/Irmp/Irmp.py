#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Common defs for IRMP
# Copyright (C) 2024 Dieter Fauth
#
# This program is free software: you can redistribute it and/or modify  
# it under the terms of the GNU General Public License as published by  
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


###############################################
import os
import time
import errno
import selectors
import logging
import threading
from dataclasses import dataclass

VID=0x1209
PID=0x4444

NUM_PIXEL=8
REPORT_ID_IR = 1
REPORT_ID_CONFIG_IN = 2
REPORT_ID_CONFIG_OUT = 3
REPORT_SIZE = 64

STAT_CMD = 0
ACC_SET = 1
CMD_EMIT = 0
CMD_STATUSLED = 10
CMD_NEOPIXEL = 0x41
NEOPIXEL_PAYLOAD_OFFSET = 8
IRSEND_PAYLOAD_OFFSET = 4

DefaultIrmpDevPath='/dev/irmp_stm32'
DEFAULT_MAPFILE='/etc/irmplircd/irmplircd.map'
DEFAULT_MAPDIR='/etc/irmplircd/irmplircd.d'

# FIXME: Bring Pixels into class IrmpHidRaw
###############################################
@dataclass
class Pixel:
	w: int = 0
	r: int = 0
	g: int = 0
	b: int = 0

Pixels = [Pixel() for i in range(NUM_PIXEL+1)]

class IrmpHidRaw():
	def __init__(self, device_path:str=DefaultIrmpDevPath, map:str=DEFAULT_MAPFILE, mapdir:str=DEFAULT_MAPDIR, stop=None):
		self._device_path = device_path
		self._hidraw_fd = None
		self._buffer_size=REPORT_SIZE
		self._mapfile=map
		self._mapdir=mapdir
		self._keymap = {}
		self._codemap = {}
		self._remotes = []
		self.RxThread = None
		if stop is None:
			self._stop_= threading.Event()
		else:
			self._stop_ = stop

	###############################################
	def open(self):
		self._hidraw_fd = os.open(self._device_path, os.O_RDWR | os.O_NONBLOCK)
		return self._hidraw_fd

	###############################################
	def read(self):
		try:
			return os.read(self._hidraw_fd, self._buffer_size)
		except IOError as ex:
			if (ex.errno == errno.EAGAIN):
				return None
			else:
				raise(ex)

	###############################################
	def write(self, data):
		try:
			os.write(self._hidraw_fd, data)
		except IOError as ex:
			logging.error(f"Error writing to HIDRAW device: {ex}")

	###############################################
	def close(self):
		try:
			if(self._hidraw_fd):
				os.close(self._hidraw_fd)
			self._hidraw_fd = None
		except IOError as ex:
			logging.error(f"Error closing HIDRAW device: {ex}")

	###############################################
	def ReadMap(self, mapfile:str, remote:str):
		self._remotes.append(remote)
		with open(mapfile) as f:
			lines = f.readlines()
			for line in lines:
				parts =line.split()
				if (parts is not None and len(parts) >= 2):
					if (parts[0].startswith('#')):
						continue
					if (parts[1].startswith('#')):
						continue
					name = f"{remote} {parts[1]}"
					if parts[0] in self._keymap:
						logging.info(f"Multiple definitions of: {parts[0]} - {name}")
					if name in self._codemap:
						logging.info(f"Multiple definitions of: {name}, problems ahead")
					self._keymap[parts[0]] = name
					self._codemap[name] = parts[0]# reverse translation for irsend
		#logging.info (self.keymap)

	###############################################
	def ReadMapDir(self, mapdir:str):
		if (os.path.exists(mapdir)):
			for file in os.listdir(mapdir):
				remote = file.split('.')[0]
				self.ReadMap(os.path.join(mapdir, file), remote)

	###############################################
	def ReadConfig(self):
		self.ReadMap(self._mapfile, "IRMP")
		self.ReadMapDir(self._mapdir)
		# logging.info (self._keymap)
		# logging.info (self._codemap)

	###############################################
	def _ReadConfig(self):
		try:
			self.ReadConfig()
		except IOError as ex:
			logging.info(ex)
		# logging.info (self._keymap)
		# logging.info (self._codemap)

	###############################################
	def GetKey(self, code):
		return self._keymap[code]

	###############################################
	def GetCode(self, remote, key):
		self.CheckRemote(remote)
		lookup = f"{remote} {key}"
		if not lookup in self._codemap:
			raise KeyException(f'unknown command: "{lookup}"\n')
		return self._codemap[lookup]

	###############################################
	def GetCodeMap(self):
		return self._codemap
	
	###############################################
	def GetRemotes(self):
		return self._remotes
	
	###############################################
	def CheckRemote(self, remote):
		if not remote in self.GetRemotes():
			raise KeyException(f'unknown remote "{remote}"')

	###############################################
	# Raw Data (dec):
	# [1, 21, 		15, 0,	34, 4, 		1,		0, 0, .....]
	# ID, Protocol, Addr,	Command,	Flag,	Unused
	###############################################
	def Decode(self, received):
		if (received[0] == REPORT_ID_IR):
			Protcol = received[1]
			Addr = received[2]+(received[3]<<8)
			Command = received[4]+(received[5]<<8)
			Flag = received[6]

			self.IrReceiveHandler(Protcol, Addr, Command, Flag)

		elif (received[0] != REPORT_ID_CONFIG_IN):
			logging.debug (received)

	###############################################
	def IrReceiveHandler(self, Protcol, Addr, Command, Flag):
		pass

	###############################################
	def ReadIr(self):
		#logging.debug("Read the data in endless loop")
		selector = selectors.DefaultSelector()
		selector.register(self._hidraw_fd, selectors.EVENT_READ)
		
		try:
			while not self._stop_.is_set():
				events = selector.select(timeout=1)
				for key, _ in events:
					if key.fileobj == self._hidraw_fd:
						d = self.read()
						if d:
							self.Decode(d)	# finally calls IrReceiveHandler
		finally:
			selector.unregister(self._hidraw_fd)

	###############################################
	def StartRxThread(self):
		self.RxThread = threading.Thread(target=self.ReadIr, args=())
		self.RxThread.start()

	###############################################
	def StopRxThread(self):
		self._stop_.set()
		if self.RxThread is not None:
			self.RxThread.join()
			self.RxThread = None

	###############################################
	def SendIrReport(self, data):
		report = bytearray(REPORT_SIZE)
		report[0] = REPORT_ID_CONFIG_OUT
		report[1] = STAT_CMD
		report[2] = ACC_SET
		report[3] = CMD_EMIT
		i = IRSEND_PAYLOAD_OFFSET
		for d in data:
			report[i] = int(d,16)
			i += 1

		self.write(report)

	###############################################
	def SendLedReport(self, led):
		report = bytearray(REPORT_SIZE)
		report[0] = REPORT_ID_CONFIG_OUT
		report[1] = STAT_CMD
		report[2] = ACC_SET
		report[3] = CMD_STATUSLED
		report[4] = led

		self.write(report)

	###############################################
	def SendNeopixelReport(self):
		report = bytearray(REPORT_SIZE)
		report[0] = REPORT_ID_CONFIG_OUT
		report[1] = STAT_CMD
		report[2] = ACC_SET
		report[3] = CMD_NEOPIXEL
		report[4] = NUM_PIXEL
		for i in range(NUM_PIXEL):
			offset = NEOPIXEL_PAYLOAD_OFFSET+i*4
			report[offset + 0] = Pixels[i].w
			report[offset + 1] = Pixels[i].b
			report[offset + 2] = Pixels[i].r
			report[offset + 3] = Pixels[i].g

		self.write(report)

	###############################################
	def setPixelColor(self, index: int, r: int, g: int, b: int):
		Pixels[index] = Pixel(0,r,g,b)

	###############################################
	def setDarkPixelColor(self, index: int, r: int, g: int, b: int):
		self.setPixelColor(index, int(r/16),int(g/16),int(b/16))

	###############################################
	def InitPixels(self):
			for n in range(NUM_PIXEL):
				self.setPixelColor(n, 0,0,0)

	###############################################
	def DemoSweep(self, r, g, b, delay=0.050):
		for n in range(NUM_PIXEL):
			self.setPixelColor(n, r,g,b)
			self.setDarkPixelColor(n+1, r,g,b)
			self.setDarkPixelColor(n-1, r,g,b)
			self.SendNeopixelReport()
			time.sleep(delay)
			self.setPixelColor(n, 0,0,0)
			self.setPixelColor(n-1, 0,0,0)

		for n in reversed(range(NUM_PIXEL)):
			self.setPixelColor(n, r,g,b)
			self.setDarkPixelColor(n-1, r,g,b)
			self.setDarkPixelColor(n+1, r,g,b)
			self.SendNeopixelReport()
			time.sleep(delay)
			self.setPixelColor(n, 0,0,0)
			self.setPixelColor(n+1, 0,0,0)

		self.setPixelColor(0, 0,0,0)
		self.SendNeopixelReport()

class KeyException(Exception):
	pass
