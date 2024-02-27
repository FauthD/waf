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

from Helpers import WafException,Counter

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
	def __init__(self, stopper):
		super().__init__()
		self.config = {}
		self._devices = []
		self.RX_Fifo = queue.Queue()
		self.TX_Fifo = queue.Queue()
		self._time = watchclock.Watchclock()
		self._status_leds = StatusLedsManager()
		self._mute = threading.Event()
		self._busy_count = Counter()
		self._stopper = stopper

###########################################
	def InstantiateClass(self, cfg:dict):
		class_name = cfg.get('class', 'UnknownClass')
		instance = globals().get(class_name)
		try:
			if instance:
				ret = instance(cfg, self._busy_count, self._stopper)
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
				raise WafException("DevicesManager: A device is None")

###########################################
	def SetState(self, state):
		self._busy_count.Set(len(self._devices))
		with self.lock:
			for device in self._devices:
				if device is not None:
					device.SetState(state)

	def stop(self):
		with self.lock:
			for device in self._devices:
				if device is not None:
					device.stop()

	def getTime(self):
		return self._time.getTime()

	def ShowBusy(self):
		logging.error('WaitFinish aborted {self.getTime():.1f} secs')
		for device in self._devices:
			if device.isBusy():
				logging.error(f'Still busy: {device.getName()}, breaking it')
				device.ResetBusy()

	def WaitFinish(self):
		logging.debug(f' WaitFinish started after {self.getTime():.1f} secs')
		to = timeout.Timeout(70)
		NumBusy = self._busy_count.Get()
		while NumBusy > 0:
			self._status_leds.ShowStatus(NumBusy)
			time.sleep(self._status_leds.GetDelay())
			NumBusy = self._busy_count.Get()
			if to.isExpired():
				self.ShowBusy()
				break

	def Clean(self):
		logging.debug(f'Clean after {self.getTime():.1f} secs')
		self._status_leds.Off()

	def Dispatch(self, ir_code:str):
		self._time.Reset()
		self._mute.clear()
		if super().Dispatch_(ir_code):
			self.WaitFinish()
			self.Clean()
