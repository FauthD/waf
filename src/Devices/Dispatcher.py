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

import logging
import time
import os
import threading

from Helpers import States,Modifier,timeout,watchclock

class Dispatcher():
	'Dispatch IR codes to device classes'
	def __init__(self):
		self.config = {}
		self.lock = threading.Lock()
		self.dispatch_dict = {}
		self.mofifier_dict = {}
		
	# For now I keep the old two step translation table until I see how the states could be directly placed in the yaml
	_States = {
		'tv': ( States.WATCHTV, 0 ),
		'movie' : ( States.WATCHTVMOVIE, 0 ),
		'brmovie' : ( States.WATCHBRMOVIE, 0 ),
		'dlna' : ( States.LISTENMUSICDLNA, 0 ),
		'radio' : ( States.LISTENRADIO, 0 ),
		'iradio' : ( States.LISTENIRADIO, 1 ),
		'iradio1' : ( States.LISTENIRADIO, 1),
		'iradio2' : ( States.LISTENIRADIO, 2,),
		'iradio3' : ( States.LISTENIRADIO, 3,),
		'iradio4' : ( States.LISTENIRADIO, 4,),
		'iradio5' : ( States.LISTENIRADIO, 5,),
		'iradio6' : ( States.LISTENIRADIO, 6,),
		'iradio7' : ( States.LISTENIRADIO, 7,),
		'iradio8' : ( States.LISTENIRADIO, 8),
		'iradio9' : ( States.LISTENIRADIO, 9,),
		'off' : ( States.OFF, 0 ),
		'chromecast' : ( States.CHROMECAST, 0 ),
		'blueray' : ( States.WATCHBRMOVIE, 0 ),
		'tv2dlna' : ( States.TV2DLNA, 0 ),
		'wii' : ( States.WII, 0 ),
	}

	_Modifier = {
		'usespeaker' : ( Modifier.USESPEAKER, 0 ),
		'mute' : ( Modifier.MUTE, 0 ),
		'unmute' : ( Modifier.UNMUTE, 0 ),
		'togglemute' : ( Modifier.TOGGLEMUTE, 0 ),
	}

###########################################
	def InitDispatch(self):
		self.dispatch_dict = self.config.get('dispatch', None)
		self.mofifier_dict = self.config.get('dispatch_modifier', None)
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
		if self.mofifier_dict is None:
			logging.error("There is no mofifier_dict defined")

###########################################
	def Dispatch(self, ir_code:str):
		cmd = self.dispatch_dict.get(ir_code, None)
		if cmd is None:
			remote,key = ir_code.split()
			cmd = self.dispatch_dict.get(key, None)
		if cmd is None:
			self.DispatchModifier(ir_code)
		else:
			state = self._States.get(cmd, None)
			if state is not None:
				self.SetState(state)

###########################################
	def DispatchModifier(self, ir_code:str):
		modifier = self.mofifier_dict.get(ir_code, None)
		if modifier is None:
			remote,key = ir_code.split()
			modifier = self.mofifier_dict.get(key, None)
		if modifier is None:
			logging.info(f"Unknown ir code {ir_code}")
		else:
			mod = self._Modifier.get(modifier, None)
			if mod is not None:
				self.SetModifier(mod)

###########################################
	def SetState(self, state):
		pass

###########################################
	def SetModifier(self, modifier):
		pass
