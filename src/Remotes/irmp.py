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
import Remote

import Irmp
from Helpers import WafException

###########################################
class irmp(Remote):
	'Send/receive IR codes with irmp'
	def __init__(self, cfg:dict):
		super().__init__(cfg)
		self.device = cfg.get('device', '/dev/irmp_stm32')
		self._irmp = IrmpConnector(self.device, self.RX_Fifo, self.rx_enable)
		self._irmp.open()

	def __del__(self):
		self._irmp.close()

###########################################
	def Send(self, code):
		if not self.tx_enable:
			return
		
		remote, key = code.split()
		try:
			code = self._irmp.GetCode(remote, key)
			data = []
			data += [code[i:i+2] for i in range(0, len(code), 2)]
			self._irmp.SendIrReport(data)
		except:
			print(f"Unknown code: '{remote} {key}'")


##############################################
class IrmpConnector(Irmp.IrmpHidRaw):
	def __init__(self, device, RX_Fifo, rx_enable):
		super().__init__(self, device)
		self.RX_Fifo = RX_Fifo
		self.rx_enable = rx_enable
		self.RxThread = threading.Thread(target=self.ReadIr, args=())
		self.RxThread.setDaemon(True)
		self.RxThread.start()

##############################################
	# callback from IrmpHidRaw (ReadIr thread)
	def IrReceiveHandler(self, Protcol, Addr, Command, Flag):
		irmp_fulldata = f"{Protcol:02x}{Addr:04x}{Command:04x}00"
		try:
			remote,name = self.GetKey(irmp_fulldata).split()
		except:
			remote = "IRMP"
			name = irmp_fulldata

		if self.rx_enable:
			self.RX_Fifo.put(f"{irmp_fulldata} {Flag} {name} {remote}")


