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
	def __init__(self, dev_config:dict, maxtime=60):
		#print(f"{dev_config}")
		self._devicename = dev_config.get('name', 'unknown')
		super().__init__(name=self._devicename)
		self._macaddress = dev_config.get('mac', '00:00:00:00:00:00')
		self._timeout = Timeout(maxtime)
		self._start_time = Watchclock()
		self._oldstate = States.NONE
		self._newstate = States.NONE
		self._newmod = Modifier.NONE
		self._StateParam=0
		self._ModParam=0
		self._work = threading.Condition()
		self._available = threading.Event()
		self._On = False
		self._GlobalMute = False
		self.setDaemon(True)
		self.start()

###########################################
	def Validate(self):
		pass
	
	def isBusy(self):
		return not self._available.is_set()

	def getTime(self):
		return self._start_time.getTime()

	def logTime(self):
		logging.debug(' Log {0} after {1:.1f} secs'.format(self.getName(), self.getTime()))

	def WakeOnLan(self):
		logging.debug('WakeOnLan %s %s', self._devicename, self._macaddress)
		pexpect.run('wakeonlan {0}'.format(self._macaddress))

	def RepeatStart(self):
		self.WakeOnLan()

	def WaitForHost(self):
		logging.debug(' Wait for %s', self.getName())
		self._timeout.Reset()
		exitstatus = 1
		count = 0
		while (exitstatus != 0) and not self._timeout.isExpired():
			time.sleep(0.5)
			#run_time = watchclock.Watchclock()
			(command_output, exitstatus) = pexpect.run('ping -i 0.3 -c1 {0}'.format(self._devicename), withexitstatus=True)
			#logging.debug('fping delay {0} {1:.1f} secs'.format(self.getName(), run_time.getTime()))
			count += 1 # do not send the repeat too often
			if exitstatus != 0 and count%4==0:
				self.RepeatStart()
		ret = not self._timeout.isExpired()
		if ret:
			logging.debug('Found {0} after {1:.1f} secs'.format(self.getName(), self.getTime()))
		else:
			logging.debug('Failed, ping exit {0}, {1}, {2}'.format(self.getName(), exitstatus, command_output))
		return ret

	def Remote(self, host, cmd):
		command = "ssh {0} '{1}'".format(host, cmd)
		logging.debug('{0}'.format(command))
		(command_output, exitstatus) = pexpect.run(command, withexitstatus=True)
		return exitstatus

	def SetState(self, state):
		self._start_time.Reset()
		logging.debug('SetState {0} {1} {2}'.format(self.getName(), state))
		self._available.wait()
		self._work.acquire()
		self._oldstate = self._newstate
		self._newstate, self._StateParam = state
		self._newmod = Modifier.NONE
		self._work.notify()
		self._work.release()
		if not self.is_alive():
			logging.debug('SetState {0} failed! Thread is dead.'.format(self.getName()))

	def SetModifier(self, mod):
		self._start_time.Reset()
		logging.debug(' SetModifier {0} {1} {2}'.format(self.getName(), mod))
		self._available.wait()
		self._work.acquire()
		self._newmod, self._ModParam = mod
		self._work.notify()
		self._work.release()
		if not self.is_alive():
			logging.debug('SetModifier {0} failed! Thread is dead.'.format(self.getName()))

	# runs as a thread
	def run(self):
		while self._newstate!=States.TERMINATE:
			if self._newmod != Modifier.NONE:
				self.work_modifier()
			else:
				self.work_state()

			self._available.set()
			self._work.acquire()
			self._work.wait()
			self._work.release()
		logging.debug('thread {0} ended'.format(self.getName()))

	# runs as a thread
	def work_modifier(self):
		logging.debug(' work_modifier {0} self._newmod {1}'.format(self.getName(), self._newmod))
		if self._newmod==Modifier.MUTE:
			self.GlobalMute()
		elif self._newmod==Modifier.UNMUTE:
			self.GlobalUnMute()
		elif self._newmod==Modifier.TOGGLEMUTE:
			self.ToggleGlobalMute()
		elif self._newmod==Modifier.USESPEAKER:
			self.UseSpeaker()
		self._self._newmod = Modifier.NONE

	# runs as a thread
	def work_state(self):
		logging.debug(' work_state {0} self._newstate {1}'.format(self.getName(), self._newstate))
		if self._newstate==States.OFF:
			self.TurnOff()
		elif self._newstate==States.WATCHTV:
			self.WatchTV()
		elif self._newstate==States.WATCHTVMOVIE:
			self.WatchTvMovie()
		elif self._newstate==States.WATCHBRMOVIE:
			self.WatchBrMovie()
		elif self._newstate==States.LISTENMUSICDLNA:
			self.ListenMusic()
		elif self._newstate==States.LISTENRADIO:
			self.ListenRadio()
		elif self._newstate==States.LISTENIRADIO:
			self.ListenIRadio()
		elif self._newstate==States.CHROMECAST:
			self.WatchChromecast()
		elif self._newstate==States.TV2DLNA:
			self.WatchDlnaOnTV()
		elif self._newstate==States.WII:
			self.PlayWii()
		logging.debug(f' Done {0} after {1:.1f} secs'.format(self.getName(), self.getTime()))

	def SetIrCommand(self, code):
		pass

	def TurnOn(self):
		logging.debug(' %s On', self.getName())

	def TurnOff(self):
		logging.debug(' %s Off', self.getName())

	def ListenRadio(self):
		pass

	def ListenIRadio(self):
		pass

	def WatchBrMovie(self):
		pass

	def WatchChromecast(self):
		pass

	def WatchDlnaOnTV(self):
		pass

	def UseSpeaker(self):
		pass

	def PlayWii(self):
		pass

	def GlobalMute(self):
		self._GlobalMute = True

	def GlobalUnMute(self):
		self._GlobalMute = False

	def ToggleGlobalMute(self):
		self._GlobalMute ^= True


