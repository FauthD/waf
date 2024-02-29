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

import pexpect
import time
import logging
from pylgnetcast import LgNetCastClient, LG_COMMAND, LG_QUERY

from . import Device
from Helpers import States,Modifier,Timeout,Watchclock

DEFAULT_VOLUME=14

class LG_Netcast(Device):
	def __init__(self, dev_config:dict, count, send):
		super().__init__(dev_config, count, send)

		self._externspeaker=False
		self.muted=False
		self.volume=DEFAULT_VOLUME
		#logging.debug('LG __init__')

	def GetTV(self):
		return self.getName(), self.dev_config.get('KEY', '')

	def RepeatStart(self):
		logging.debug(f'{self.getName()} RepeatStart')
		self.SendIR('POWER_ON')

	def SendIR(self, cmd):
		logging.debug(f' LG Send {cmd}')
		super().SendIR(cmd, 4)

	def TurnOn(self):
		super().TurnOn()
		self.SendIR('POWER_ON')
		self._On = self.WaitForHost()
		self.IsMute()
		
	def TurnOff(self):
		super().TurnOff()
		self.NetCastCmd(LG_COMMAND.POWER)
#		self.Send('POWEROFF')
		self._On = False

	def LG_Hdmi(self, Key):
		number = self.dev_config.get('INPUTS', {}).get(Key, 0)
		logging.debug(f' {self.getName()} Hdmi{number}')
		self.SendIR(f'HDMI{number}')

	def IsRunning(self):
		if self._On == True:
			return True
			
		(command_output, exitstatus) = pexpect.run(f'fping -t 100 -c1 -q {self._devicename}', withexitstatus=True)
		return exitstatus==0

	def NetCastQuery(self, cmd):
		if self.IsRunning():
			logging.debug(f'LG Query {cmd}')
			to = Timeout(30)
			data = None
			while not data:
				try:
					with LgNetCastClient(self.GetTV()) as client:
						data = client.query_data(cmd)
				except:
					logging.debug(' LG Query exception')
					time.sleep(2)
					if to.isExpired():
						logging.debug(' LG Query abort')
						return None
			return data
		return None

	def NetCastCmd(self, cmd):
		if self.IsRunning():
			logging.debug(f' LG Cmd {cmd}')
			to = Timeout(30)
			loop = True
			while loop:
				try:
					with LgNetCastClient(self.GetTV()) as client:
						client.send_command(cmd)
					loop = False
				except:
					logging.debug(' LG Cmd exception')
					time.sleep(2)
					if to.isExpired():
						logging.debug(' LG Cmd abort')
						loop = False

	def IsMute_old(self):
		#logging.debug('IsMute1')
		muted = False
		data = self.NetCastQuery(LG_QUERY.VOLUME_INFO)
		if data:
			volume_info = data[0]
			muted = volume_info.find('mute').text == 'true'
		#logging.debug('IsMute2')
		return muted

	def IsMute(self):
		#logging.debug('IsMute1')
		self.muted = False
		if self.IsRunning():
			#logging.debug('LG Cmd {0}'.format(cmd))
			to = Timeout(30)
			loop = True
			while loop:
				try:
					with LgNetCastClient(self.GetTV()) as client:
						self.volume, self.muted = client.get_volume()
					loop = False
				except:
					logging.debug(' LG Cmd exception')
					time.sleep(2)
					if to.isExpired():
						logging.debug(' LG Cmd abort')
						loop = False
		#logging.debug('IsMute2')
		logging.debug(f' LG Volume {self.volume}, mute {self.muted}')
		return self.muted

	def SetVolume(self, volume):
		#logging.debug('SetVolume1')
		if self.IsRunning():
			#logging.debug('LG Cmd {0}'.format(cmd))
			to = Timeout(30)
			loop = True
			while loop:
				try:
					with LgNetCastClient(self.GetTV()) as client:
						client.set_volume(volume)
					loop = False
					self.volume = volume
					self.muted = False
				except:
					logging.debug(' LG Cmd exception')
					time.sleep(2)
					if to.isExpired():
						logging.debug(' LG Cmd abort')
						loop = False
		#logging.debug('SetVolume2')
		#logging.debug('LG Volume {0}, mute {1}'.format(self.volume, self.muted))

	def ToggleMute(self):
		if self._On:
			self.NetCastCmd(LG_COMMAND.MUTE_TOGGLE)

	def LG_Mute(self):
		logging.debug(f' {self.getName()} Mute')
		if not self.IsMute():
			self.ToggleMute()

	def LG_UnMute(self):
		logging.debug(f' {self.getName()} UnMute')
		if self.IsMute():
			self.ToggleMute()

	def GlobalMute(self):
		super().GlobalMute()
		if self._On:
			self.LG_Mute()

	def GlobalUnMute(self):
		super().GlobalUnMute()
		if self._On:
			if not self._externspeaker:
				self.LG_UnMute()

	def ToggleGlobalMute(self):
		super().ToggleGlobalMute()
		if self._On:
			if not self._externspeaker:
				self.ToggleMute()

	def UseSpeaker(self):
		if self._On:
			self.LG_Mute()
		self._externspeaker=True

	def WatchTV(self):
		self.TurnOn()
		self.LG_Hdmi('VDR')
		self.LG_UnMute()
		self.SetVolume(self.dev_config.get('TV_VOLUME', DEFAULT_VOLUME))
		self._externspeaker=False

	def WatchTvMovie(self):
		self.TurnOn()
		self.LG_Hdmi('VDR')

	def WatchBrMovie(self):
		self.TurnOn()
		self.LG_Hdmi('BLUERAY')

	def ListenMusic(self):
		self.TurnOff()
		self._externspeaker=True

	def ListenRadio(self):
		self.TurnOff()
		self._externspeaker=True

	def ListenIRadio(self):
		self.TurnOff()

	def WatchChromecast(self):
		self.TurnOn()
		self.LG_Hdmi('CROMECAST')
		self.UseSpeaker()

	def WatchDlnaOnTV(self):
		self.TurnOn()
		self.NetCastCmd(LG_COMMAND.AV_MODE)

	def PlayWii(self):
		self.TurnOn()
		#logging.debug('LG_COMPONENT1')
		self.SendIR('WII')
		self.UseSpeaker()
