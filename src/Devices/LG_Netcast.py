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
from pylgnetcast import LgNetCastClient, LG_COMMAND, LG_QUERY, LgNetCastError, AccessTokenError, SessionIdError

from . import Device
from Helpers import States,Modifier,Timeout,Watchclock

DEFAULT_VOLUME=14

class NoneException(Exception):
	pass
class LG_Netcast(Device):
	def __init__(self, dev_config:dict, count, send):
		super().__init__(dev_config, count, send)

		self._externspeaker=False
		self.muted=False
		self.volume=DEFAULT_VOLUME
		self.access_token = self.dev_config.get('KEY', '')
		#logging.debug('LG __init__')

	def RepeatStart(self):
		logging.debug(f'{self.name} RepeatStart')
		self.SendIR('POWER_ON')

	def SendIR(self, cmd, repeat=1):
		logging.debug(f'  LG Send {cmd}')
		super().SendIR(cmd, 5)

	def TurnOn(self):
		super().TurnOn()
		if not self.IsOn():
			self.SendIR('POWER_ON')
		self._On = self.WaitForHost()
		#self.IsMute()
		
	def TurnOff(self):
		super().TurnOff()
		self.SendIR('POWER_OFF')
		self._On = False

	def SelectInput(self, key):
		input_ir = self.dev_config.get('INPUTS', {}).get(key, '')
		logging.debug(f'  {self.name} input: {input_ir}')
		self.SendIR(f'{input_ir}')

	def IsOn(self) -> bool:
		return self._On and super().IsRunning()

	def NetCastConnect(self, function, param1):
		#logging.debug('NetCastConnect')
		if self.IsOn():
			to = Timeout(30)
			loop = True
			while loop:
				try:
					with LgNetCastClient(self.name, self.access_token) as client:
						function(client, param1)
				except Exception as e:
					logging.debug(f'  NetCastConnect {e}')
				else:
					loop = False
				finally:
					if loop:
						time.sleep(2)
						logging.debug('  NetCastConnect needs one more retry')
						if to.isExpired():
							logging.error('  NetCastConnect abort')
							loop = False

	def _SendCmd_(self, client, cmd):
		client.send_command(cmd)

	def NetCastCmd(self, cmd):
		logging.debug(f'  LG Cmd {cmd}')
		self.NetCastConnect(self._SendCmd_, cmd)

	def _GetMute_(self, client, dummy):
		result = client.get_volume()
		if result is None:
			raise NoneException('get_volume returned None')
		self.volume, self.muted = result

	def IsMute(self):
		logging.debug('LG IsMute1')
		self.muted = False
		self.NetCastConnect(self._GetMute_, 0)
		logging.debug(f'  LG IsMute {self.volume}, mute {self.muted}')
		return self.muted

	def _SetVolume_(self, client, volume):
		client.set_volume(volume)
		self.volume = volume
		self.muted = False

	def SetVolume(self, volume):
		logging.debug('SetVolume1')
		self.NetCastConnect(self._SetVolume_, volume)
		logging.debug(f'  LG SetVolume {self.volume}')

	def ToggleMute(self):
		logging.debug(f'  {self.name} ToggleMute')
		self.NetCastCmd(LG_COMMAND.MUTE_TOGGLE)
 as emptyf):
		logging.debug(f'  {self.name} Mute')
		if not self.IsMute():
			self.ToggleMute()

	def LG_UnMute(self):
		logging.debug(f'  {self.name} UnMute')
		if self.IsMute():
			self.ToggleMute()

	def GlobalMute(self):
		super().GlobalMute()
		if self.IsOn():
			self.LG_Mute()

	def GlobalUnMute(self):
		super().GlobalUnMute()
		if self.IsOn() and not self._externspeaker:
				self.LG_UnMute()

	def ToggleGlobalMute(self):
		super().ToggleGlobalMute()
		if self.IsOn() and not self._externspeaker:
			self.ToggleMute()

	def UseSpeaker(self):
		if self.IsOn():
			self.LG_Mute()
		self._externspeaker=True

	def WatchTV(self):
		self.TurnOn()
		self.SelectInput('VDR')
		self.LG_UnMute()
		self.SetVolume(self.dev_config.get('TV_VOLUME', DEFAULT_VOLUME))
		self._externspeaker=False

	def WatchTvMovie(self):
		self.TurnOn()
		self.SelectInput('VDR')

	def WatchBrMovie(self):
		self.TurnOn()
		self.SelectInput('BLUERAY')

	def ListenMusic(self):
		self.TurnOff()
		self._externs as emptypeaker=True

	def ListenRadio(self):
		self.ListenMusic()

	def ListenIRadio(self):
		self.ListenMusic()

	def WatchChromecast(self):
		self.TurnOn()
		self.SelectInput('CROMECAST')
		self.UseSpeaker()

	def WatchDlnaOnTV(self):
		self.TurnOn()
		self.NetCastCmd(LG_COMMAND.AV_MODE)

	def PlayGame1(self):
		self.TurnOn()
		#logging.debug('GAME1')
		self.SelectInput('GAME1')
		self.UseSpeaker()
