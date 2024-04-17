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
import gpiod
from gpiod.line import Direction, Value
from . StatusLed import StatusLed

InvalidMsg = 'GpiodLed is invalid'
class GpiodLed(StatusLed):
	'Gpio handler'
	def __init__(self, status_led:dict):
		super().__init__(status_led)
		self._Status = False
		chip = status_led.get('chip', None)
		if not chip:
			logging.error(f'StatusLed failed since chip {chip} is not valid')
		self.line = status_led.get('line', None)
		if not self.line:
			logging.error(f'StatusLed failed since line {self.line} is not valid')

		if chip and self.line:
			self.request=gpiod.request_lines(
				chip, consumer="waf",
				config={
					self.line: gpiod.LineSettings(
						direction=Direction.OUTPUT, output_value=Value.ACTIVE
					)
				}
			)
		else:
			logging.error('GpiodLed failed')

	# def __del__(self):
	# 	if self.line:
	# 		self.line.release()
	# 	else:
	# 		logging.error(InvalidMsg)

	def Off(self):
		self._Status = False
		if self.line:
			self.set_value(self._Status)
		else:
			logging.error(InvalidMsg)

	def On(self):
		self._Status = True
		if self.line:
			self.set_value(self._Status)
		else:
			logging.error(InvalidMsg)

	def Toggle(self):
		self._Status ^= True
		if self.line:
			self.set_value(self._Status)
		else:
			logging.error(InvalidMsg)

	def set_value(self, val):
		self.request.set_value(self.line, Value.ACTIVE if val else Value.INACTIVE)
