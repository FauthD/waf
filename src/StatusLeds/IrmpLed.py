#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import logging
import time
import Irmp
from . StatusLed import StatusLed

#####################################################################
class IrmpLed(StatusLed):
	'Irmp status led handler'
	def __init__(self, status_led:dict):
		super().__init__(status_led)
		self.device = self.status_led.get('device', '/dev/irmp_stm32')
		try:
			self.irmp = Irmp.IrmpHidRaw(self.device)
			self.irmp.open()
		except IOError as ex:
			logging.error(f"You probably don't have the IRMP device. {ex}")

	def __del__(self):
		self.irmp.Set(0)

	def Stop(self):
		super().Stop()
		self.Off()
		self._irmp.close()

	def Off(self):
		self._Status = False
		self.irmp.SendLedReport(self._Status)

	def On(self):
		self._Status = True
		self.irmp.SendLedReport(self._Status)

	def Toggle(self):
		self._Status ^= True
		self.irmp.SendLedReport(self._Status)

