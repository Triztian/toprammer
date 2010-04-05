"""
#    TOP2049 Open Source programming suite
#
#    Atmel Mega8 DIP28 support
#
#    Copyright (c) 2009-2010 Michael Buesch <mb@bu3sch.de>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

from chip_atmega_common import *


class Chip_ATMega8DIP28(Chip_ATMega_common):
	def __init__(self):
		Chip_ATMega_common.__init__(self,
			chipPackage = "DIP28",
			chipPinVCCX = 7,
			chipPinsVPP = 1,
			chipPinGND = 8,
			signature = "\x1E\x93\x07",
			flashPageSize = 32,
			flashPages = 128,
			eepromPageSize = 4,
			eepromPages = 128)

RegisteredChip(
	Chip_ATMega8DIP28,
	bitfile = "atmega8dip28",
	runtimeID = (0x0003, 0x01),
	description = "Atmel AtMega8",
	packages = ( ("DIP28", ""), )
)
