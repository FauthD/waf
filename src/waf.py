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
import pathlib

from StatusLeds import *
from IrReceiver import *
from IrBlaster import *
from Devices import *
from Helpers import States,Modifier,timeout,watchclock

CONFIGNAME='waf.yaml'
LOGPATH='/var/log/waf/waf.log'

class Waf():
	def __init__(self):
		self.InitLogging()
		self.config = None
		self.devices = []
		self.ir_receiver = None
		self.status_led = None
		self.ir_blaster = None
		self.dispatch_dict = None
		self.mofifier_dict = None
		self.lock = threading.Lock()
		self._time = watchclock.Watchclock()
		self._mute = threading.Event()

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

	def ReadConfig(self, name=CONFIGNAME):
		# first try in /etc
		try:
			path = pathlib.join('/etc', name)
			with open(path, 'r') as file:
				self.config = yaml.safe_load(file)
		except:
			# then in current dir
			try:
				with open(name, 'r') as file:
					self.config = yaml.safe_load(file)
			except Exception as e:
				print(e)

		# print(self.config)

	def InstantiateClass(self, cfg:dict):
		class_name = cfg.get('class', 'UnknownClass')
		instance = globals().get(class_name)
		try:
			if instance:
				ret = instance(cfg)
			else:
				print(f"Class '{class_name}' not found.")
				ret = None
		except Exception as e:
			print(f"{class_name} - {e}")
			ret = None

		return ret

	def InstantiateDevices(self):
		devices = self.config['devices']
		# print(type(devices), devices)
		if isinstance(devices, dict):
			keys = devices.keys()
			#print(keys)
			for k in keys:
				device = devices[k]
				if 'name' not in device:
					device['name'] = k
				# print (type(device), device)
				self.devices.append(self.InstantiateClass(device))
		else:
			print("devices must be a dict (ensure to add a space after the :)")

	def InstantiateStatusLed(self):
		cfg = self.config['status_led']
		self.status_led = self.InstantiateClass(cfg)
		#print(self.status_led)

	def InstantiateIrReceiver(self):
		cfg = self.config['ir_receiver']
		self.ir_receiver = self.InstantiateClass(cfg)
		#print(self.ir_receiver)

	def InstantiateIrBlaster(self):
		cfg = self.config['ir_blaster']
		self.ir_blaster = self.InstantiateClass(cfg)
		#print(self.ir_blaster)

	def Instantiate(self):
		self.InstantiateDevices()
		self.InstantiateStatusLed()
		self.InstantiateIrReceiver()
		self.InstantiateIrBlasternewmod()

	# this does not work, the variable (e.g. status_led is not used as a reference but  the value (which is None))
	# def Instantiate(self):
	# 	classes = {
	# 		'status_led': [self.status_led],
	# 		'ir_receiver': [self.ir_receiver],
	# 		'ir_blaster': [self.ir_blaster],
	# 	}
	# 	for key,v in classes.items():
	# 		cfg = self.config[key]
	# 		v[0] = self.InstantiateClass(cfg)
	# 	print(self.status_led)
###########################################
	def InitDispatch(self):
		self.dispatch_dict = self.config['dispatch']
		self.mofifier_dict = self.config['dispatch_modifier']
		# print(cfg)

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
			print(f"Unknown ir code {ir_code}")
		else:
			mod = self._Modifier.get(modifier, None)
			if mod is not None:
				self.SetModifier(mod)

###########################################
	def SetState(self, state):
		with self.lock:
			for device in self.devices:
				device.SetState(state)

###########################################
	def SetModifier(self, modifier):
		with self.lock:
			for device in self.devices:
				device.SetModifier(modifier)

###########################################
	def Validate(self):
		check = []
		check.append(self.devices)
		check.append(self.status_led)
		check.append(self.ir_receiver)
		check.append(self.ir_blaster)
		check.append(self.dispatch_dict)
		check.append(self.mofifier_dict)
		for i in check:
			if i is None:
				print(f'A variable is not properly instantiated')

###########################################
	def SetIrCommand(self, code):
		for device in self._devices:
			device.SetIrCommand(code)

	def getTime(self):
		return self._time.getTime()

	def isBusy(self):
		return self.NumBusy() > 0

	def NumBusy(self):
		Busy = 0
		for device in self._devices:
			Busy += device.isBusy()
		return Busy

	def ShowBusy(self):
		for device in self._devices:
			if device.isBusy():
				logging.debug('Still busy: {0}, breaking it'.format(device.getName()))
				device.ResetBusy()

	def WaitFinish(self):
		logging.debug(' WaitFinish started after {0:.1f} secs'.format(self.getTime()))
		to = timeout.Timeout(70)
		Busy = self.NumBusy()
		while Busy > 0:
			self.green_led.Toggle()
			time.sleep(Busy/4)
			Busy = self.NumBusy()
			if to.isExpired():
				logging.debug('WaitFinish aborted {0:.1f} secs'.format(self.getTime()))
				self.ShowBusy()
				break

	def InitLogging(self):
		logging.basicConfig(filename=LOGPATH, format='%(asctime)s.%(msecs)03d %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
		logging.debug('=== Start ===')

	def Clean(self):
		logging.debug('Clean after {0:.1f} secs'.format(self.getTime()))
		self.green_led.Off()

###########################################

def main():
	c = Waf()
	c.ReadConfig()
	c.Instantiate()
	c.Validate()
	c.status_led.On()
	c.InitDispatch()
	#c.T()
	print(globals())



if __name__ == "__main__":
	exit ( main() )
