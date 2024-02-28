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
from . import Device
from Helpers import States,Modifier,Timeout,Watchclock

###########################################
class Vdr(Device):
	def __init__(self, dev_config:dict, count, send):
		super().__init__(dev_config, count, send)

	def RepeatStart(self):
		logging.debug(f'{self.getName()} RepeatStart')
		self.WakeOnLan()
		self.ServerOn_IR()

	def TurnOffRemote(self):
		if self._On:
			self._SvdrPsend('REMO off')

	# retrun True on success
	def SvdrPsend_ssh(self, cmd):
		#logging.debug('{} SvdrPsend {}'.format(self.getName(), cmd))
		to = Timeout(40)
		exitstatus = 1
		while exitstatus!=0:
			#run_time = watchclock.Watchclock()
			exitstatus = self.Remote('cmd@vdr', 'svdrpsend' + cmd)
			#logging.debug('Svdrpsend delay {0:.1f} secs'.format(run_time.getTime()))
			if exitstatus!=0:
				if to.isExpired():
					logging.debug(f'{self.getName()} abort {cmd}')
					return False
				time.sleep(0.5)
		return exitstatus==0

	def SvdrPsend(self, cmd):
		to = Timeout(40)
		exitstatus = 1
		while exitstatus!=0:
			exitstatus = not self._SvdrPsend(cmd)
			if exitstatus!=0:
				if to.isExpired():
					logging.debug(f'{self.getName()} abort {cmd}')
					return False
				time.sleep(0.5)
		return exitstatus==0

	def _SvdrPsend(self, cmd):
		logging.debug(f'SvdrPsend {cmd}')
		#run_time = watchclock.Watchclock()
		exitstatus = 1
		command = "svdrpsend -d f{self._devicename} '{cmd}'"
		(command_output, exitstatus) = pexpect.run(command, withexitstatus=True)
		#logging.debug('Svdrpsend delay {0:.1f} secs exit={1}'.format(run_time.getTime(), exitstatus))
		return exitstatus==0

	def IsRunning(self):
		(command_output, exitstatus) = pexpect.run(f'fping -t 100 -c1 -q {self._devicename}', withexitstatus=True)
		return exitstatus==0

	def ServerOn_IR(self):
		logging.debug(f'{self.getName()} On_IR')
		self.SendIR('POWER_ON')
		# should turn on the vdr mainboard via CIR

	def ServerOff_IR(self):
		logging.debug(f'{self.getName()} Off')
		self.SendIR('POWER_OFF')
		# Must be configured in VDR!

	def TurnOn(self):
		super().TurnOn()
		self.WakeOnLan()
		self.WaitForHost()
		self.SvdrPsend('PING')
		time.sleep(0.5)
		self._On = self.SvdrPsend('REMO on')
		##self._On = self.SvdrPsend('VOLU 150')    # keep startup volume
		self._SvdrPsend('plug softhddevice ATTA')
		# time.sleep(0.5)
		# self._SvdrPsend('plug pulsecontrol scpr 0 off')
		# time.sleep(2)
		# self._SvdrPsend('plug pulsecontrol scpr 0 output:hdmi-stereo-extra1')

	def TurnOff(self):
		super().TurnOff()
		#if self._On:
		if self.IsRunning():
			# turn off the play (if running)
			self.SvdrPsend('HITK STOP')
			# detach frontend
			#self.SvdrPsend('plug softhddevice DETA')
			# Stop VDR
			time.sleep(0.2)
			# remote control off
			#self.SvdrPsend('REMO off')
			self.SvdrPsend('HITK power')
		#else:
			#self.ServerOff_IR()
		self._On = False

	def WatchTV(self):
		self.TurnOn()

	def WatchTvMovie(self):
		self.TurnOn()

	def WatchBrMovie(self):
		self.TurnOff()

	def ListenMusic(self):
		self.TurnOff()

	def ListenRadio(self):
		self.TurnOff()

	def ListenIRadio(self):
		self.TurnOff()

