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
import eiscp

from . import Device
from Helpers import States,Modifier,Timeout,Watchclock

DEFAULT_VOLUME=20

class Onkyo(Device):
	def __init__(self, dev_config:dict, count, send):
		super().__init__(dev_config, count, send)
		self.receiver = eiscp.eISCP(self._devicename, self.dev_config.get('PORT', 60128))
		self._once = False;
#FIXME:		self._mute = mute_event
		self._on_timer = Timeout(13)
		self._volume=self.dev_config.get('DLNA_VOLUME', DEFAULT_VOLUME)
		self._ipos = 3

	def __del__(self):
		if self.receiver is not None:
			self.receiver.disconnect()

	def RepeatStart(self):
		logging.debug('%s RepeatStart', self.getName())
		self.SendIR('POWER_ON')
		newstate = self._newstate
		if newstate==States.WATCHTVMOVIE:
			self.SelectTV_IR()
			if self._on_timer.isExpired():
				self._mute.set()    # tell TV that we are ready to play
		elif newstate==States.WATCHBRMOVIE:
			self.SelectBR_IR()
			if self._on_timer.isExpired():
				self._mute.set()    # tell TV that we are ready to play
		elif newstate==States.LISTENMUSICDLNA:
			self.SelectDlna_IR()

	def logTime(self):
		if not self._once:
			super().logTime()
			self._once = True

	def SendIR(self, cmd):
		logging.debug(f' Onkyo Send {cmd}')
		super().SendIR(cmd, 4)

	def TurnOn(self):
		super().TurnOn()
		self.SendIR('POWER_ON')
		self._on_timer.Reset()
		self._On = self.WaitForHost()
		if self._newstate==States.WATCHTVMOVIE:
			self._mute.set()    # tell TV that we are ready to play

	NeedPrepare = [
		States.LISTENMUSICDLNA,
		States.LISTENRADIO,
		States.LISTENIRADIO,
		States.WATCHBRMOVIE,
	]

	def TurnOff(self):
		super().TurnOff()
		if self._On:
			# prepare to watch move on next start for a better user experience
			if self._oldstate in self.NeedPrepare:
				self.SelectTV()
				self._oldstate=States.WATCHTVMOVIE

		self.SendIR('POWER_OFF')
		self._once = False
		self._On = False
		if self.receiver is not None:
			self.receiver.disconnect()

	def OnkyoOff_Eth(self):
		logging.debug('OnkyoOff_Eth')
		self.OnkyoRaw('PWR00')

	def OnkyoDiscover(self):
		(command_output, exitstatus) = pexpect.run('onkyo --discover', withexitstatus=True)
		if exitstatus != 0 :
			print(f'OnkyoDiscover failed {exitstatus}')

	def DoRecover(self, to):
		RetVal = True
		time.sleep(1)
		logging.debug('Onkyo exception')
		self.receiver.disconnect()
		if to.isExpired():
			logging.debug('Onkyo abort')
			RetVal = False
		return RetVal

	def OnkyoRaw(self, cmd):
		to = Timeout(20)
		logging.debug(f' OnkyoRaw {cmd}')
		loop = True
		while loop:
			try:
				self.receiver.raw(cmd)
				loop = False
				self.logTime()
			except ValueError as verr:
				logging.debug(f' OnkyoRaw {cmd} failed: {verr}')
				loop = False
			except:
				# If we are too soon after power up, Onkyo is not ready yet and rejects connection
				# We then need to call the disconnect to get a clean start after some time (~6 secs)
				loop = self.DoRecover(to)
				# time.sleep(1)
				# logging.debug('OnkyoRaw exception')
				# self.receiver.disconnect()
				# if to.isExpired():
				#     logging.debug('OnkyoRaw abort')
				#     loop = False

	def OnkyoCommand(self, command, arguments=None):
		to = Timeout(20)
		logging.debug(f' OnkyoCommand {command} {arguments}')
		loop = True
		while loop:
			try:
				self.receiver.command(command, arguments, zone='main')
				loop = False
				self.logTime()
			except ValueError as verr:
				logging.debug(f' OnkyoCommand {command} {arguments} failed: {verr}')
				loop = False
			except:
				# If we are too soon after power up, Onkyo is not ready yet and rejects connection
				# We then need to call the disconnect to get a clean start after some time (~6 secs)
				loop = self.DoRecover(to)

	def GlobalMute(self):
		super().GlobalMute()
		if self._On:
			self.SendIR('MUTE')

	def GlobalUnMute(self):
		super().GlobalUnMute()
		self.OnkyoVolume(self._volume)
		logging.debug(f' GlobalMute done {self.getName()}')

	def ToggleGlobalMute(self):
		super().ToggleGlobalMute()
		if self._On:
			self.SendIR('MUTE')

	def OnkyoVolume(self, volume):
		if self._On:
			self._volume = volume
			self.OnkyoRaw(f'MVL{volume:2X}')

	def SelectDlna(self):
		logging.debug(f'{self.getName()} SelectDlna')
		self.OnkyoVolume(self.dev_config.get('DLNA_VOLUME', DEFAULT_VOLUME))
		self.OnkyoRaw('SLI27')

	def SelectDlna_IR(self):
		logging.debug(f'{self.getName()} SelectDlna_IR')
		self.SendIR('NET')

	def SelectTV(self):
		logging.debug(f'{self.getName()} SelectTV')
		self.OnkyoRaw('SLI23')
		self.OnkyoVolume(self.dev_config.get('TV_VOLUME', DEFAULT_VOLUME))

	def SelectTV_IR(self):
		logging.debug(f'{self.getName()} SelectTV_IR')
		self.SendIR('TV_CD')

	def SelectBR(self):
		logging.debug(f'{self.getName()} SelectBR')
		self.OnkyoRaw('SLI10')
		self.OnkyoVolume(self.dev_config.get('BR_VOLUME', DEFAULT_VOLUME))

	def SelectBR_IR(self):
		logging.debug(f'{self.getName()} SelectBR_IR')
		self.SendIR('BD_DVD')

	def WatchTV(self):
		self.TurnOff()

	def WatchTvMovie(self):
		self.TurnOn()
		self.SelectTV()

	def WatchBrMovie(self):
		self.TurnOn()
		self.SelectBR()

	def UseSpeaker(self):
		self.WatchTvMovie()

	def ListenMusic(self):
		self.TurnOn()
		self.SelectDlna()
		logging.debug(f'{self.getName()} ListenMusic done')

	def ListenRadio(self):
		self.TurnOn()
		self.OnkyoRaw('SLI24')
		self.OnkyoVolume(self.dev_config.get('FMRADIO_VOLUME', DEFAULT_VOLUME))
		logging.debug(f'{self.getName()} ListenRadio done')

	def ListenIRadio(self):
		self.TurnOn()
		self.OnkyoRaw('SLI2B')
		#self.OnkyoCommand('source', 'internet-radio')
		#self.OnkyoCommand('source=internet-radio')
		self.OnkyoVolume(self.dev_config.get('IRADIO_VOLUME', DEFAULT_VOLUME))
		self._ipos = self._StateParam
		self.SelectIRadio()
		logging.debug(f'{self.getName()} ListenIRadio done')

	def SelectIRadio(self):
		self.OnkyoRaw(f'NPR{self._ipos:02d}')

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
			logging.debug('Onkyo {code}, state={self._newstate}')
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
					#logging.debug('Onkyo {0}, _ipos={1}'.format(code[0], self._ipos))

				if self._ipos>40:
					self._ipos=1
				if self._ipos<1:
					self._ipos=40

				self.SelectIRadio()

	def PlayWii(self):
		logging.debug('Onkyo WII')
		self.TurnOn()
		self.OnkyoVolume(self.dev_config.get('WII_VOLUME', DEFAULT_VOLUME))

	def WatchChromecast(self):
		self.TurnOn()
		logging.debug(f'{self.getName()} WatchChromecast')
		self.OnkyoRaw('SLI23')
		self.OnkyoVolume(self.dev_config.get('CROMECAST_VOLUME', DEFAULT_VOLUME))
