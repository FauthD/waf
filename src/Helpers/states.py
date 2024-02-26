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

from enum import Enum, EnumMeta

# Idea found there:
# https://stackoverflow.com/questions/61796731/contains-and-python3-8-enum-enum
class MyMeta(EnumMeta):
    def __contains__(self, other):
        try:
            self(other)
        except ValueError:
            return False
        else:
            return True

class States(str, Enum, metaclass=MyMeta):
	NONE='none'
	TERMINATE='terminate'
	OFF='off'
	WATCHTV='tv'
	LISTENMUSICDLNA='dlna'
	WATCHTVMOVIE='movie'
	WATCHBRMOVIE='blueray'
	LISTENRADIO='radio'
	LISTENIRADIO='iradio'
	LISTENIRADIO1='iradio1'
	LISTENIRADIO2='iradio2'
	LISTENIRADIO3='iradio3'
	LISTENIRADIO4='iradio4'
	LISTENIRADIO5='iradio5'
	LISTENIRADIO6='iradio6'
	LISTENIRADIO7='iradio7'
	LISTENIRADIO8='iradio8'
	LISTENIRADIO9='iradio9'
	CHROMECAST='chromecast'
	TV2DLNA='tv2dlna'
	WII='wii'
	# Add new states here

class Modifier(str, Enum, metaclass=MyMeta):
	UNMUTE='unmute'
	MUTE='mute'
	TOGGLEMUTE='togglemute'
	USESPEAKER='usespeaker'
	# Add new modifiers here
