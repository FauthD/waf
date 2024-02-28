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
import threading
import queue

from Helpers import WafException

class Remote():
	def __init__(self, cfg:dict, RX_Fifo:queue):
		self.cfg = cfg
		self.RX_Fifo = RX_Fifo
		self.tx_enable = cfg.get('tx', True)
		self.rx_enable = cfg.get('rx', True)
		self._stop_ = threading.Event()

	def Init(self):
		pass

	def Stop(self):
		self._stop_.set()

	def Validate(self):
		if self.cfg is None or len(self.cfg) == 0:
			raise WafException("Remote: There is no config defined")

	def Send(self, code):
		pass
