"""
#    TOP2049 Open Source programming suite
#
#    ZIF socket layout generator
#
#    Copyright (c) 2010 Michael Buesch <mb@bu3sch.de>
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
from top_xxxx import *

#FIXME This needs to be fixed to properly support devices with multiple possible
# VPP layouts. It needs to be split up to do the chip-placement and VPP-enabling
# in two separate steps.

class LayoutGenerator:
	"Layout generator baseclass."

	class MapError(Exception): pass

	def __init__(self):
		pass

	def setProgrammerType(self, programmer="TOP2049"):
		supportedDevices = {
			# Map  deviceName : layoutModules, ZIF-pin-count
			"TOP2049"	: (top2049.vccx_layouts, top2049.vpp_layouts,
					   top2049.gnd_layouts, 48)
		}
		try:
			(vccx_layouts, vpp_layouts, gnd_layouts, zifPins) = \
				supportedDevices[programmer]
		except (KeyError), e:
			raise TOPException("Programmer " + programmer + " not supported")
		self.vccxLayout = vccx_layouts.VCCXLayout()
		self.vppLayout = vpp_layouts.VPPLayout()
		self.gndLayout = gnd_layouts.GNDLayout()
		self.zifPins = zifPins

	def setPins(self, vccxPin, vppPins, gndPin):
		"""Load the supply pin locations.
		vppPins may either be one pin number or a list of pin numbers or None."""
		self.vccxPin = vccxPin
		if vppPins is None:
			self.vppPins = None
		else:
			try:
				self.vppPins = list(vppPins)
			except TypeError:
				self.vppPins = [ vppPins, ]
		self.gndPin = gndPin
		self.verifyPins()

	def verifyPins(self):
		pass

	def maxOffset(self, upsideDown):
		"Returns the max possible chip offset (in the ZIF socket)"
		raise TOPException("Reimplement me")

	def mapToZIF(self, offset, upsideDown):
		"Tries to map the chip into the ZIF socket"
		raise TOPException("Reimplement me")

	def zifLayoutAsciiArt(self):
		"Returns nice ascii ART of the mapped ZIF socket"
		raise TOPException("Reimplement me")

	def zifPinAssignments(self):
		"Returns a string describing the pin assignments"
		raise TOPException("Reimplement me")

	def recalculate(self):
		"Redo the mapping calculation"
		for upsideDown in (False, True):
			offset = self.maxOffset(upsideDown)
			while offset >= 0:
				try:
					self.mapToZIF(offset, upsideDown)
				except (LayoutGenerator.MapError), e:
					offset -= 1
					continue
				return
		raise TOPException("Did not find a possible valid layout for the setup")

	def applyGNDLayout(self, top):
		"Send the GND layout to hardware"
		(id, mask) = self.result_GND
		#print "Loading autogenerated GND layout %d, 0x%X" % (id, mask)
		top.gnd.setLayoutID(id)

	def applyVCCXLayout(self, top):
		"Send the VCCX layout to hardware"
		(id, mask) = self.result_VCCX
		#print "Loading autogenerated VCCX layout %d, 0x%X" % (id, mask)
		top.vccx.setLayoutID(id)

	def applyVPPLayout(self, top):
		"Send the VPP layout to hardware"
		#print "Resetting VPP layout"
		top.vpp.setLayoutMask(0) # Reset
		if self.result_VPP:
			for (id, mask) in self.result_VPP:
				#print "Loading autogenerated VPP layout %d, 0x%X" % (id, mask)
				top.vpp.setLayoutID(id)

	def findSingleLayout(self, layoutDefs, zifBitmask):
		# Returns an (id, mask) tuple
		for (id, mask) in layoutDefs.supportedLayouts():
			if zifBitmask == mask:
				break
		else:
			raise self.MapError()
		return (id, mask)

	def findCumulativeLayout(self, layoutDefs, zifBitmask):
		# Returns a list of (id, mask) tuples
		result = []
		for (id, mask) in layoutDefs.supportedLayouts():
			if zifBitmask == 0:
				break
			if mask == 0:
				continue
			if mask & zifBitmask == mask:
				result.append( (id, mask) )
				zifBitmask &= ~mask
		if zifBitmask:
			raise self.MapError()
		return result

class LayoutGeneratorDIP(LayoutGenerator):
	"Layout generator for DIP packages."

	def __init__(self, nrPins):
		LayoutGenerator.__init__(self)
		self.nrPins = nrPins

	def verifyPins(self):
		LayoutGenerator.verifyPins(self)
		if self.nrPins < 2 or self.nrPins > self.zifPins or self.nrPins % 2 != 0:
			raise TOPException("Invalid DIP package")
		if self.vccxPin < 1 or self.vccxPin > self.nrPins:
			raise TOPException("Invalid VCCX pin number for the selected package")
		if self.vppPins is not None:
			for vppPin in self.vppPins:
				if vppPin < 1 or vppPin > self.nrPins:
					raise TOPException("Invalid VPP pin number for the selected package")
		if self.gndPin < 1 or self.gndPin > self.nrPins:
			raise TOPException("Invalid GND pin number for the selected package")

	def maxOffset(self, upsideDown):
		return self.zifPins // 2 - self.nrPins // 2

	def mapToZIF(self, offset, upsideDown):
		if offset < 0 or offset > self.maxOffset(upsideDown):
			raise self.MapError()

		# Find a GND layout
		zifGndPin = self.__pin2zif(self.gndPin, offset, upsideDown)
		self.result_GND = self.findSingleLayout(self.gndLayout,
							(1 << (zifGndPin - 1)))

		# Find a VCCX layout
		zifVccxPin = self.__pin2zif(self.vccxPin, offset, upsideDown)
		self.result_VCCX = self.findSingleLayout(self.vccxLayout,
							 (1 << (zifVccxPin - 1)))

		# Find a (possibly cumulative) VPP layout
		if self.vppPins is None:
			self.result_VPP = None
		else:
			zifVppMask = 0
			for vppPin in self.vppPins:
				pin = self.__pin2zif(vppPin, offset, upsideDown)
				zifVppMask |= (1 << (pin - 1))
			self.result_VPP = self.findCumulativeLayout(self.vppLayout,
								    zifVppMask)

		# Also store the chip orientation for later use.
		self.result_upsideDown = upsideDown
		self.result_offset = offset

	def __pin2zif(self, dipPin, offset, upsideDown):
		if upsideDown:
			if dipPin > self.nrPins // 2:
				# Right side of DIP
				dipPin -= self.nrPins // 2
				return dipPin + offset
			else:
				# Left side of DIP
				return self.zifPins - self.nrPins // 2 + dipPin - offset
		else:
			if dipPin > self.nrPins // 2:
				# Right side of DIP
				dipPin -= self.nrPins // 2
				return self.zifPins - self.nrPins // 2 + dipPin - offset
			else:
				# Left side of DIP
				return dipPin + offset

	def zifLayoutAsciiArt(self):
		ret =  "T     ZIF socket\n"
		ret += "^--o==============o\n"
		for zp in range(1, self.zifPins // 2 + 1):
			if zp < self.result_offset + 1 or \
			   zp > self.result_offset + self.nrPins // 2:
				ret += "%2d |----- || -----| %2d\n" %\
					(zp, self.zifPins + 1 - zp)
			else:
				if zp == self.result_offset + 1 and \
				   not self.result_upsideDown:
					ret += "%2d |-- 1##..##o --| %2d\n" %\
						(zp, self.zifPins + 1 - zp)
				elif zp == self.result_offset + self.nrPins // 2 and \
				     self.result_upsideDown:
					ret += "%2d |-- o##''##1 --| %2d\n" %\
						(zp, self.zifPins + 1 - zp)
				else:
					ret += "%2d |-- o######o --| %2d\n" %\
						(zp, self.zifPins + 1 - zp)
		ret += "   o==============o\n"
		return ret

	def zifPinAssignments(self):
		ret =  "VCCX ZIF pins: " + self.__bitmask2zifList(self.result_VCCX[1]) + "\n"
		if self.result_VPP:
			vppBitmask = 0
			for (id, mask) in self.result_VPP:
				vppBitmask |= mask
			ret += "VPP ZIF pins:  " + self.__bitmask2zifList(vppBitmask) + "\n"
		ret += "GND ZIF pins:  " + self.__bitmask2zifList(self.result_GND[1]) + "\n"
		return ret

	def __bitmask2zifList(self, bitmask):
		ret = ""
		for bit in range(0, self.zifPins):
			if bitmask & (1 << bit):
				if ret:
					ret += ","
				ret += str(bit + 1)
		return ret

def createLayoutGenerator(package):
	p = package.upper()
	try:
		if p.startswith("DIP"):
			nrPins = int(p[3:])
			return LayoutGeneratorDIP(nrPins)
		else:
			raise ValueError()
	except (ValueError), e:
		raise TOPException("Unknown package type " + package)
