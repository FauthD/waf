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

# pip install pexpect
import pexpect
import time
import logging
import threading

from Helpers import States,Modifier,Timeout,Watchclock

class Device(threading.Thread):
	'Base class for devices'
	def __init__(self, dev_config:dict, count, stopper, maxtime=60):
		#print(f"{dev_config}")
		self._devicename = dev_config.get('name', 'unknown')
		super().__init__(name=self._devicename)
		self._macaddress = dev_config.get('mac', '00:00:00:00:00:00')
		self._timeout = Timeout(maxtime)
		self._busy_count = count
		self._stopper = stopper
		self._start_time = Watchclock()
		self._oldstate = States.NONE
		self._newstate = States.NONE
		self._work = threading.Condition()
		self._available = threading.Event()
		self._On = False
		self._GlobalMute = False
		# self.setDaemon(True)
		self.start()

###########################################
	def Validate(self):
		pass
	
	def stop(self):
		self._newstate = States.NONE
		with self._work:
			self._work.notify()
		self.join()

	def isBusy(self):
		return not self._available.is_set()

	def getTime(self):
		return self._start_time.getTime()

	def logTime(self):
		logging.debug(f' Log {self.getName()} after {self.getTime():.1f} secs')

	def WakeOnLan(self):
		logging.debug(f'WakeOnLan {self._devicename} {self._macaddress}')
		pexpect.run(f'wakeonlan {self._macaddress}')

	def RepeatStart(self):
		self.WakeOnLan()

	def WaitForHost(self):
		logging.debug(f' Wait for {self.getName()}')
		self._timeout.Reset()
		exitstatus = 1
		count = 0
		while (exitstatus != 0) and not self._timeout.isExpired() and self._stopper.run:
			time.sleep(0.5)
			#run_time = watchclock.Watchclock()
			(command_output, exitstatus) = pexpect.run(f'ping -i 0.3 -c1 {self._devicename}', withexitstatus=True)
			#logging.debug('fping delay {0} {1:.1f} secs'.format(self.getName(), run_time.getTime()))
			count += 1 # do not send the repeat too often
			if exitstatus != 0 and count%4==0:
				self.RepeatStart()
		ret = not self._timeout.isExpired()
		if ret:
			logging.debug(f'Found {self.getName()} after {self.getTime():.1f} secs')
		else:
			logging.debug(f'Failed, ping exit {self.getName()}, {exitstatus}, {command_output}')
		return ret

	def Remote(self, host, cmd):
		command = f"ssh {host} '{cmd}'"
		logging.debug(f'{command}')
		(command_output, exitstatus) = pexpect.run(command, withexitstatus=True)
		return exitstatus

	def SetState(self, state):
		self._start_time.Reset()
		logging.debug(f'SetState {self.getName()}: {state}')
		self._available.wait()
		self._available.clear()
		# do not update oldstate for modifiere keys (e.g. mute)
		if state in States:
			self._oldstate = self._newstate
		self._newstate = state
		with self._work:
			self._work.notify()
		if not self.is_alive():
			logging.debug(f'SetState {self.getName()} failed! Thread is dead.')

	# runs as a thread
	def run(self):
		self._available.set()
		while self._stopper.run:

			jmp = {
				# states
				States.OFF: self.TurnOff,
				States.WATCHTV: self.WatchTV,
				States.WATCHTVMOVIE: self.WatchTvMovie,
				States.WATCHBRMOVIE: self.WatchBrMovie,
				States.LISTENMUSICDLNA: self.ListenMusic,
				States.LISTENRADIO: self.ListenRadio,
				States.LISTENIRADIO: self.ListenIRadio,
				States.CHROMECAST: self.WatchChromecast,
				States.TV2DLNA: self.WatchDlnaOnTV,
				States.WII: self.PlayWii,
				# Modifiers
				Modifier.MUTE: self.GlobalMute,
				Modifier.UNMUTE: self.GlobalUnMute,
				Modifier.TOGGLEMUTE: self.ToggleGlobalMute,
				Modifier.USESPEAKER: self.UseSpeaker,
			}
			if self._newstate in jmp:
				logging.debug(f' work {self.getName()}: {self._newstate}')
				jmp[self._newstate]()
				logging.debug(f' Done {self.getName()} after {self.getTime():.1f} secs')
				self._busy_count.Decrement()

			self._available.set()
			with self._work:
				self._work.wait()

		logging.debug(f'thread {self.getName()} ended')

	def SetIrCommand(self, code):
		pass

	def TurnOn(self):
		logging.debug(f' {self.getName()} On')

	def TurnOff(self):
		logging.debug(f' {self.getName()} Off')

	def WatchTV(self):
		time.sleep(50)
		pass

	def WatchTvMovie(self):
		pass

	def ListenMusic(self):
		pass

	def ListenRadio(self):
		pass

	def ListenIRadio(self):
		pass

	def WatchBrMovie(self):
		pass

	def WatchChromecast(self):
		pass

	def UseSpeaker(self):
		pass

	def PlayWii(self):
		pass

	def WatchDlnaOnTV(self):
		pass

	def GlobalMute(self):
		self._GlobalMute = True

	def GlobalUnMute(self):
		self._GlobalMute = False

	def ToggleGlobalMute(self):
		self._GlobalMute ^= True

