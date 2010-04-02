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


class Chip:
	def __init__(self, chipPackage=None, chipPinVCCX=None, chipPinsVPP=None, chipPinGND=None):
		"""chipPackage is the ID string for the package.
		May be None, if no initial auto-layout is required.
		chipPinVCCX is the required VCCX pin on the package.
		chipPinVPP is the required VPP pin on the package.
		chipPinGND is the required GND pin on the package."""

		self.printPrefix = True

		if chipPackage:
			# Initialize auto-layout
			self.__generateVoltageLayouts(chipPackage=chipPackage,
						      chipPinVCCX=chipPinVCCX,
						      chipPinsVPP=chipPinsVPP,
						      chipPinGND=chipPinGND)

	def setTOP(self, top):
		self.top = top

	def setChipID(self, chipID):
		self.chipID = chipID

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

	def __generateVoltageLayouts(self, chipPackage, chipPinVCCX, chipPinsVPP, chipPinGND):
		self.generator = createLayoutGenerator(chipPackage)
		self.generator.setProgrammerType("TOP2049")#XXX Currently the only supported programmer
		self.generator.setPins(vccxPin=chipPinVCCX,
				       vppPins=chipPinsVPP,
				       gndPin=chipPinGND)
		self.generator.recalculate()

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
		self.progressNrSteps = nrSteps
		self.progress = range(0, 100)
		self.printInfo(message + " [0%", newline=False)

	def progressMeterFinish(self):
		if not self.progressNrSteps:
			self.progressMeter(0)
		self.printInfo("100%]")

	def progressMeter(self, step):
		if self.progressNrSteps:
			percent = (step * 100 // self.progressNrSteps)
		else:
			percent = 100
		for progress in list(self.progress):
			if progress > percent:
				break
			if progress == 25:
				self.printInfo("25%", newline=False)
			elif progress == 50:
				self.printInfo("50%", newline=False)
			elif progress == 75:
				self.printInfo("75%", newline=False)
			elif progress % 2 == 0:
				self.printInfo(".", newline=False)
			self.progress.remove(progress)

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

class RegisteredChip:
	def __init__(self, chipImplClass, bitfile, chipID="",
		     description="", packages=None, comment="",
		     broken=False):
		"""Register a chip implementation class.
		chipImplClass	=> The implementation class of the chip.
		bitfile		=> The bitfile ID of the chip.
		chipID		=> The chip-ID. Will default to the value of bitfile.
		description	=> Human readable chip description string.
		packages	=> List of supported packages.
				   Each entry is a tuple of two strings: ("PACKAGE", "description")
		comment		=> Additional comment string.
		broken		=> Boolean flag to mark the implementation as broken.
		"""

		if not chipID:
			chipID = bitfile
		self.chipImplClass = chipImplClass
		self.bitfile = bitfile
		self.chipID = chipID
		self.description = description
		self.packages = packages
		self.comment = comment
		self.broken = broken
		registeredChips.append(self)

	@staticmethod
	def find(chipID, allowBroken=False):
		"Find a chip implementation by ID and return an instance of it."
		for chip in registeredChips:
			if chip.broken and not allowBroken:
				continue
			if chip.chipID.lower() == chipID.lower():
				instance = chip.chipImplClass()
				instance.setChipID(chip.chipID)
				return (chip, instance)
		return None

	@staticmethod
	def dumpAll(fd, verbose=1, showBroken=True):
		"Dump all supported chips to file fd."
		count = 0
		for chip in registeredChips:
			if chip.broken and not showBroken:
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
				("erase", "Full chip erase"),
				("readSignature", "Chip signature reading"),
				("readProgmem", "Program memory reading (flash)"),
				("writeProgmem", "Program memory writing (flash)"),
				("readEEPROM", "(E)EPROM memory reading"),
				("writeEEPROM", "(E)EPROM memory writing"),
				("readFuse", "Fuse bits reading"),
				("writeFuse", "Fuse bits writing"),
				("readLockbits", "Lock bits reading"),
				("writeLockbits", "Lock bits writing"),
			)
			for (attr, description) in supportedFeatures:
				if getattr(self.chipImplClass, attr) != getattr(Chip, attr):
					fd.write("%25s:  %s\n" % ("Support for", description))
		if verbose >= 2 and self.comment:
			fd.write("%25s:  %s\n" % ("Comment", self.comment))

