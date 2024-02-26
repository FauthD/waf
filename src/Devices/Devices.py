#!/usr/bin/env python
# -*- coding: utf-8 -*-
#	WIP
# 
# This file is part of the waf distribution (https://github.com/fauthd/waf).
# Copyright (c) 2024 Dieter Fauth.
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

import time
import logging
import threading
import queue
from Helpers import WafException
from .Dispatcher import Dispatcher
from .Vdr import Vdr
from .VdrOnboard import VdrOnboard
from .Nas import Nas
from .LG_Netcast import LG_Netcast
from .Onkyo import Onkyo
from .PanasonicBR import PanasonicBR

from Helpers import timeout,watchclock,WafException
from StatusLeds import StatusLedsManager

class DevicesManager(Dispatcher):
	'Manager for Devices'
	def __init__(self):
		super().__init__()
		self.config = {}
		self._devices = []
		self.RX_Fifo = queue.Queue()
		self.TX_Fifo = queue.Queue()
		self._time = watchclock.Watchclock()
		self._status_leds = StatusLedsManager()
		self._mute = threading.Event()

###########################################
	def InstantiateClass(self, cfg:dict):
		class_name = cfg.get('class', 'UnknownClass')
		instance = globals().get(class_name)
		try:
			if instance:
				ret = instance(cfg)
			else:
				logging.info(f"Class '{class_name}' not found.")
				ret = None
		except Exception as e:
			logging.info(f"{class_name} - {e}")
			ret = None

		return ret

###########################################
	def Init(self, config:dict):
		super().Init(config)
		self._status_leds.Init(self.config)

		devices = config.get('devices', None)
		# print(type(devices), devices)
		if isinstance(devices, dict):
			keys = devices.keys()
			#print(keys)
			for k in keys:
				device = devices[k]
				if 'name' not in device:
					device['name'] = k
				logging.info (f"Init Devices: {k}")
				self._devices.append(self.InstantiateClass(device))
		else:
			logging.info("devices must exist and be a dict (ensure to add a space after the :)")

###########################################
	def Validate(self):
		super().Validate()
		self._status_leds.Validate()

		if self._devices is None or len(self._devices) == 0:
			raise WafException("DevicesManager: There is no device defined")
		for device in self._devices:
			if device is not None:
				device.Validate()
			else:
				raise WafException("DevicesManager: A remote control is None")

###########################################
	def SetState(self, state):
		with self.lock:
			for device in self._devices:
				if device is not None:
					device.SetState(state)

	def getTime(self):
		return self._time.getTime()

	def NumBusy(self):
		Busy = 0
		for device in self._devices:
			Busy += device.isBusy()
		return Busy

	def ShowBusy(self):
		for device in self._devices:
			if device.isBusy():
				logging.debug(f'Still busy: {device.getName()}, breaking it')
				device.ResetBusy()

	def WaitFinish(self):
		logging.debug(f' WaitFinish started after {self.getTime():.1f} secs')
		to = timeout.Timeout(70)
		Busy = self.NumBusy()
		while Busy > 0:
			self._status_leds.Toggle()
			time.sleep(Busy/4)
			Busy = self.NumBusy()
			if to.isExpired():
				logging.debug('WaitFinish aborted {self.getTime():.1f} secs')
				self.ShowBusy()
				break

	def Clean(self):
		logging.debug(f'Clean after {self.getTime():.1f} secs')
		self._status_leds.Off()

	def Dispatch(self, ir_code:str):
		self._time.Reset()
		self._mute.clear()
		super().Dispatch(ir_code)
		self.WaitFinish()
		self.Clean()
