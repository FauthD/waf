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

NUM_PIXEL=Irmp.NUM_PIXEL
DefaultColors = { 1: '100,20,25' }
#####################################################################
class IrmpNeopixel(StatusLed):
	'IrmpNeopixel status led handler'
	def __init__(self, status_led:dict):
		super().__init__(status_led)
		self.colors = {}
		self.index=0
		self.device = self.status_led.get('device', '/dev/irmp_stm32')
		try:
			self.irmp = Irmp.IrmpHidRaw(self.device)
			self.irmp.open()
		except IOError as ex:
			print(ex)
			logging.error("You probably don't have the IRMP device.")

		self.TranslateDict(self.status_led.get('colors', DefaultColors))
		self.last_color = 0,0,0
		self.last_num = 0

	def Stop(self):
		super().Stop()
		self._irmp.close()

	def String2Integers(self, string):
		try:
			if string is None:
				raise ValueError('RGB string is None.')
			integers = [int(num.strip(), 0) for num in string.split(',')]
			if len(integers) != 3:
				raise ValueError('RGB must have exact 3 numbers "{string}".')
			return integers
		except ValueError as e:
			print("Could not parse int:", e)
		return []

	def TranslateDict(self, input:dict):
		for key,value in input.items():
			rgb = self.String2Integers(value)
			self.colors[key] = rgb

	def BlendColor(self, color):
		blend_color = [0,0,0]
		for i in range(len(color)):
			blend_color[i] = int((color[i]+self.last_color[i]*3)/4)
		return blend_color

	def Off(self):
		self._Status = False
		self.last_color = 0,0,0
		self.last_num = 0
		self.Set(self._Status)

	def On(self):
		self._Status = True
		self.Set(self._Status)

	def Toggle(self):
		self._Status ^= True
		self.Set(self._Status)

	def ShowStatus(self, num_busy):
		color = self.colors.get(num_busy, (50,35,20))
		if self.last_num != num_busy:
			self.last_num = num_busy
			for i in range(7):
				_color = self.BlendColor(color)
				self.last_color = _color
				self.Next(_color)
				time.sleep(self.GetDelay())
		self.last_color = color
		self.Next(color)

	def Set(self, value):
		v = int(value)
		r=v*128
		g=0
		b=int(v*8)
		for n in range(NUM_PIXEL):
			self.irmp.setPixelColor(n, r,g,b)
		self.irmp.SendNeopixelReport()

	def NextIndex(self):
		list = [1,2,3,4,5,6, 5,4,3,2]
		self.index += 1
		if self.index >= len(list):
			self.index = 0
		return list[self.index]

	def Next(self, color):
		n = self.NextIndex()
		r, g, b = color
		self.irmp.setPixelColor(n, r,g,b)
		self.irmp.setDarkPixelColor(n+1, r,g,b)
		self.irmp.setDarkPixelColor(n-1, r,g,b)
		self.irmp.SendNeopixelReport()
		self.irmp.setPixelColor(n, 0,0,0)
		self.irmp.setPixelColor(n-1, 0,0,0)
		self.irmp.setPixelColor(n+1, 0,0,0)
