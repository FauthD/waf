#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import time
import logging
import threading
import queue

from Helpers import WafException
from .lirc import lirc
from .irmp import irmp
from .DummyRemote import DummyRemote

class RemotesManager():
	'Manager for Remotes'
	def __init__(self, stopper):
		super().__init__()
		# self.config = None
		self._remotes = []
		self.RX_Fifo = queue.Queue()
		self.TX_Fifo = queue.Queue()
		self._stopper = stopper

###########################################
	def InstantiateClass(self, cfg:dict):
		class_name = cfg.get('class', 'UnknownClass')
		instance = globals().get(class_name)
		try:
			if instance:
				ret = instance(cfg, self.RX_Fifo, self._stopper)
			else:
				logging.info(f"Class '{class_name}' not found.")
				ret = None
		except Exception as e:
			logging.info(f"{class_name} - {e}")
			ret = None

		return ret

	def Init(self, config):
		remotes = config.get('remotes', None)
		# print(type(devices), devices)
		if isinstance(remotes, dict):
			keys = remotes.keys()
			#print(keys)
			for k in keys:
				remote = remotes[k]
				if 'name' not in remote:
					remote['name'] = k
				logging.info (f"Init Remotes: {k}")
				self._remotes.append(self.InstantiateClass(remote))
		else:
			logging.info("remotes must exist and be a dict (ensure to add a space after the :)")
		
		for remote in self._remotes:
			if remote is not None:
				remote.Init()

	def Validate(self):
		if self._remotes is None or len(self._remotes) == 0:
			raise WafException("RemotesManager: There is no remote control defined")

		for remote in self._remotes:
			if remote is not None:
				remote.Validate()
			else:
				raise WafException("RemotesManager: A remote control is None")

###########################################
	def Send(self, code):
		for remote in self._remotes:
			if remote is not None:
				remote.Send(code)

###########################################
	# This is a blocking call
	def GetRemoteCode(self, timeout):
		return self.RX_Fifo.get(timeout=timeout)

