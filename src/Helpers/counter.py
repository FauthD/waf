#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import threading

class Counter():
	'A thread save counter'
	def __init__(self):
		self._lock = threading.Lock()
		self._counter = 0

	def Get(self):
		with self._lock:
			return self._counter

	def Set(self, value):
		with self._lock:
			self._counter = value

	def Clear(self):
		with self._lock:
			self._counter = 0

	def Decrement(self):
		with self._lock:
			self._counter -= 1

	def Increment(self):
		with self._lock:
			self._counter += 1
