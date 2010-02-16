"""
#    TOP2049 Open Source programming suite
#
#    TOP2049 GND layout definitions
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

class GNDLayout:
	# A list of valid IDs
	validIDs = (0, 5, 14, 15, 16, 17, 18, 19, 20, 24, 26, 27,
		28, 29, 33, 34, 35)

	def __init__(self, top):
		self.top = top
		self.layouts = []
		for id in self.validIDs:
			mask = 0
			if id:
				mask |= (1 << (id - 1))
			self.layouts.append( (id, mask) )

	def supportedLayouts(self):
		"""Returns a list of supported layouts.
		Each entry is a tuple of (id, bitmask), where bitmask is
		the ZIF layout. bit0 is ZIF-pin-1. A bit set means a hot pin."""
		return self.layouts