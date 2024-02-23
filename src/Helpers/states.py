#!/usr/bin/python3
#
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

from enum import Enum

class States(Enum):
	NONE=-2
	TERMINATE=-1
	OFF=0
	WATCHTV=1
	LISTENMUSICDLNA=2
	WATCHTVMOVIE=3
	WATCHBRMOVIE=4
	LISTENRADIO=5
	LISTENIRADIO=6
	CHROMECAST=7
	TV2DLNA=8
	WII=9

class Modifier(Enum):
	NONE=0
	UNMUTE=1
	MUTE=2
	TOGGLEMUTE=3
	USESPEAKER=4

