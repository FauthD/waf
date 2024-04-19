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
import telnetlib

from . import Device

class PanasonicBR(Device):
	def __init__(self, dev_config:dict, count, send):
		super().__init__(dev_config, count, send)

	def SendTelnet(self, cmd):
		logging.debug(f'SendTelnet {cmd} to {self.name}')
		try:
			tn = telnetlib.Telnet(host=self._devicename, port=8102, timeout=2)
			#tn.set_debuglevel(20)
			tn.write(cmd.encode('ascii') + b"\r\n")
			response = tn.read_until(b'R', 1)
			logging.debug(f'Telnet response={response} from {self.name}')
			tn.close()
		except:
			logging.debug(f'SendTelnet to {self.name} failed')


	def TurnOn(self):
		super().TurnOn()
		#pexpect.run('irsend SEND_ONCE RC-2422 KEY_ENTER')
		#pexpect.run('irsend SEND_ONCE RC-2422 KEY_POWER')
		#self.WakeOnLan()
		self.SendTelnet('PN')
		self._On = self.WaitForHost()

	def TurnOff(self):
		#pexpect.run('irsend SEND_ONCE RC-2422 KEY_ENTER')
		#pexpect.run('irsend SEND_ONCE RC-2422 KEY_POWER')
		if self._On:
			self.SendTelnet('PF')
			self._On = False

	def WatchBrMovie(self):
		self.TurnOn()

	def WatchTV(self):
		self.TurnOff()

	def WatchTvMovie(self):
		self.TurnOff()

	def ListenMusic(self):
		self.TurnOff()

	def ListenRadio(self):
		self.TurnOff()

	def ListenIRadio(self):
		self.TurnOff()
