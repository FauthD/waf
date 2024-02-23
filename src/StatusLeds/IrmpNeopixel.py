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

from . import StatusLed
import Irmp

NUM_PIXEL=8

class Irmp(Irmp.IrmpHidRaw):
	def __init__(self):
		super().__init__()
		self.open()
	
	def __del__(self):
		self.close()

	def Set(self, value):
		v = int(value)
		try:
			r=v*128
			g=0
			b=int(v*8)
			for n in range(NUM_PIXEL):
				self.setPixelColor(n, r,g,b)
			self.SendNeopixelReport()

		except IOError as ex:
			print(ex)
			print("You probably don't have the IRMP device.")

#####################################################################
class IrmpNeopixel(StatusLed):
	'IrmpNeopixel status led handler'
	def __init__(self, status_led:dict):
		super().__init__(status_led)
		self.irmp = Irmp()

	def __del__(self):
		self.irmp.Set(0)

	def Off(self):
		self._Status = False
		self.irmp.Set(self._Status)

	def On(self):
		self._Status = True
		self.irmp.Set(self._Status)

	def Toggle(self):
		self._Status ^= True
		self.irmp.Set(self._Status)

