"""
#    TOP2049 Open Source programming suite
#
#    Chip support
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

from util import *
from layout_generator import *
from user_interface import *


class Chip:
	SUPPORT_ERASE		= (1 << 0)
	SUPPORT_SIGREAD		= (1 << 1)
	SUPPORT_PROGMEMREAD	= (1 << 2)
	SUPPORT_PROGMEMWRITE	= (1 << 3)
	SUPPORT_EEPROMREAD	= (1 << 4)
	SUPPORT_EEPROMWRITE	= (1 << 5)
	SUPPORT_FUSEREAD	= (1 << 6)
	SUPPORT_FUSEWRITE	= (1 << 7)
	SUPPORT_LOCKREAD	= (1 << 8)
	SUPPORT_LOCKWRITE	= (1 << 9)

	@staticmethod
	def chipSupportsAttr(chipImplClass, attribute):
		"""Check if a chip implementation supports a feature.
		'attribute' is the class member function to check for"""
		# This works by checking whether the subclass overloaded
		# the member function attribute.
		if str(type(chipImplClass)) == "<type 'instance'>":
			# This is an instance. Get the class
			chipImplClass = chipImplClass.registeredChip.chipImplClass
		return getattr(chipImplClass, attribute) != getattr(Chip, attribute)

	@staticmethod
	def getSupportFlags(chip):
		"Get the SUPPORT_... flags for this chip"
		flags = 0
		if Chip.chipSupportsAttr(chip, "erase"):
			flags |= Chip.SUPPORT_ERASE
		if Chip.chipSupportsAttr(chip, "readSignature"):
			flags |= Chip.SUPPORT_SIGREAD
		if Chip.chipSupportsAttr(chip, "readProgmem"):
			flags |= Chip.SUPPORT_PROGMEMREAD
		if Chip.chipSupportsAttr(chip, "writeProgmem"):
			flags |= Chip.SUPPORT_PROGMEMWRITE
		if Chip.chipSupportsAttr(chip, "readEEPROM"):
			flags |= Chip.SUPPORT_EEPROMREAD
		if Chip.chipSupportsAttr(chip, "writeEEPROM"):
			flags |= Chip.SUPPORT_EEPROMWRITE
		if Chip.chipSupportsAttr(chip, "readFuse"):
			flags |= Chip.SUPPORT_FUSEREAD
		if Chip.chipSupportsAttr(chip, "writeFuse"):
			flags |= Chip.SUPPORT_FUSEWRITE
		if Chip.chipSupportsAttr(chip, "readLockbits"):
			flags |= Chip.SUPPORT_LOCKREAD
		if Chip.chipSupportsAttr(chip, "writeLockbits"):
			flags |= Chip.SUPPORT_LOCKWRITE
		return flags

	def __init__(self, chipPackage=None, chipPinVCCX=None, chipPinsVPP=None, chipPinGND=None):
		"""chipPackage is the ID string for the package.
		May be None, if no initial auto-layout is required.
		chipPinVCCX is the required VCCX pin on the package.
		chipPinVPP is the required VPP pin on the package.
		chipPinGND is the required GND pin on the package."""

		self.printPrefix = True
		self.__chipPackage = chipPackage
		self.__chipPinVCCX = chipPinVCCX
		self.__chipPinsVPP = chipPinsVPP
		self.__chipPinGND = chipPinGND

	def setTOP(self, top):
		self.top = top

	def setChipID(self, chipID):
		self.chipID = chipID

	def setProgrammerType(self, programmerType):
		"Set the TOP programmer type. See class TOP.TYPE_..."
		self.programmerType = programmerType

	def printWarning(self, message, newline=True):
		if self.printPrefix:
			message = self.chipID + ": " + message
		self.top.printWarning(message, newline)
		self.printPrefix = newline

	def printInfo(self, message, newline=True):
		if self.printPrefix:
			message = self.chipID + ": " + message
		self.top.printInfo(message, newline)
		self.printPrefix = newline

	def printDebug(self, message, newline=True):
		if self.printPrefix:
			message = self.chipID + ": " + message
		self.top.printDebug(message, newline)
		self.printPrefix = newline

	def throwError(self, message):
		raise TOPException(self.chipID + ": " + message)

	def generateVoltageLayouts(self):
		if self.__chipPackage:
			self.generator = createLayoutGenerator(self.__chipPackage)
			self.generator.setProgrammerType(self.programmerType)
			self.generator.setPins(vccxPin=self.__chipPinVCCX,
					       vppPins=self.__chipPinsVPP,
					       gndPin=self.__chipPinGND)
			self.generator.recalculate()

	def getLayoutGenerator(self):
		if self.__chipPackage:
			return self.generator
		return None

	def applyVCCX(self, turnOn):
		"Turn VCCX on, using the auto-layout."
		if turnOn:
			try:
				generator = self.generator
			except (AttributeError), e:
				self.throwError("BUG: Using auto-layout, but did not initialize it.")
			generator.applyVCCXLayout(self.top)
		else:
			self.top.vccx.setLayoutMask(0)

	def applyVPP(self, turnOn, packagePinsToTurnOn=[]):
		"""Turn VPP on, using the auto-layout.
		packagePinsToTurnOn is a list of pins on the package to drive to VPP.
		If it is not passed (or an empty list), all VPP pins of the layout are turned on.
		The parameter is unused, if turnOn=False."""
		if turnOn:
			try:
				generator = self.generator
			except (AttributeError), e:
				self.throwError("BUG: Using auto-layout, but did not initialize it.")
			generator.applyVPPLayout(self.top, packagePinsToTurnOn)
		else:
			self.top.vpp.setLayoutMask(0)

	def applyGND(self, turnOn):
		"Turn GND on, using the auto-layout."
		if turnOn:
			try:
				generator = self.generator
			except (AttributeError), e:
				self.throwError("BUG: Using auto-layout, but did not initialize it.")
			generator.applyGNDLayout(self.top)
		else:
			self.top.gnd.setLayoutMask(0)

	def progressMeterInit(self, message, nrSteps):
		self.top.progressMeterInit(AbstractUserInterface.PROGRESSMETER_CHIPACCESS,
					   message, nrSteps)

	def progressMeterFinish(self):
		self.top.progressMeterFinish(AbstractUserInterface.PROGRESSMETER_CHIPACCESS)

	def progressMeter(self, step):
		self.top.progressMeter(AbstractUserInterface.PROGRESSMETER_CHIPACCESS,
				       step)

	def initializeChip(self):
		pass # Override me in the subclass, if required.

	def shutdownChip(self):
		pass # Override me in the subclass, if required.

	def readSignature(self):
		# Override me in the subclass, if required.
		raise TOPException("Signature reading not supported on " + self.chipID)

	def erase(self):
		# Override me in the subclass, if required.
		raise TOPException("Chip erasing not supported on " + self.chipID)

	def readProgmem(self):
		# Override me in the subclass, if required.
		raise TOPException("Program memory reading not supported on " + self.chipID)

	def writeProgmem(self, image):
		# Override me in the subclass, if required.
		raise TOPException("Program memory writing not supported on " + self.chipID)

	def readEEPROM(self):
		# Override me in the subclass, if required.
		raise TOPException("EEPROM reading not supported on " + self.chipID)

	def writeEEPROM(self, image):
		# Override me in the subclass, if required.
		raise TOPException("EEPROM writing not supported on " + self.chipID)

	def readFuse(self):
		# Override me in the subclass, if required.
		raise TOPException("Fuse reading not supported on " + self.chipID)

	def writeFuse(self, image):
		# Override me in the subclass, if required.
		raise TOPException("Fuse writing not supported on " + self.chipID)

	def readLockbits(self):
		# Override me in the subclass, if required.
		raise TOPException("Lockbit reading not supported on " + self.chipID)

	def writeLockbits(self, image):
		# Override me in the subclass, if required.
		raise TOPException("Lockbit writing not supported on " + self.chipID)

registeredChips = []

class BitDescription:
	def __init__(self, bitNr, description):
		self.bitNr = bitNr
		self.description = description

class ChipDescription:
	def __init__(self, chipImplClass, bitfile, chipID="",
		     runtimeID=(0,0),
		     description="", fuseDesc=(), lockbitDesc=(),
		     packages=None, comment="",
		     broken=False, internal=False):
		"""Chip implementation class description.
		chipImplClass	=> The implementation class of the chip.
		bitfile		=> The bitfile ID string of the chip.
		chipID		=> The chip-ID string. Will default to the bitfile ID string.
		runtimeID	=> The runtime-ID is a tuple of two numbers that uniquely
				   identifies a loaded FPGA configuration. The first number in the
				   tuple is an ID number and the second number is a revision number.
		description	=> Human readable chip description string.
		fuseDesc	=> Tuple of fuse bits descriptions (BitDescription(), ...)
		lockbitDesc	=> Tuple of lock bits descriptions (BitDescription(), ...)
		packages	=> List of supported packages.
				   Each entry is a tuple of two strings: ("PACKAGE", "description")
		comment		=> Additional comment string.
		broken		=> Boolean flag to mark the implementation as broken.
		internal	=> Boolean flag to mark algorithms for internal use.
		"""

		if not chipID:
			chipID = bitfile
		self.chipImplClass = chipImplClass
		self.bitfile = bitfile
		self.chipID = chipID
		self.runtimeID = runtimeID
		self.description = description
		self.fuseDesc = fuseDesc
		self.lockbitDesc = lockbitDesc
		self.packages = packages
		self.comment = comment
		self.broken = broken
		self.internal = internal
		registeredChips.append(self)

	@staticmethod
	def find(programmerType, chipID, allowBroken=False):
		"Find a chip implementation by ID and return an instance of it."
		for chip in registeredChips:
			if chip.broken and not allowBroken:
				continue
			if chip.chipID.lower() == chipID.lower():
				instance = chip.chipImplClass()
				instance.registeredChip = chip
				instance.setChipID(chip.chipID)
				instance.setProgrammerType(programmerType)
				instance.generateVoltageLayouts()
				return (chip, instance)
		return (None, None)

	@staticmethod
	def dumpAll(fd, verbose=1, showBroken=True):
		"Dump all supported chips to file fd."
		count = 0
		for chip in registeredChips:
			if chip.broken and not showBroken:
				continue
			if chip.internal:
				continue
			count = count + 1
			if count >= 2:
				fd.write("\n")
			chip.dump(fd, verbose)

	def dump(self, fd, verbose=1):
		"Dump information about a registered chip to file fd."
		if self.description:
			fd.write(self.description)
		else:
			fd.write(self.bitfile)
		if self.broken:
			fd.write("  (broken implementation)")
		fd.write("\n")
		if verbose >= 1:
			fd.write("%25s:  %s\n" % ("ChipID", self.chipID))
		if verbose >= 2:
			fd.write("%25s:  %s\n" % ("BIT-file", self.bitfile))
		if verbose >= 3 and self.packages:
			for (package, description) in self.packages:
				if description:
					description = "  (" + description + ")"
				fd.write("%25s:  %s%s\n" % ("Supported package", package, description))
		if verbose >= 4:
			supportedFeatures = (
				(Chip.SUPPORT_ERASE,		"Full chip erase"),
				(Chip.SUPPORT_SIGREAD,		"Chip signature reading"),
				(Chip.SUPPORT_PROGMEMREAD,	"Program memory reading (flash)"),
				(Chip.SUPPORT_PROGMEMWRITE,	"Program memory writing (flash)"),
				(Chip.SUPPORT_EEPROMREAD,	"(E)EPROM memory reading"),
				(Chip.SUPPORT_EEPROMWRITE,	"(E)EPROM memory writing"),
				(Chip.SUPPORT_FUSEREAD,		"Fuse bits reading"),
				(Chip.SUPPORT_FUSEWRITE,	"Fuse bits writing"),
				(Chip.SUPPORT_LOCKREAD,		"Lock bits reading"),
				(Chip.SUPPORT_LOCKWRITE,	"Lock bits writing"),
			)
			supportFlags = Chip.getSupportFlags(self.chipImplClass)
			for (flag, description) in supportedFeatures:
				if flag & supportFlags:
					fd.write("%25s:  %s\n" % ("Support for", description))
		if verbose >= 2 and self.comment:
			fd.write("%25s:  %s\n" % ("Comment", self.comment))
