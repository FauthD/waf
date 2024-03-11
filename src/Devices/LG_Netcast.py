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

ConnectionTimeout=60
DEFAULT_VOLUME=14

class LG_Netcast(Device):
	def __init__(self, dev_config:dict, count, send):
		super().__init__(dev_config, count, send)

		self._externspeaker=False
		self.muted=False
		self.volume=DEFAULT_VOLUME
		self.access_token = self.dev_config.get('KEY', '')
		#logging.debug('LG __init__')

	def RepeatStart(self):
		logging.debug(f'{self.getName()} RepeatStart')
		self.SendIR('POWER_ON')

	def SendIR(self, cmd):
		logging.debug(f'  LG Send {cmd}')
		super().SendIR(cmd, 4)

	def TurnOn(self):
		super().TurnOn()
		self.SendIR('POWER_ON')
		self._On = self.WaitForHost()
		time.sleep(1)
		self.IsMute()
		
	def TurnOff(self):
		super().TurnOff()
		#self.NetCastCmd(LG_COMMAND.POWER) # IR is much faster
		self.SendIR('POWER_OFF')
		self._On = False

	def SelectInput(self, key):
		input_ir = self.dev_config.get('INPUTS', {}).get(key, None)
		logging.debug(f'  {self.getName()} input: {input_ir}')
		self.SendIR(f'{input_ir}')

	def IsRunning(self):
		if self._On == True:
			return True
		return super().IsRunning

	def NetCastCmd(self, cmd):
		if self.IsRunning() and self._On:
			logging.debug(f'  LG Cmd {cmd}')
			to = Timeout(ConnectionTimeout)
			loop = True
			while loop:
				try:
					with LgNetCastClient(self.getName(), self.access_token) as client:
						client.send_command(cmd)
					break
				except LgNetCastError as lg:
					logging.debug(f'  LG NetCastCmd exception {lg}')
				except ConnectionError as ce:
					logging.debug(f'  LG ConnectionError exception {ce}')
				except Exception as ex:
					logging.debug(f'  LG NetCastCmd Exception {ex}')
				finally:
					time.sleep(2)
					if to.isExpired():
						logging.error(f'  LG NetCastCmd abort {cmd}')
						loop = False

	def IsMute(self):
		#logging.debug('IsMute1')
		self.muted = False
		if self.IsRunning() and self._On:
			#logging.debug('LG Cmd {0}'.format(cmd))
			to = Timeout(ConnectionTimeout)
			loop = True
			while loop:
				try:
					with LgNetCastClient(self.getName(), self.access_token) as client:
						self.volume, self.muted = client.get_volume()
					break
				except LgNetCastError as lg:
					logging.debug(f'  LG IsMute exception {lg}')
				except ConnectionError as ce:
					logging.debug(f'  LG IsMute ConnectionError exception {ce}')
				except Exception as ex:
					logging.debug(f'  LG IsMute Exception {ex}')
				finally:
					time.sleep(2)
					if to.isExpired():
						logging.error('  LG IsMute abort')
						loop = False
		#logging.debug('IsMute2')
		logging.debug(f'  LG Volume {self.volume}, mute {self.muted}')
		return self.muted

	def SetVolume(self, volume):
		#logging.debug('SetVolume1')
		if self.IsRunning() and self._On:
			#logging.debug('LG Cmd {0}'.format(cmd))
			to = Timeout(ConnectionTimeout)
			loop = True
			while loop:
				try:
					with LgNetCastClient(self.getName(), self.access_token) as client:
						client.set_volume(volume)
					self.volume = volume
					self.muted = False
					break
				except LgNetCastError as lg:
					logging.debug(f'  LG SetVolume exception {lg}')
				except ConnectionError as ce:
					logging.debug(f'  LG SetVolume exception {ce}')
				except Exception as ex:
					logging.debug(f'  LG SetVolume Exception {ex}')
				finally:
					time.sleep(2)
					if to.isExpired():
						logging.error('  LG SetVolume abort')
						loop = False

		#logging.debug('SetVolume2')
		#logging.debug('LG Volume {0}, mute {1}'.format(self.volume, self.muted))

	def ToggleMute(self):
		if self._On:
			self.NetCastCmd(LG_COMMAND.MUTE_TOGGLE)

	def LG_Mute(self):
		logging.debug(f'  {self.getName()} Mute')
		if not self.IsMute():
			self.ToggleMute()

	def LG_UnMute(self):
		logging.debug(f'  {self.getName()} UnMute')
		if self.IsMute():
			self.ToggleMute()

	def GlobalMute(self):
		super().GlobalMute()
		if self._On:
			self.LG_Mute()

	def GlobalUnMute(self):
		super().GlobalUnMute()
		if self._On and not self._externspeaker:
				self.LG_UnMute()

	def ToggleGlobalMute(self):
		super().ToggleGlobalMute()
		if self._On and not self._externspeaker:
			self.ToggleMute()

	def UseSpeaker(self):
		if self._On:
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
		self._externspeaker=True

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
