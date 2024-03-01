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
from Helpers import States,Modifier,Timeout,Watchclock,WafException

from .BananaPiLed import BananaPiLed
from .DummyLed import DummyLed
from .IrmpLed import IrmpLed
from .IrmpNeopixel import IrmpNeopixel

class StatusLedsManager(object):
	'Manager for Status Leds'
	def __init__(self):
		super().__init__()
		self.cfg = None
		self._devices = []

###########################################
	def InstantiateClass(self):
		class_name = self.cfg.get('class', 'UnknownClass')
		instance = globals().get(class_name)
		try:
			if instance:
				ret = instance(self.cfg)
			else:
				logging.info(f"Class '{class_name}' not found.")
				ret = None
		except Exception as e:
			logging.info(f"{class_name} - {e}")
			ret = None

		return ret

	def Init(self, config):
		self.cfg = config.get('status_led', None)
		if isinstance(self.cfg, dict):
			self.status_led = self.InstantiateClass()
		else:
			logging.info("status_led must exist and be a dict (ensure to add a space after the :)")

	def Validate(self):
		if self.status_led is None:
			logging.error("StatusLedsManager: No status led available.")

	def GetDelay(self):
		if self.status_led is not None:
			return self.status_led.GetDelay()
		else:
			return 0.1

	def Off(self):
		if self.status_led is not None:
			self.status_led.Off()

	def On(self):
		if self.status_led is not None:
			self.status_led.On()

	def Toggle(self):
		if self.status_led is not None:
			self.status_led.Toggle()

	def ShowStatus(self, num_busy):
		if self.status_led is not None:
			self.status_led.ShowStatus(num_busy)
