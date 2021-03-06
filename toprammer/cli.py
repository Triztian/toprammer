#!/usr/bin/env python
"""
#    TOP2049 Open Source programming suite
#
#    Commandline utility
#
#    Copyright (c) 2009-2013 Michael Buesch <m@bues.ch>
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

from main import *
from util import *
import getopt


def usage():
	print("TOP2049 Open Source programming suite v{}".format(VERSION))
	print("")
	print("Usage: {} [OPTIONS] [ACTIONS]".format(sys.argv[0]))
	print("")
	print("--gui					Initiate the Graphical User Interface")
	print(" -c|--chip-id            The ID of the handled chip. (mandatory)")
	print("                         See -t|--list for a list of supported chips.")
	print("")
	print("Optional:")
	print(" -C|--chip-opt NAME=VAL  Set a chip-id specific option.")
	print("                         Use  -c CHIPID -t  to get a list of options.")
	print("")
	print("Actions:")
	print(" -s|--read-sig FILE      Read the signature bytes")
	print(" -x|--erase              Erase the chip")
	print(" -T|--test               Run chip unit-test")
	print("")
	print(" -p|--read-prog FILE     Read the program memory")
	print(" -P|--write-prog FILE    Write the program memory")
	print("")
	print(" -e|--read-eeprom FILE   Read the EEPROM")
	print(" -E|--write-eeprom FILE  Write the EEPROM")
	print("")
	print(" -f|--read-fuse FILE     Read the fuse bits")
	print(" -F|--write-fuse FILE    Write the fuse bits")
	print("")
	print(" -l|--read-lock FILE     Read the lock bits")
	print(" -L|--write-lock FILE    Write the lock bits")
	print("")
	print(" -r|--read-ram FILE      Read the RAM")
	print(" -R|--write-ram FILE     Write the RAM")
	print("")
	print(" -a|--read-uil FILE      Read the User ID Location")
	print(" -A|--write-uil FILE     Write the User ID Location")
	print("")
	print("Other options:")
	print(" -t|--list               Print a list of supported chips and exit.")
	print("                         Use -V|--verbose to control the list verbosity (0-4)")
	print(" -d|--device DEVID       Use a specific programmer. For USB:")
	print("                         usb:BUSNR.DEVNR")
	print("                         First found programmer is used, if not given.")
	print(" -V|--verbose LEVEL      Set the verbosity level:")
	print("                         0 => show warnings")
	print("                         1 => also show informational messages (default)")
	print("                         2 => also show debugging messages")
	print("                         3 => also dump all USB commands")
	print(" -o|--force LEVEL        Set the force level. Default = 0")
	print("                         Note that any value greater than 0 may brick devices")
	print(" -U|--force-upload       Force upload the bitfile, even if it already appears")
	print("                         to be uploaded.")
	print(" -Q|--noqueue            Disable command queuing. Really slow!")
	print(" -B|--broken             Also use broken algorithms")
	print(" -I|--in-format FMT      Input file format. Default = autodetect")
	print(" -O|--out-format FMT     Output file format. Default = bin")
	print("")
	print("File formats (FMT):")
	print(" auto                    Autodetect. (input only)")
	print(" bin                     Raw binary data")
	print(" ihex                    Intel hex")
	print(" ihex-raw                Raw Intel hex (don't interpret sections)")
	print(" ahex                    Hex with ASCII dump")


def fileOut(filename, fmtString, data):
	"""Write the output file"""

	handler = get_IO_handler(data, fmtString)
	data = handler.fromBinary(data)
	if filename == "-":
		sys.stdout.write(data)
	else:
		open(filename, "w+b").write(data)

def fileIn(top, action, filename, fmtString):
	"""Read a file and execute an action"""

	data = sys.stdin.read() if filename == '-' else open(filename, "rb").read()
	handler = get_IO_handler(data, fmtString)

	if isinstance(handler, IO_ihex):
		interp = top.getChip().getIHexInterpreter()
		interp.interpret(data)

		readRaw = True if interp.cumulativeSupported() else fmtString.endswith("-raw")

		if action == "write-prog":
			binData = interp.getProgmem(dontInterpretSections = readRaw)
		elif action == "write-eeprom":
			binData = interp.getEEPROM(dontInterpretSections = readRaw)
		elif action == "write-fuse":
			binData = interp.getFusebits(dontInterpretSections = readRaw)
		elif action == "write-lock":
			binData = interp.getLockbits(dontInterpretSections = readRaw)
		elif action == "write-ram":
			binData = interp.getRAM(dontInterpretSections = readRaw)
		elif action == "write-uil":
			binData = interp.getUIL(dontInterpretSections = readRaw)
		else:
			assert(0)
		return binData
	return handler.toBinary(data)

def main(argv):
	opt_verbose = 1
	opt_forceLevel = 0
	opt_forceBitfileUpload = False
	opt_chipID = None
	opt_chipOptions = []
	opt_device = None
	opt_action = None
	opt_file = None
	opt_noqueue = False
	opt_usebroken = False
	opt_informat = "auto"
	opt_outformat = "bin"

	chips = register_chips()

	try:
		(opts, args) = getopt.getopt(sys.argv[1:],
			"hc:d:V:Qs:xTp:P:e:E:f:F:o:Ul:L:r:R:BtI:O:C:a:A:",
			[ "help", "chip-id=", "device=", "verbose=", "noqueue",
			  "read-sig=", "erase", "test", "read-prog=", "write-prog=",
			  "read-eeprom=", "write-eeprom=", "read-fuse=", "write-fuse=",
			  "read-lock=", "write-lock=", "read-ram=", "write-ram=",
			  "force=", "force-upload", "broken", "list",
			  "in-format=", "out-format=", "chip-opt=",
			  "read-uil=", "write-uil=" ])
		for (o, v) in opts:
			if o in ("-h", "--help"):
				usage()
				return 0

			if o in ("-c", "--chip-id"):
				opt_chipID = v

			if o in ("-C", "--chip-opt"):
				try:
					v = v.split('=')
					name, value = v[0], v[1]
				except (IndexError, ValueError), e:
					print "-C|--chip-opt invalid parameter"
					return 1
				copt = AssignedChipOption(name, value)
				opt_chipOptions.append(copt)

			if o in ("-t", "--list"):
				opt_action = "print-list"

			if o in ("-d", "--device"):
				try:
					v = v.replace('.', ':').split(':')
					opt_device = "%s:%03d:%03d" %\
						(v[0], int(v[1], 10),
						 int(v[2], 10))
				except (IndexError, ValueError), e:
					print("-d|--device invalid DEVID.")
					return 1
			if o in ("-V", "--verbose"):
				opt_verbose = int(v)
			if o in ("-o", "--force"):
				opt_forceLevel = int(v)
			if o in ("-U", "--force-upload"):
				opt_forceBitfileUpload = True
			if o in ("-Q", "--noqueue"):
				opt_noqueue = True
			if o in ("-B", "--broken"):
				opt_usebroken = True
			if o in ("-I", "--in-format"):
				opt_informat = v.lower()
			if o in ("-O", "--out-format"):
				opt_outformat = v.lower()
			if o in ("-s", "--read-sig"):
				opt_action = "read-sig"
				opt_file = v
			if o in ("-x", "--erase"):
				opt_action = "erase"
			if o in ("-T", "--test"):
				opt_action = "test"
			if o in ("-P", "--write-prog"):
				opt_action = "write-prog"
				opt_file = v
			if o in ("-p", "--read-prog"):
				opt_action = "read-prog"
				opt_file = v
			if o in ("-E", "--write-eeprom"):
				opt_action = "write-eeprom"
				opt_file = v
			if o in ("-e", "--read-eeprom"):
				opt_action = "read-eeprom"
				opt_file = v
			if o in ("-F", "--write-fuse"):
				opt_action = "write-fuse"
				opt_file = v
			if o in ("-f", "--read-fuse"):
				opt_action = "read-fuse"
				opt_file = v
			if o in ("-l", "--read-lock"):
				opt_action = "read-lock"
				opt_file = v
			if o in ("-L", "--write-lock"):
				opt_action = "write-lock"
				opt_file = v
			if o in ("-r", "--read-ram"):
				opt_action = "read-ram"
				opt_file = v
			if o in ("-R", "--write-ram"):
				opt_action = "write-ram"
				opt_file = v
			if o in ("-a", "--read-uil"):
				opt_action = "read-uil"
				opt_file = v
			if o in ("-A", "--write-uil"):
				opt_action = "write-uil"
				opt_file = v				
	except (getopt.GetoptError, ValueError), e:
		usage()
		return 1

	if opt_action != "print-list" and not opt_chipID:
		print "-c|--chip-id is mandatory!"
		return 1

	if not opt_informat in ("auto", "bin", "ihex", "ihex-raw", "ahex"):
		print "Invalid -I|--in-format"
		return 1

	if not opt_outformat in ("bin", "ihex", "ihex-raw", "ahex"):
		print "Invalid -O|--out-format"
		return 1

	try:
		if opt_action == "print-list":
			_chips = [] 
			if opt_chipID:
				chip = ChipDescription.findOne(opt_chipID, True)
				_chips.append(chip)

			if not _chips:
				_chips += chips

			# ChipDescription.dumpAll(sys.stdout,
			#    verbose=opt_verbose, showBroken=True)
			# TODO: Remove the filter once all chips have the ChipDescription
			# 		as part of the class
			for chip in filter(lambda c: hasattr(c, 'description'), _chips):
				chip.description.detail_level = opt_verbose
				print(str(chip.description))
					
			return 0

		top = TOP(
			  devIdentifier = opt_device,
			  verbose = opt_verbose, forceLevel = opt_forceLevel,
			  noqueue = opt_noqueue, usebroken = opt_usebroken,
			  forceBitfileUpload = opt_forceBitfileUpload)

		top.initializeChip(chipID = opt_chipID,
				   assignedChipOptions = opt_chipOptions)

		if opt_action == "read-sig":
			fileOut(opt_file, opt_outformat, top.readSignature())
		elif opt_action == "erase":
			top.eraseChip()
		elif opt_action == "test":
			top.testChip()
		elif opt_action == "read-prog":
			fileOut(opt_file, opt_outformat, top.readProgmem())
		elif opt_action == "write-prog":
			image = fileIn(top, opt_action, opt_file, opt_informat)
			top.writeProgmem(image)
		elif opt_action == "read-eeprom":
			fileOut(opt_file, opt_outformat, top.readEEPROM())
		elif opt_action == "write-eeprom":
			top.writeEEPROM(fileIn(top, opt_action, opt_file, opt_informat))
		elif opt_action == "read-fuse":
			fileOut(opt_file, opt_outformat, top.readFuse())
		elif opt_action == "write-fuse":
			image = fileIn(top, opt_action, opt_file, opt_informat)
			top.writeFuse(image)
		elif opt_action == "read-lock":
			fileOut(opt_file, opt_outformat, top.readLockbits())
		elif opt_action == "write-lock":
			top.writeLockbits(fileIn(top, opt_action, opt_file, opt_informat))
		elif opt_action == "read-ram":
			fileOut(opt_file, opt_outformat, top.readRAM())
		elif opt_action == "write-ram":
			top.writeRAM(fileIn(top, opt_action, opt_file, opt_informat))
		elif opt_action == "read-uil":
			fileOut(opt_file, opt_outformat, top.readUserIdLocation())
		elif opt_action == "write-uil":
			top.writeUserIdLocation(fileIn(top, opt_action, opt_file, opt_informat))
		else:
			if opt_verbose >= 1:
				print "No action specified"
		top.shutdownChip()
	except (TOPException, BitfileException, IOError), e:
		print e
		return 1
	return 0

if __name__ == "__main__":
	sys.exit(main(sys.argv))
