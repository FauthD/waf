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
from Helpers import States,Modifier,Timeout,Watchclock,WafException

class StatusLedsManager(object):
	'Manager for Status Leds'
	def __init__(self, dev_config:dict):
		print(f"{dev_config}")
		super().__init__()
		self.config = None
		self._devices = []

###########################################
	def InstantiateClass(self, cfg:dict):
		class_name = cfg.get('class', 'UnknownClass')
		instance = globals().get(class_name)
		try:
			if instance:
				ret = instance(cfg)
			else:
				logging.info(f"Class '{class_name}' not found.")
				ret = None
		except Exception as e:
			logging.info(f"{class_name} - {e}")
			ret = None

		return ret

	def Instantiate(self, config):
		cfg = config.get('status_led', None)
		if isinstance(cfg, dict):
			self.status_led = self.InstantiateClass(cfg)
		else:
			logging.info("status_led must exist and be a dict (ensure to add a space after the :)")

	def Validate(self):
		if self.status_led is None:
			raise WafException("StatusLedsManager: There is no status led defined")
