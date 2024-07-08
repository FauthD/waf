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

import logging
import threading
import time
import os
import socket
import queue
import selectors

from enum import Enum

from Helpers import WafException
from . Remote import Remote

DEFAULT_LIRC_INET_PORT = 8765

class lirc(Remote):
	'Send/receive IR codes with lirc'
	def __init__(self, cfg:dict, rx_fifo:queue.Queue):
		super().__init__(cfg, rx_fifo)
		self.socket_addr = cfg.get('host', None)
		if self.socket_addr is not None:
			self.socket_type = socket.AF_INET
			self.socket_port = cfg.get('port', DEFAULT_LIRC_INET_PORT)
			self.connect = (self.socket_addr,self.socket_port)
		else:
			self.socket_type = socket.AF_UNIX
			self.connect = cfg.get('socket', '/run/lirc/lircd')

		if self.rx_enable:
			self.receiver = LircReceiver(self.socket_type, self.connect, self.rx_fifo, self._stop_)
		else:
			self.receiver = LircDummy()
		self.StartTX()

	def StartTX(self):
		if self.tx_enable:
			self.transmitter = LircTransmitter(self.socket_type, self.connect, self._stop_)
		else:
			self.transmitter = LircDummy()


	def Stop(self):
		super().Stop()
		self.transmitter.Stop()
		self.receiver.Stop()
		self.transmitter.join()
		self.receiver.join()

	def Send(self, code):
		if self.transmitter.Send(code):
			logging.debug(f'Retry {self.connect} {code}')
			self.StartTX()
			self.transmitter.Send(code)

##############################################
class LircDummy():
	def __init__(self):
		''' just a dummy '''
		pass

	def Stop(self):
		''' just a dummy '''
		pass

	def join(self):
		''' just a dummy '''
		pass

	def Send(self, code):
		''' just a dummy '''
		return 0

SOCKET_BUFER=256
##############################################
class LircReceiver(threading.Thread):
	def __init__(self, socket_type, connect, rx_fifo:queue.Queue, stop):
		super().__init__(name='LircReceiver')
		self._stop_ = stop
		self.rx_fifo = rx_fifo
		self.connect = connect
		self.socket_type = socket_type
		self.client_socket = socket.socket(self.socket_type, socket.SOCK_STREAM)
		self.connected = False
		self.start()

	def __del__(self):
		logging.debug(f'thread {self.name} __del__')
		self.Stop()

	def Stop(self):
		logging.debug(f'thread {self.name} STOP')
		try:
			self.client_socket.shutdown(socket.SHUT_RDWR)
			self.client_socket.close()
		except Exception as e:
			logging.debug(f"thread {self.name} - {e}")

	def IsConnected(self):
		return self.connected

	def SocketConnect(self):
		while not self.connected and not self._stop_.is_set():
			if self.socket_type == socket.AF_UNIX:
				if not os.path.exists(self.connect):
					time.sleep(1)
					continue
			try:
				# connect to LIRC-UNIX-Socket
				self.client_socket.connect(self.connect)
				self.connected = True
			except socket.error as e:
				logging.error(f'{self.name} error connecting to socket "{self.connect}": {e}')
				time.sleep(1)
				continue


		if self.connected:
			logging.info(f"{self.name} connected to socket: {self.connect}")

	# runs as a thread
	def run(self):
		self.SocketConnect()
		while not self._stop_.is_set():
			data = self.client_socket.recv(SOCKET_BUFER)
			if data is None or len(data) == 0:
				break

			text = data.decode('utf-8')
			message =text.split(sep='\n')
			self.rx_fifo.put(message[0])

		# allow the other side of the fifo to exit
		self.rx_fifo.put(None)
		logging.debug(f'thread {self.name} "{self.connect}" ended')

##############################################
class LircTransmitter(LircReceiver):
	def __init__(self, socket_type, connect, stop):
		super().__init__(socket_type, connect, None, stop)
		self.name='LircTransmitter'
		self._parser = ReplyParser()
		self._select = selectors.DefaultSelector()
		self._select.register(self.client_socket, selectors.EVENT_READ)
		self._buffer = bytearray(0)
	
	# runs as a thread
	def run(self):
		self.SocketConnect()
		logging.debug(f'Connector thread {self.name} "{self.connect}" finished')

	def Send(self, code):
		if not self.IsConnected():
			return 0

		remote, key = code.split()
		cmd_string = f'SEND_ONCE {remote} {key}\n'
		try:
			#logging.debug(f'Sending {cmd_string}')
			self.client_socket.sendall(cmd_string.encode("ascii"))
		except Exception as e:
			logging.error(f"Error sending data to {self.connect}: {e}")
			return 1

		try:
			while not self._parser.is_completed() and not self._stop_.is_set():
				line = self.readline(1)
				if not line:
					raise TimeoutException('No data from lircd host.')
				self._parser.feed(line)
		except Exception as e:
			logging.error(f"Error communicating with lircd: {e}")

		return 0

######################################################################
# Taken from lirc-0.10.1 python-pkg/lirc/client.py and modified slightly
######################################################################

	def readline(self, timeout: float =1) -> str:
		''' Implements readline(). '''
		start=0
		if timeout:
			start = time.perf_counter()
		while b'\n' not in self._buffer:
			ready = self._select.select(
				start + timeout - time.perf_counter() if timeout else timeout)
			if ready == []:
				if timeout:
					raise TimeoutException(
						"readline: no data within %f seconds" % timeout)
				else:
					return ''
			self._buffer += self.client_socket.recv(4096)
		line, self._buffer = self._buffer.split(b'\n', 1)
		return line.decode('ascii', 'ignore')

######################################################################
# Below code has been taken from lirc-0.10.1 python-pkg/lirc/client.py
######################################################################

class Reply(object):
	''' The status/result from parsing a command reply.

	Attributes:
		result: Enum Result, reflects parser state.
		success: bool, reflects SUCCESS/ERROR.
		data: List of lines, the command DATA payload.
		sighup: bool, reflects if a SIGHUP package has been received
				(these are otherwise ignored).
		last_line: str, last input line (for error messages).
	'''
	def __init__(self):
		self.result = Result.INCOMPLETE
		self.success = None
		self.data = []
		self.sighup = False
		self.last_line = ''


class ReplyParser(Reply):
	''' Handles the actual parsing of a command reply.  '''

	def __init__(self):
		Reply.__init__(self)
		self._state = self._State.BEGIN
		self._lines_expected = 0
		self._buffer = bytearray(0)

	def is_completed(self) -> bool:
		''' Returns true if no more reply input is required. '''
		return self.result != Result.INCOMPLETE

	def feed(self, line: str):
		''' Enter a line of data into parsing FSM, update state. '''

		fsm = {
			self._State.BEGIN: self._begin,
			self._State.COMMAND: self._command,
			self._State.RESULT: self._result,
			self._State.DATA: self._data,
			self._State.LINE_COUNT: self._line_count,
			self._State.LINES: self._lines,
			self._State.END: self._end,
			self._State.SIGHUP_END: self._sighup_end
		}
		line = line.strip()
		if not line:
			return
		self.last_line = line
		fsm[self._state](line)
		if self._state == self._State.DONE:
			self.result = Result.OK

##
#  @defgroup FSM Internal parser FSM
#  @{
#  Internal parser FSM.
#  pylint: disable=missing-docstring,redefined-variable-type

	class _State(Enum):
		''' Internal FSM state. '''
		BEGIN = 1
		COMMAND = 2
		RESULT = 3
		DATA = 4
		LINE_COUNT = 5
		LINES = 6
		END = 7
		DONE = 8
		NO_DATA = 9
		SIGHUP_END = 10

	def _bad_packet_exception(self, line):
		self.result = Result.FAIL
		raise BadPacketException(
			'Cannot parse: %s\nat state: %s\n' % (line, self._state))

	def _begin(self, line):
		if line == 'BEGIN':
			self._state = self._State.COMMAND

	def _command(self, line):
		if not line:
			self._bad_packet_exception(line)
		elif line == 'SIGHUP':
			self._state = self._State.SIGHUP_END
			self.sighup = True
		else:
			self._state = self._State.RESULT

	def _result(self, line):
		if line in ['SUCCESS', 'ERROR']:
			self.success = line == 'SUCCESS'
			self._state = self._State.DATA
		else:
			self._bad_packet_exception(line)

	def _data(self, line):
		if line == 'END':
			self._state = self._State.DONE
		elif line == 'DATA':
			self._state = self._State.LINE_COUNT
		else:
			self._bad_packet_exception(line)

	def _line_count(self, line):
		try:
			self._lines_expected = int(line)
		except ValueError as ve:
			self._bad_packet_exception(line)
			logging.error(f'value error line 325, lirc.py, DF: {ve}')
		if self._lines_expected == 0:
			self._state = self._State.END
		else:
			self._state = self._State.LINES

	def _lines(self, line):
		self.data.append(line)
		if len(self.data) >= self._lines_expected:
			self._state = self._State.END

	def _end(self, line):
		if line != 'END':
			self._bad_packet_exception(line)
		self._state = self._State.DONE

	def _sighup_end(self, line):
		if line == 'END':
			ReplyParser.__init__(self)
			self.sighup = True
		else:
			self._bad_packet_exception(line)

## @}
#  FSM
#  pylint: enable=missing-docstring,redefined-variable-type

## @}

class Result(Enum):
	''' Public reply parser result, available when completed. '''
	OK = 1
	FAIL = 2
	INCOMPLETE = 3

class BadPacketException(Exception):
	''' Malformed or otherwise unparsable packet received. '''
	pass

class TimeoutException(Exception):
	''' Timeout receiving data from remote host.'''
	pass
