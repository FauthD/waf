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

import time

class StatusLed():
	def __init__(self, status_led:dict):
		# print(type(status_led), status_led)
		if isinstance(status_led, dict):
			self.status_led = status_led
		else:
			print("status_led must be a dict (ensure to add a space after the :)")
		self._Status = 0

	def ShowStatus(self, num_busy, delay):
		self.Toggle()
		time.sleep(num_busy/8)
