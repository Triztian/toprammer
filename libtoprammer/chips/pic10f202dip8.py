"""
#    TOP2049 Open Source programming suite
#
#   Microchip PIC10F202, PIC10F206 and PIC10f222 DIP8
#
#    Copyright (c) 2012 Pavel Stemberk <stemberk@gmail.com>
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

from microchip_common import *

class Chip_Pic18F202dip8(Chip_Microchip_common):
	voltageVDD = 5
	voltageVPP = 13
	#CONFIGURATION WORD FOR PIC10F200/202/204/206
	#X X X X   X X X MCLRE     /CP WDT X X
	logicalFlashSize = 0x400
	userIDLocationSize = 4

    	def __init__(self):
	    	Chip_Microchip_common.__init__(self,
			chipPackage="DIP8",
			chipPinVCC=2,
			chipPinsVPP=8,
			chipPinGND=7,
			signature="\x09\x18\x24\x35",
			flashPageSize=0x200,
			flashPages=1,
			eepromPageSize=0,
			eepromPages=0,
			fuseBytes=2
			)
		self.configWordAddr = self.logicalFlashSize - 1
		self.osccalAddr = self.flashPageSize - 1
		self.userIDLocationAddr = self.flashPageSize
		self.osccalBackupAddr = self.userIDLocationAddr + self.userIDLocationSize

ChipDescription(
	Chip_Pic18F202dip8,
	bitfile = "pic10fXXXdip8",
	chipID = "pic10f202dip8",
	runtimeID = (0x000D, 0x01),
	chipVendors = "Microchip",
	description = "PIC10F202, PIC10F206, PIC10F222",
	packages = (("DIP8", ""),),
	maintainer = "Pavel Stemberk <stemberk@gmail.com>",
)