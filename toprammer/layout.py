#!/usr/bin/env python
"""
#    TOP2049 Open Source programming suite
#
#    ZIF socket layout generator
#
#    Copyright (c) 2010 Michael Buesch <m@bues.ch>
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

from layout_generator import *
from main import *
from chip import *
import getopt
import sys


class FakeTOP(object):
	def __init__(self, topType):
		self.topType = topType

	def getProgrammerType(self):
		return self.topType

def usage():
	print("Toprammer ZIF socket layout generator v{}".format(VERSION))
	print("")
	print("Usage: %s [OPTIONS]") % sys.argv[0]
	print("")
	print("Mandatory options:")
	print(" -d|--device TOPxxxx    The TOPxxxx device that is used.")
	print("                        Possible choices are: TOP2049")
	print(" -p|--package DIPxx     The package type of the DUT.")
	print("                        Package may also be the name of a supported chip.")
	print("                        In this case, --vcc, --vpp and --gnd are ignored.")
	print(" -v|--vcc PIN           Set VCC pin number, relative to the package.")
	print(" -P|--vpp PIN(s)        Set VPP pin number(s), relative to the package.")
	print("                        May be one pin number or a comma separated list of pin numbers.")
	print("                        May be omitted or NONE, if no VPP pin is required.")
	print(" -g|--gnd PIN           Set GND pin number, relative to the package.")
	print("")
	print("Optional:")
	print(" -h|--help              Print this help text")
	print(" -I|--only-insert       Only show insert-layout")
	print(" -S|--only-supply       Only show supply-layout")

def main(argv):
	package = None
	programmer = None
	vccPin = None
	vppPins = None
	gndPin = None
	showInsert = True
	showSupply = True
	try:
		(opts, args) = getopt.getopt(argv[1:],
			"d:p:hv:P:g:IS",
			[ "help", "device=", "package=", "vcc=", "vcc=", "vpp=", "gnd=",
			  "only-insert", "only-supply", ])
		for (o, v) in opts:
			if o in ("-h", "--help"):
				usage()
				return 0
			if o in ("-d", "--device"):
				programmer = v
			if o in ("-p", "--package"):
				package = v
			if o in ("-v", "--vcc", "--vcc"):
				vccPin = int(v)
			if o in ("-P", "--vpp"):
				if v.upper() == "NONE":
					vppPins = None
				else:
					vppPins = []
					for v in v.split(","):
						vppPins.append(int(v))
			if o in ("-g", "--gnd"):
				gndPin = int(v)
			if o in ("-I", "--only-insert"):
				showInsert = True
				showSupply = False
			if o in ("-S", "--only-supply"):
				showInsert = False
				showSupply = True
		if not programmer:
			print "-d|--device is mandatory!\n"
			raise ValueError()
		if not package:
			print "-p|--package is mandatory!\n"
			raise ValueError()

		generator = None
		try:
			chipDesc = ChipDescription.findOne(
				package, allowBroken=True)
			chip = chipDesc.chipImplClass.createInstance(
				FakeTOP(programmer), chipDesc)
		except (TOPException), e:
			chip = None
			if vccPin is None or gndPin is None:
				print "-v|--vcc and  -g|--gnd  " +\
					"are mandatory, if a package type is specified.\n"
				raise ValueError()

	except (getopt.GetoptError, ValueError, KeyError), e:
		usage()
		return 1
	except (TOPException), e:
		print e
		return 1
	try:
		if chip:
			try:
				generator = chip.generator
			except (AttributeError), e:
				print "The chip %s does not have a layout autogenerator. "\
					"You must specify the package type, -v, -P and -g manually." %\
					package
				return 1
		else:
			generator = createLayoutGenerator(package)
			generator.setProgrammerType(programmer.upper())
			generator.setPins(vccPin, vppPins, gndPin)
			generator.recalculate()
		if showInsert:
			print "Chip insert layout:\n"
			print generator.zifLayoutAsciiArt()
		if showSupply:
			print "\nSupply voltage pins on the ZIF:\n"
			print generator.zifPinAssignments()
	except (TOPException), e:
		print e
		return 1
	return 0

if __name__ == "__main__":
	sys.exit(main(sys.argv))
