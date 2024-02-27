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
import queue
import time
import os
import systemd_stopper

from Remotes import RemotesManager
from Devices import DevicesManager
from Helpers import timeout,watchclock,WafException

CONFIGNAME='waf.yaml'
LOGPATH='/var/log/waf.log'

class Waf():
	def __init__(self):
		self.InitLogging()
		self.config = None
		self._stopper = systemd_stopper.install()
		self._devices = DevicesManager(self._stopper)
		self._remotes = RemotesManager(self._stopper)

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
		try:
			self.ReadConfig()
			if self.config is not None:
				self._devices.Init(self.config)
				self._remotes.Init(self.config)
				ret = True
		except Exception as e:
			logging.error(e)
			ret = False
		if ret:
			ret = self.Validate()
		return ret

###########################################
	def Validate(self):
		try:
			if self.config is None:
				raise WafException(f'No config available')
			self._devices.Validate()
			self._remotes.Validate()
			ret = True
		except WafException as e:
			logging.debug(e)
			ret = False
		return ret

	def InitLogging(self):
		logging.basicConfig(filename=LOGPATH, format='%(asctime)s.%(msecs)03d %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
		logging.debug('=== Start ===')

###########################################
	def Work(self):
		timeout = 0.2
		try:
			if self.Init():
				while self._stopper.run:
					try:
						code = self._remotes.GetRemoteCode(timeout)
					except queue.Empty as empty:
						continue
					else:
						if code is not None:
							self._devices.Dispatch(code)
		except IOError as ex:
			print(f'{ex}')
		except Exception as ex:
			print(f'{ex}')
		finally:
			self._devices.stop()
			logging.debug('=== Stop ===')


def main():
	c = Waf()
	c.Work()
	# print(globals())



if __name__ == "__main__":
	exit ( main() )

