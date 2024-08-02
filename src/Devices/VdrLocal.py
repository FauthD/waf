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

import pexpect
import time
import logging

from . import Device
from Helpers import Timeout

###########################################
class VdrLocal(Device):
	'VDR on local machine'

	def __init__(self, dev_config:dict, count, send):
		super().__init__(dev_config, count, send, maxtime=2)
		self._SvdrPsend_Dict = self.dev_config.get('SvdrPsend', None)

	def RepeatStart(self):
		pass

	def RunSvdrPsend(self, DictName):
		if self._SvdrPsend_Dict:
			cmds = self._SvdrPsend_Dict.get(DictName, None)
			if cmds:
				for cmd in cmds:
					if type(cmd) is list:
						command,delay = cmd
					else:
						command = cmd
						delay = '0.1'
					if len(command):
						self._SvdrPsend(command)
					time.sleep(float(delay))

	def SvdrPsend(self, cmd):
		to = Timeout(40)
		exitstatus = 1
		while exitstatus!=0:
			exitstatus = not self._SvdrPsend(cmd)
			if exitstatus!=0:
				if to.isExpired():
					logging.debug(f'{self.name} abort {cmd}')
					return False
				time.sleep(0.5)
		return exitstatus==0

	def _SvdrPsend(self, cmd):
		logging.debug(f'  SvdrPsend {cmd}')
		#run_time = watchclock.Watchclock()
		exitstatus = 1
		command = f"svdrpsend -d {self._devicename} '{cmd}'"
		(command_output, exitstatus) = pexpect.run(command, withexitstatus=True)
		#logging.debug('Svdrpsend delay {0:.1f} secs exit={1}'.format(run_time.getTime(), exitstatus))
		return exitstatus==0

	def TurnOn(self):
		super().TurnOn()
		pexpect.run('systemctl start vdr.service')
		self.SvdrPsend('PING')
		time.sleep(0.5)
		self._On = self.SvdrPsend('REMO on')
		if self._On:
			self.RunCommands('OnTurnOn')

	def TurnOff(self):
		super().TurnOff()
		if self.IsRunning():
			self.RunCommands('OnTurnOff')
		self._On = False

	def WatchTV(self):
		self.TurnOn()

	def WatchTvMovie(self):
		self.TurnOn()

	def ListenMusic(self):
		self.TurnOff()
