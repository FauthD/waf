#!/usr/bin/env python
# -*- coding: utf-8 -*-
# with activity fun -> waf
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

import yaml
import threading
import logging
import time
import os

from StatusLeds import StatusLedsManager
from Remotes import RemotesManager
from Devices import DevicesManager
from Helpers import timeout,watchclock,WafException

CONFIGNAME='waf.yaml'
LOGPATH='/var/log/waf.log'

class Waf():
	def __init__(self):
		self.InitLogging()
		self.config = None
		self._devices = DevicesManager()
		self._remotes = RemotesManager()
		self._status_leds = StatusLedsManager()
		self._time = watchclock.Watchclock()
		self._mute = threading.Event()

	def ReadConfig(self, name=CONFIGNAME):
		pathlist = []
		pathlist.append(os.path.join('~/.config', name))
		pathlist.append(os.path.join('/etc', name))
		pathlist.append(name)
		for path in pathlist:
			logging.debug(f'Try config file {path}')
			if os.path.isfile(path):
				try:
					with open(name, 'r') as file:
						self.config = yaml.safe_load(file)
						if self.config is not None or len(self.config):
							logging.debug(f'Using config file {path}')
							break
				except:
					continue
		if self.config is None or self.config is {}:
			logging.debug(f'No config file {name} found')

###########################################
	def Init(self):
		self.ReadConfig()
		if self.config is not None:
			self._devices.Init(self.config)
			self._remotes.Init(self.config)
			self._status_leds.Init(self.config)
		return self.Validate()

###########################################
	def Validate(self):
		try:
			if self.config is None:
				raise WafException(f'No config available')
			self._devices.Validate()
			self._remotes.Validate()
			self._status_leds.Validate()
			ret = True
		except WafException as e:
			logging.debug(e)
			ret = False
		return ret

###########################################
	# def SetIrCommand(self, code):
	# 	for device in self._devices:
	# 		device.SetIrCommand(code)

	def getTime(self):
		return self._time.getTime()

	def isBusy(self):
		return self.NumBusy() > 0

	def NumBusy(self):
		return self._devices.NumBusy()

	def ShowBusy(self):
		self._devices.ShowBusy()

	def WaitFinish(self):
		logging.debug(f' WaitFinish started after {self.getTime():.1f} secs')
		to = timeout.Timeout(70)
		Busy = self.NumBusy()
		while Busy > 0:
			self._status_leds.Toggle()
			time.sleep(Busy/4)
			Busy = self.NumBusy()
			if to.isExpired():
				logging.debug('WaitFinish aborted {self.getTime():.1f} secs')
				self.ShowBusy()
				break

	def InitLogging(self):
		logging.basicConfig(filename=LOGPATH, format='%(asctime)s.%(msecs)03d %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
		logging.debug('=== Start ===')

	def Clean(self):
		logging.debug(f'Clean after {self.getTime():.1f} secs')
		self._status_leds.Off()

###########################################
	def Doit(self):
		while True:
			code = self._remotes.GetRemoteCode()
			self._time.Reset()
			self._mute.clear()
			self._devices.Dispatch(code)
			self.WaitFinish()
			self.Clean()


def main():
	c = Waf()
	c.Init()
	if c.Validate():
		#c.status_led.On()
		c.Doit()

	# print(globals())



if __name__ == "__main__":
	exit ( main() )

