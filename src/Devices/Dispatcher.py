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
from abc import abstractmethod

class Dispatcher():
	'Dispatch IR codes to device classes'
	def __init__(self):
		self.config = {}
		self.lock = threading.Lock()
		self.dispatch_dict = {}

###########################################
	def InitDispatch(self):
		self.dispatch_dict = self.config.get('dispatch', None)
		# print(cfg)

###########################################
	def Init(self, config:dict):
		self.config = config
		dispatch = config.get('dispatch', None)
		# print(type(devices), devices)
		if isinstance(dispatch, dict):
			self.InitDispatch()
		else:
			logging.info("dispatch must exist and be a dict (ensure to add a space after the :)")

###########################################
	def Validate(self):
		if self.dispatch_dict is None:
			logging.error("There is no dispatch_dict defined")

###########################################
	#'15000f04c300 0 15000f04c300 IRMP'
	def TranslateIR(self, ir_code:str):
		state=None
		repeat='1'
		parts = ir_code.split()
		if len(parts)==4:
			code,repeat,key,remote = parts
			state = self.dispatch_dict.get(f'{remote} {key}', None)
			if state is None:
				state = self.dispatch_dict.get(f'{key}', None)
			if state is None:
				state = self.dispatch_dict.get(f'{remote} {code}', None)
		return (state,int(repeat))

###########################################
	def Dispatch_(self, ir_code:str):
		ret = False
		state,repeat = self.TranslateIR(ir_code)
		if not repeat:
			if state:
				logging.debug(f'=== code={state} ===')
				self.SetState(state)
				ret = True
			else:
				logging.debug(f"Unknown ir code {ir_code}")
		return ret
###########################################
	@abstractmethod
	def SetState(self, state):
		''' Must overwrite this in a derived class! '''
		pass

