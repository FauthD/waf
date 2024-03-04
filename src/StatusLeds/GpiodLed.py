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
from . StatusLed import StatusLed

class GpiodLed(StatusLed):
	'Gpio handler'
	def __init__(self, status_led:dict):
		super().__init__(status_led)
		self._Status = False
		chip = status_led.get('chip', None)
		if not chip:
			logging.error(f'StatusLed failed since chip is not valid')
		line = status_led.get('line', None)
		if not line:
			logging.error(f'StatusLed failed since line is not valid')

		if chip and line:
			self.chip = gpiod.chip(chip)
			self.line = self.chip.get_line(line)
			config = gpiod.line_request()
			config.consumer = status_led.get('consumer', 'waf')
			config.request_type = gpiod.line_request.DIRECTION_OUTPUT
			self.line.request(config)

	def __del__(self):
		self.line.release()

	def Off(self):
		self._Status = False
		self.line.set_value(self._Status)

	def On(self):
		self._Status = True
		self.line.set_value(self._Status)

	def Toggle(self):
		self._Status ^= True
		self.line.set_value(self._Status)

# set_direction_input
# is_requested
# is_used
# release

# ACTIVE_HIGH = 2
# ACTIVE_LOW = 1
# BIAS_AS_IS = 1
# BIAS_DISABLE = 2
# BIAS_PULL_DOWN = 4
# BIAS_PULL_UP = 3
# DIRECTION_INPUT = 1
# DIRECTION_OUTPUT = 2
