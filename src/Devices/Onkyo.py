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
import eiscp

from . import Device
from Helpers import States,Timeout

DEFAULT_VOLUME=20

class Onkyo(Device):
	def __init__(self, dev_config:dict, count, send):
		super().__init__(dev_config, count, send)
		self.receiver = eiscp.eISCP(self._devicename, self.dev_config.get('PORT', 60128))
		self._turn_on_timer = Timeout(13)
		self._volume=self.dev_config.get('DLNA_VOLUME', DEFAULT_VOLUME)
		self._ipos = 3

	def __del__(self):
		if self.receiver is not None:
			self.receiver.disconnect()

	def RepeatStart(self):
		logging.debug(f'{self.name} RepeatStart')
		self.SendIR('POWER_ON')
		inputs = self.dev_config.get('INPUTS', {})
		code = inputs.get(self._newstate, None)
		if code:
			self.SendIR(code)
		if self._turn_on_timer.isExpired():
			self.SetExternSpeaker()    # tell TV that we are ready to play

	# Called by RunCommands to process the Commands from yaml
	def RunCommand(self, command):
		if self.receiver and self._On:
			parts = command.split('|')
			if len(parts) == 1:
				self.OnkyoCommand(command)
			elif parts[0].upper() == 'RAW':
				self.OnkyoRaw(parts[1])
			else:
				logging.debug(f'Unknown command: {command}')

	def SendIR(self, cmd, repeat=1):
		logging.debug(f' {self.name} Send {cmd}')
		super().SendIR(cmd, 4)

	def TurnOn(self):
		super().TurnOn()
		self._turn_on_timer.Reset()
		self.SendIR('POWER_ON')
		self._On = self.WaitForHost()
		if self._On:
			self.RunCommands('OnTurnOn')

	NeedPrepare = [
		States.LISTENMUSICDLNA,
		States.LISTENRADIO,
		States.LISTENIRADIO,
		States.WATCHBRMOVIE,
	]

	def TurnOff(self):
		super().TurnOff()
		if self._On:
			# prepare to watch movie on next start for a better user experience
			if self._oldstate in self.NeedPrepare:
				self.SelectTV()
				self._oldstate=States.WATCHTVMOVIE
			self.RunCommands('OnTurnOff')
			if self.receiver:
				self.receiver.disconnect()
		self.SendIR('POWER_OFF')
		self._On = False

	def DoRecover(self, to, command):
		ret = True
		time.sleep(1)
		logging.debug(f'  {self.name} recover from {command}')
		self.receiver.disconnect()
		if to.isExpired():
			logging.debug(f'{self.name} abort {command}')
			ret = False
		time.sleep(1)
		return ret

	def OnkyoRaw(self, cmd):
		self.OnkyoCmd(self.receiver.raw, cmd)

	def OnkyoCommand(self, cmd):
		self.OnkyoCmd(self.receiver.command, cmd)

	def OnkyoCmd(self, function, cmd):
		to = Timeout(20)
		logging.debug(f' {function.__name__} {cmd}')
		log_once = False
		loop = self._On
		while loop:
			try:
				function(cmd)
				loop = False
				if not log_once:
					super().logTime()
					log_once = True
			except ValueError as valerr:
				logging.debug(f' {function.__name__} {cmd} failed: {valerr}')
				loop = False
			except Exception as e:
				# If we are too soon after power up, Onkyo is not ready yet and rejects connection
				# We then need to call the disconnect to get a clean start after some time (~6 secs)
				logging.debug(f' {function.__name__} {cmd} failed: {e}')
				loop = self.DoRecover(to, cmd)

	def GlobalMute(self):
		super().GlobalMute()
		if self._On:
			self.SendIR('MUTE')

	def GlobalUnMute(self):
		super().GlobalUnMute()
		self.OnkyoVolume(self._volume)
		logging.debug(f' GlobalMute done {self.name}')

	def ToggleGlobalMute(self):
		super().ToggleGlobalMute()
		if self._On:
			self.SendIR('MUTE')

	def OnkyoVolume(self, volume):
		if self._On:
			self._volume = volume
			self.OnkyoRaw(f'MVL{volume:2X}')

	def SelectDlna(self):
		logging.debug(f'{self.name} SelectDlna')
		self.OnkyoVolume(self.dev_config.get('DLNA_VOLUME', DEFAULT_VOLUME))
		self.OnkyoRaw('SLI27')

	def SelectTV(self):
		logging.debug(f'{self.name} SelectTV')
		self.OnkyoRaw('SLI23')
		self.OnkyoVolume(self.dev_config.get('TV_VOLUME', DEFAULT_VOLUME))

	def SelectBR(self):
		logging.debug(f'{self.name} SelectBR')
		self.OnkyoRaw('SLI10')
		self.OnkyoVolume(self.dev_config.get('BR_VOLUME', DEFAULT_VOLUME))

	def WatchTV(self):
		self.TurnOff()

	def WatchTvMovie(self):
		self.TurnOn()
		self.SelectTV()
		self.SetExternSpeaker()    # tell TV that we are ready to play

	def WatchBrMovie(self):
		self.WatchTvMovie()

	def PlayGame1(self):
		logging.debug(f'{self.name} GAME1')
		self.TurnOn()

	def OnkyoOff_Eth(self):
		logging.debug(f' {self.name} OnkyoOff_Eth')
		self.OnkyoRaw('PWR00')

		self.OnkyoVolume(self.dev_config.get('GAME1_VOLUME', DEFAULT_VOLUME))
		self.SetExternSpeaker()    # tell TV that we are ready to play

	def WatchChromecast(self):
		self.TurnOn()
		logging.debug(f'{self.name} WatchChromecast')
		self.OnkyoRaw('SLI23')
		self.OnkyoVolume(self.dev_config.get('CROMECAST_VOLUME', DEFAULT_VOLUME))
		self.SetExternSpeaker()    # tell TV that we are ready to play

	def UseSpeaker(self):
		self.WatchTvMovie()

	def ListenMusic(self):
		self.TurnOn()
		self.SelectDlna()
		logging.debug(f'{self.name} ListenMusic done')

	def ListenRadio(self):
		self.TurnOn()
		self.OnkyoRaw('SLI24')
		self.OnkyoVolume(self.dev_config.get('FMRADIO_VOLUME', DEFAULT_VOLUME))
		logging.debug(f'{self.name} ListenRadio done')

	def ListenIRadio(self):
		self.TurnOn()
		self.OnkyoRaw('SLI2B')
		self.OnkyoVolume(self.dev_config.get('IRADIO_VOLUME', DEFAULT_VOLUME))
		# FIXME later: self._ipos = self._StateParam
		self.SelectIRadio()
		logging.debug(f'{self.name} ListenIRadio done')

	def SelectIRadio(self):
		self.OnkyoRaw(f'NPR{self._ipos:02d}')

# Experimental below
	Translate = [
		States.LISTENRADIO,
		States.LISTENIRADIO,
	]

	IR_Send = {
		'vol+': 'ONKYO_VOLUMEUP',
		'vol-': 'ONKYO_VOLUMEDOWN',
		'mute': 'ONKYO_MUTE',
	}

	Num = ['1','2','3','4','5','6','7','8','9']

	def SetIrCommand(self, code):
		if self._newstate in self.Translate:
			logging.debug(f'{self.name} {code}, state={self._newstate}')
			if code in self.IR_Send:
				send = self.IR_Send[code]
				logging.debug(f'Send: {send}')
				self.SendIR(send)
			elif self._newstate==States.LISTENIRADIO:
				#logging.debug('Onkyx {0}, state={1}'.format(code, self._newstate))
				if code == 'chan+':
					self._ipos +=1
				elif code == 'chan-':
					self._ipos -=1
				elif code in self.Num:
					self._ipos = ord(code[0])-ord('0')
					#logging.debug(f'{self.name} {0}, _ipos={1}'.format(code[0], self._ipos))

				if self._ipos>40:
					self._ipos=1
				if self._ipos<1:
					self._ipos=40

				self.SelectIRadio()
