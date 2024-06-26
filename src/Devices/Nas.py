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
import logging

from . import Device

class Nas(Device):
	def __init__(self, dev_config:dict, count, send):
		super().__init__(dev_config, count, send)

	def RepeatStart(self):
		logging.debug(f'{self.name} RepeatStart')
		self.WakeOnLan()

	def TurnOn(self):
		super().TurnOn()
		self.WakeOnLan()
		self._On = self.WaitForHost()

	def TurnOff(self):
		self._On = False

	def WatchTV(self):
		pass
		#logging.debug('StartVdrOnEis')
		#Remote('cmd@eis', 'vdr_start.sh')

	def WatchTvMovie(self):
		pass

	def ListenMusic(self):
		pass
