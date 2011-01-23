"""
#    TOP2049 Open Source programming suite
#
#    Cypress M8C In System Serial Programmer
#
#    Copyright (c) 2010-2011 Michael Buesch <mb@bu3sch.de>
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

from chip import *
import time


class Chip_M8C_ISSP(Chip):
	ISSPCMD_POR	= 1 # Perform a power-on-reset
	ISSPCMD_PWROFF	= 2 # Turn power off
	ISSPCMD_SENDVEC	= 3 # Send a vector
	ISSPCMD_EXEC	= 4 # Do an "execute" transfer

	STAT_BUSY0		= 0x01
	STAT_BUSY1		= 0x02
	STAT_ISSPSTATE		= 0x1C
	STAT_ISSPSTATE_SHIFT	= 2
	STAT_SDATA		= 0x20

	STRVEC_SETFREQ = {
		2	: "1001111110000000101000",
		3	: "1001111110000001001000",
		3.578	: "1001111110000001011000",
		4	: "1001111110000001101000",
		5	: "1001111110000010001000",
		6	: "1001111110000010101000",
		6.66666	: "1001111110000010111000",
		7	: "1001111110000011001000",
		8	: "1001111110000011100000",
		9	: "1001111110000100000000",
		10	: "1001111110000100100000",
		11	: "1001111110000101000000",
		12	: "1001111110000101100000",
	}
	STRVEC_INIT1 = (
		"1100101000000000000000",
		"0000000000000000000000",
		"0000000000000000000000",
		"1000111101100100000000",
		"1101111011100000000000",
		"1101111011000001000000",
		"1001111100000111010000",
		"1001111100100001011000",
		"1101111010100000000000",
		"1101111010000000011000",
		"1001111101100100000000",
		"1101111100100110000000",
		"1101111101001000000000",
		"1101111000000001000000",
		"1101111100000000000000",
		"1101111111100010010000",
	)
	STRVEC_INIT2 = (
		"1101111011100000000000",
		"1101111011000001000000",
		"1001111100000111010000",
		"1001111100100001011000",
		"1101111010100000000000",
		"1101111010000000011000",
		"1001111101100100000000",
		"1101111100100110000000",
		"1101111101001000000000",
		"1001111101000000001000",
		"1101111000000000110000",
		"1101111100000000000000",
		"1101111111100010010000",
	)
	STRVEC_INIT3_HIVDD = (
		"1101111011100000000000",
		"1101111010000000011000",
		"1101111010100000000000",
		"1101111011000001000000",
		"1101111100001010001000",
		"1101111100111111100000",
		"1101111101000110000000",
		"1101111111100010010000",
		"0000000000000000000000",
		"1101111011100000000000",
		"1101111010000000011000",
		"1101111010100000000000",
		"1101111011000001000000",
		"1101111100001100000000",
		"1101111100111101010000",
		"1101111101000110000000",
		"1101111011100010000000",
		"1101111111100010010000",
		"0000000000000000000000",
	)
	STRVEC_INIT3_LOVDD = (
		"1101111011100000000000",
		"1101111010000000011000",
		"1101111010100000000000",
		"1101111011000001000000",
		"1101111100001010001000",
		"1101111100111111000000",
		"1101111101000110000000",
		"1101111111100010010000",
		"0000000000000000000000",
		"1101111011100000000000",
		"1101111010000000011000",
		"1101111010100000000000",
		"1101111011000001000000",
		"1101111100001100000000",
		"1101111100111101010000",
		"1101111101000110000000",
		"1101111011100010000000",
		"1101111111100010010000",
		"0000000000000000000000",
	)
	STRVEC_IDSETUP = (
		"1101111011100000000000",
		"1101111011000001000000",
		"1001111100000111010000",
		"1001111100100001011000",
		"1101111010100000000000",
		"1101111010000000011000",
		"1001111101100100000000",
		"1101111100100110000000",
		"1101111101001000000000",
		"1001111101000000000000",
		"1101111000000000110000",
		"1101111100000000000000",
		"1101111111100010010000",
	)
	STRVEC_READBYTE = "101aaaaaaaaZDDDDDDDDZ0"
	STRVEC_WRITEBYTE = "100aaaaaaaadddddddd000"
	STRVEC_ERASEALL = (
		"1101111011100000000000",
		"1101111011001000000000",
		"1001111100000111010000",
		"1001111100101000011000",
		"1101111010100000000000",
		"1101111010000000011000",
		"1001111101110000000000",
		"1101111100100110000000",
		"1101111101001000000000",
		"1101111000000000101000",
		"1101111100000000000000",
		"1101111111100010010000",
	)
	STRVEC_SECURE = (
		"1101111011100000000000",
		"1101111011001000000000",
		"1001111100000111010000",
		"1001111100101000011000",
		"1101111010100000000000",
		"1101111010000000011000",
		"1001111101110000000000",
		"1101111100100110000000",
		"1101111101001000000000",
		"1101111000000000100000",
		"1101111100000000000000",
		"1101111111100010010000",
	)
	STRVEC_WRITESECBYTE = "10010aaaaaadddddddd000"
	STRVEC_SETBLKNUM = "10011111010dddddddd000"
	STRVEC_READBLK = (
		"1101111011100000000000",
		"1101111011000001000000",
		"1001111100000111010000",
		"1001111100100001011000",
		"1101111010100000000000",
		"1101111010000000011000",
		"1001111101100100000000",
		"1101111100100110000000",
		"1101111101001000000000",
		"1101111000000000001000",
		"1101111100000000000000",
		"1101111111100010010000",
	)
	STRVEC_WRITEBLK = (
		"1101111011100000000000",
		"1101111011000001000000",
		"1001111100000111010000",
		"1001111100100001011000",
		"1101111010100000000000",
		"1101111010000000011000",
		"1001111101100100000000",
		"1101111100100110000000",
		"1101111101001000000000",
		"1101111000000000010000",
		"1101111100000000000000",
		"1101111111100010010000",
	)
	STRVEC_READCHKSUM = "10111111001ZDDDDDDDDZ010111111000ZDDDDDDDDZ0"

	def __init__(self):
		Chip.__init__(self)
#		self.progmemSize = 1024 * 16
		self.progmemSize = 128#FIXME

	def readSignature(self):
		self.progressMeterInit("Reading chip ID", 0)
		self.__powerOnReset()
		gotID = self.__readID()
		self.progressMeterFinish()

		return int2byte(gotID & 0xFF) + int2byte((gotID >> 8) & 0xFF)

	def erase(self):
		self.progressMeterInit("Erasing chip", 0)
		self.__powerOnReset()
		self.__sendSetFreqVector()
		for vec in self.STRVEC_ERASEALL:
			self.__loadStringVector(vec)
			self.__runCommandSync(self.ISSPCMD_SENDVEC)
		self.__runCommandSync(self.ISSPCMD_EXEC)
		self.progressMeterFinish()

	def writeProgmem(self, image):
		if len(image) > self.progmemSize or len(image) % 64 != 0:
			self.throwError("Invalid program memory image size %d "
					"(expected <=%d and multiple of 64)" %\
				(len(image), self.progmemSize))

		self.progressMeterInit("Writing program memory", len(image))
		self.__powerOnReset()
		for blknum in range(0, len(image) // 64):
			for i in range(0, 64):
				self.progressMeter(blknum * 64 + i)
				self.__writeByte(i, byte2int(image[blknum * 64 + i]))
			self.__sendSetFreqVector()
			vec = self.__stringVectorReplace(self.STRVEC_SETBLKNUM, "d", blknum)
			self.__loadStringVector(vec)
			self.__runCommandSync(self.ISSPCMD_SENDVEC)
			for vec in self.STRVEC_WRITEBLK:
				self.__loadStringVector(vec)
				self.__runCommandSync(self.ISSPCMD_SENDVEC)
			self.__runCommandSync(self.ISSPCMD_EXEC)
		self.progressMeterFinish()

	def readProgmem(self):
		self.progressMeterInit("Reading program memory", self.progmemSize)
		self.__powerOnReset()
		assert(self.progmemSize % 64 == 0)
		image = []
		for blknum in range(0, self.progmemSize // 64):
			vec = self.__stringVectorReplace(self.STRVEC_SETBLKNUM, "d", blknum)
			self.__loadStringVector(vec)
			self.__runCommandSync(self.ISSPCMD_SENDVEC)
			for vec in self.STRVEC_READBLK:
				self.__loadStringVector(vec)
				self.__runCommandSync(self.ISSPCMD_SENDVEC)
			self.__runCommandSync(self.ISSPCMD_EXEC)
			for i in range(0, 64):
				self.progressMeter(blknum * 64 + i)
				image.append(int2byte(self.__readByte(i)))
		self.progressMeterFinish()
		return b"".join(image)

	def __powerDown(self):
		"Turn the power to the device off"
		self.printDebug("Powering device down...")
		self.__runCommandSync(self.ISSPCMD_PWROFF)
		self.top.hostDelay(5)

	def __powerOnReset(self):
		"Perform a complete power-on-reset and initialization"
		self.top.vccx.setLayoutMask(0)
		self.top.vpp.setLayoutMask(0)
		self.top.gnd.setLayoutMask(0)
		self.top.cmdSetVCCXVoltage(5)
		self.top.cmdSetVPPVoltage(5)

		self.printDebug("Initializing supply power...")
		self.top.gnd.setLayoutPins( (20,) )
		self.top.vccx.setLayoutPins( (21,) )

		self.__powerDown()
		self.printDebug("Performing a power-on-reset...")
		self.__loadStringVector(self.STRVEC_INIT1[0])
		self.__runCommandSync(self.ISSPCMD_POR)
		self.printDebug("Sending vector 1...")
		for vec in self.STRVEC_INIT1[1:]:
			self.__loadStringVector(vec)
			self.__runCommandSync(self.ISSPCMD_SENDVEC)
		self.__runCommandSync(self.ISSPCMD_EXEC)
		self.printDebug("Sending vector 2...")
		for vec in self.STRVEC_INIT2:
			self.__loadStringVector(vec)
			self.__runCommandSync(self.ISSPCMD_SENDVEC)
		self.__runCommandSync(self.ISSPCMD_EXEC)
		self.printDebug("Sending vector 3...")
		for vec in self.STRVEC_INIT3_HIVDD:
			self.__loadStringVector(vec)
			self.__runCommandSync(self.ISSPCMD_SENDVEC)
#		self.__runCommandSync(self.ISSPCMD_EXEC)

	def __readID(self):
		"Read the silicon ID"
		for vec in self.STRVEC_IDSETUP:
			self.__loadStringVector(vec)
			self.__runCommandSync(self.ISSPCMD_SENDVEC)
		self.__runCommandSync(self.ISSPCMD_EXEC)

		low = self.__readByte(0xF8)
		high = self.__readByte(0xF9)

		return low | (high << 8)

	def __readByte(self, address):
		strVec = self.__stringVectorReplace(self.STRVEC_READBYTE, "a", address)
		self.__loadStringVector(strVec)
		self.__runCommandSync(self.ISSPCMD_SENDVEC)
		input = self.__getInputVector()
		return (input >> 2) & 0xFF

	def __writeByte(self, address, byte):
		vec = self.__stringVectorReplace(self.STRVEC_WRITEBYTE, "a", address)
		vec = self.__stringVectorReplace(vec, "d", byte)
		self.__loadStringVector(vec)
		self.__runCommandSync(self.ISSPCMD_SENDVEC)

	def __sendSetFreqVector(self):
		sclkFreq = 2	# 2 Mhz. Hardcoded in FPGA.
		strVec = self.STRVEC_SETFREQ[sclkFreq]
		self.__loadStringVector(strVec)
		self.__runCommandSync(self.ISSPCMD_SENDVEC)

	def __loadCommand(self, command):
		self.top.cmdFPGAWrite(0x12, command & 0xFF)

	def __runCommandSync(self, command):
		self.printDebug("Running synchronous command %d" % command)
		self.__loadCommand(command)
		self.__busyWait()

	def __loadVectorLow(self, vecLow):
		self.top.cmdFPGAWrite(0x13, vecLow & 0xFF)

	def __loadVectorMed(self, vecMed):
		self.top.cmdFPGAWrite(0x14, vecMed & 0xFF)

	def __loadVectorHigh(self, vecHigh):
		self.top.cmdFPGAWrite(0x15, vecHigh & 0xFF)

	def __loadVector(self, vec):
		self.__loadVectorLow(vec)
		self.__loadVectorMed(vec >> 8)
		self.__loadVectorHigh(vec >> 16)

	def __loadVectorInputMaskLow(self, maskLow):
		self.top.cmdFPGAWrite(0x16, maskLow & 0xFF)

	def __loadVectorInputMaskMed(self, maskMed):
		self.top.cmdFPGAWrite(0x17, maskMed & 0xFF)

	def __loadVectorInputMaskHigh(self, maskHigh):
		self.top.cmdFPGAWrite(0x18, maskHigh & 0xFF)

	def __loadVectorInputMask(self, mask):
		self.__loadVectorInputMaskLow(mask)
		self.__loadVectorInputMaskMed(mask >> 8)
		self.__loadVectorInputMaskHigh(mask >> 16)

	def __getStatusFlags(self):
		self.top.cmdFPGARead(0x12)
		stat = self.top.cmdReadBufferReg8()
		isspState = (stat & self.STAT_ISSPSTATE) >> self.STAT_ISSPSTATE_SHIFT
		sdata = bool(stat & self.STAT_SDATA)
		isBusy = bool(stat & self.STAT_BUSY0) != bool(stat & self.STAT_BUSY1)
		self.printDebug("isspState = 0x%02X, isBusy = %d, busyFlags = 0x%01X, sdata = %d" %\
			(isspState, isBusy, (stat & (self.STAT_BUSY0 | self.STAT_BUSY1)), sdata))
		return (isBusy, sdata, isspState)

	def __busy(self):
		(isBusy, sdata, isspState) = self.__getStatusFlags()
		return isBusy

	def __busyWait(self):
		for i in range(0, 200):
			if not self.__busy():
				return
			self.top.hostDelay(0.01)
		self.throwError("Timeout in busywait. Chip not responding?")

	def __getInputVector(self):
		self.top.cmdFPGARead(0x13)
		self.top.cmdFPGARead(0x14)
		self.top.cmdFPGARead(0x15)
		return self.top.cmdReadBufferReg24()

	def __stringVectorToBinary(self, vector):
		binary = 0
		inputMask = 0
		assert(len(vector) == 22)
		bit = len(vector) - 1
		for b in vector:
			if b == "1":
				binary |= (1 << bit)
			if b == "H" or b == "L" or b == "Z" or b == "D":
				inputMask |= (1 << bit)
			bit -= 1
		return (binary, inputMask)

	def __stringVectorReplace(self, strVec, replace, data):
		ret = ""
		for i in range(len(strVec) - 1, -1, -1):
			b = strVec[i]
			if b == replace:
				if (data & 1):
					ret = "1" + ret
				else:
					ret = "0" + ret
				data >>= 1
			else:
				ret = b + ret
		return ret

	def __loadStringVector(self, strVec):
		(vector, inputMask) = self.__stringVectorToBinary(strVec)
#		print "Loading vector 0x%06X, 0x%06X" % (vector, inputMask)
		self.__loadVectorInputMask(inputMask)
		self.__loadVector(vector)

ChipDescription(
	Chip_M8C_ISSP,
	bitfile = "m8c-issp",
	runtimeID = (0x0007, 0x01),
	chipVendors = "Cypress",
	description = "M8C In System Serial Programmer",
	packages = ( ("M8C ISSP header", "Special adapter"), ),
	comment = "Special adapter required",
	broken = True
)
