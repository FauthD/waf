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
import threading
import queue

from Helpers import WafException
from .lirc import lirc
from .irmp import irmp
from .DummyRemote import DummyRemote

class RemotesManager():
	'Manager for Remotes'
	def __init__(self):
		super().__init__()
		# self.config = None
		self._remotes = []
		self.rx_fifo = queue.Queue()
		self.tx_fifo = queue.Queue()

###########################################
	def InstantiateClass(self, cfg:dict):
		class_name = cfg.get('class', 'UnknownClass')
		instance = globals().get(class_name)
		try:
			if instance:
				ret = instance(cfg, self.rx_fifo)
			else:
				logging.error(f"Class '{class_name}' not found.")
				ret = None
		except Exception as e:
			logging.info(f"{class_name} - {e}")
			ret = None

		return ret

	def Init(self, config):
		remotes = config.get('remotes', None)
		if isinstance(remotes, dict):
			keys = remotes.keys()
			for k in keys:
				remote = remotes[k]
				if 'name' not in remote:
					remote['name'] = k
				logging.info (f"Init Remotes: {k}")
				self._remotes.append(self.InstantiateClass(remote))
		else:
			logging.critical("remotes must exist and be a dict (ensure to add a space after the :)")
		
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
				logging.error("RemotesManager: Initialization of a remote control failed.")

	def Stop(self):
		for remote in self._remotes:
			if remote is not None:
				remote.Stop()

###########################################
	def Send(self, code):
		logging.debug((f'  Sending: {code}'))
		for remote in self._remotes:
			if remote is not None:
				remote.Send(code)

###########################################
	# This is a blocking call
	def GetRemoteCode(self, timeout):
		return self.rx_fifo.get(timeout=timeout)

