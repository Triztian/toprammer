#!/usr/bin/env python
"""
#    TOP2049 Open Source programming suite
#
#    Qt-based graphical user interface
#
#    Copyright (c) 2010-2012 Michael Buesch <m@bues.ch>
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
import sys
import time
import cgi
import ConfigParser

try:
	from PySide.QtCore import *
	from PySide.QtGui import *
except (ImportError), e:
	print "Failed to import PySide modules: %s" % str(e)
	print "Please install PySide. On Debian Linux run: aptitude install python-pyside"
	sys.exit(1)


EVENT_HWTHREAD		= QEvent.Type(QEvent.User + 0)


def stringRemoveChars(string, chars):
	ret = []
	for c in string:
		if c not in chars:
			ret.append(c)
	return "".join(ret)

def htmlEscape(plaintext):
	return cgi.escape(plaintext)

def getIconPath(name):
	return pkg_resources.resource_filename("libtoprammer",
					       "icons/" + name + ".png")

def getIcon(name):
	return QIcon(getIconPath(name))

class Wrapper(object):
	def __init__(self, obj):
		self.obj = obj

	def __eq__(self, other):
		return self.obj == other.obj

	def __ne__(self, other):
		return self.obj != other.obj

class ZifPinButton(QWidget):
	TEXT_RIGHT	= 0
	TEXT_LEFT	= 1

	stateChanged = Signal(bool)

	class Label(QLabel):
		clicked = Signal()

		def __init__(self, text, parent=None):
			QLabel.__init__(self, text, parent)

		def mousePressEvent(self, event):
			self.clicked.emit()

	def __init__(self, text, textPos=TEXT_RIGHT, parent=None):
		QWidget.__init__(self, parent)
		self.setLayout(QHBoxLayout(self))
		self.layout().setContentsMargins(QMargins())

		self.checkbox = QCheckBox(self)
		self.checkbox.stateChanged.connect(self.__cbStateChanged)

		self.label = self.Label(text, self)
		self.label.clicked.connect(self.toggle)

		if textPos == self.TEXT_RIGHT:
			self.label.setAlignment(Qt.AlignLeft)
			self.layout().addWidget(self.checkbox)
			self.layout().addWidget(self.label)
		else:
			self.label.setAlignment(Qt.AlignRight)
			self.layout().addWidget(self.label)
			self.layout().addWidget(self.checkbox)

	def __cbStateChanged(self, newState):
		self.stateChanged.emit(newState == Qt.Checked)

	def state(self):
		return self.checkbox.checkState() == Qt.Checked

	def setState(self, en):
		self.checkbox.setCheckState(Qt.Checked if en else Qt.Unchecked)

	def toggle(self):
		self.setState(not self.state())

class ZifWidget(QGroupBox):
	def __init__(self, unitest, nrZifPins):
		QGroupBox.__init__(self, "ZIF socket", unitest)
		self.unitest = unitest
		self.setLayout(QGridLayout())

		self.nrPins = nrZifPins
		assert(self.nrPins % 2 == 0)

		self.blockedPins = []
		self.ignoreOutChange = False

		label = QLabel("ZIF\nsocket", self)
		label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
		label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
		label.setMinimumWidth(80)
		self.layout().addWidget(label, 0, 2, self.nrPins // 2, 1)

		self.pins = [ None ] * self.nrPins
		self.pinOuten = [ None ] * self.nrPins
		for i in range(0, self.nrPins // 2):
			left = i + 1
			right = self.nrPins - i
			self.pins[left - 1] = ZifPinButton(str(left),
						ZifPinButton.TEXT_LEFT, self)
			self.pins[left - 1].stateChanged.connect(self.__outChanged)
			self.pinOuten[left - 1] = ZifPinButton("out",
						ZifPinButton.TEXT_LEFT, self)
			self.pinOuten[left - 1].stateChanged.connect(self.__outEnChanged)
			self.layout().addWidget(self.pinOuten[left - 1], left - 1, 0)
			self.layout().addWidget(self.pins[left - 1], left - 1, 1)
			self.pins[right - 1] = ZifPinButton(str(right),
						ZifPinButton.TEXT_RIGHT, self)
			self.pins[right - 1].stateChanged.connect(self.__outChanged)
			self.pinOuten[right - 1] = ZifPinButton("out",
						ZifPinButton.TEXT_RIGHT, self)
			self.pinOuten[right - 1].stateChanged.connect(self.__outEnChanged)
			self.layout().addWidget(self.pins[right - 1], self.nrPins - right, 3)
			self.layout().addWidget(self.pinOuten[right - 1], self.nrPins - right, 4)
		self.__outEnChanged()
		self.__outChanged()

	def readInputs(self):
		try:
			inputMask = self.unitest.queryTop("top.getChip().getInputs()")
		except (TOPException), e:
			QMessageBox.critical(self, "TOP communication failed",
				"Failed to fetch input states:\n" +\
				str(e))
			return False
		for i in range(0, self.nrPins):
			if not self.pinOuten[i].state() and\
			   i + 1 not in self.blockedPins:
				state = False
				if inputMask & bit(i):
					state = True
				self.ignoreOutChange = True
				self.pins[i].setState(state)
				self.ignoreOutChange = False
		return True

	def __updateInOutStates(self):
		for i in range(0, self.nrPins):
			if i + 1 in self.blockedPins:
				self.pins[i].setEnabled(False)
				self.pins[i].setState(False)
				self.pinOuten[i].setEnabled(False)
				self.pinOuten[i].setState(False)
			else:
				self.pinOuten[i].setEnabled(True)
				if self.pinOuten[i].state():
					self.pins[i].setEnabled(True)
				else:
					self.pins[i].setEnabled(False)

	def __outEnChanged(self, unused=False):
		self.__updateInOutStates()
		outEnMask = self.getOutEnMask()
		try:
			self.unitest.queryTop("top.getChip().setOutputEnableMask(...)",
					      outEnMask)
		except (TOPException), e:
			QMessageBox.critical(self, "TOP communication failed",
				"Failed to set output-enable states:\n" +\
				str(e))
			return
		self.readInputs()

	def __outChanged(self, unused=False):
		if self.ignoreOutChange:
			return
		outMask = self.getOutMask()
		try:
			self.unitest.queryTop("top.getChip().setOutputs(...)",
					      outMask)
		except (TOPException), e:
			QMessageBox.critical(self, "TOP communication failed",
				"Failed to set output states:\n" +\
				str(e))
			return
		self.readInputs()

	def setBlockedPins(self, blockedPins):
		self.blockedPins = blockedPins
		self.__updateInOutStates()
		self.readInputs()

	def getOutEnMask(self):
		outEnMask = 0
		for i in range(0, self.nrPins):
			if self.pinOuten[i].state():
				outEnMask |= bit(i)
		return outEnMask

	def setOutEnMask(self, mask):
		for i in range(0, self.nrPins):
			if mask & bit(i):
				self.pinOuten[i].setState(True)
			else:
				self.pinOuten[i].setState(False)
			mask &= ~bit(i)
		if mask:
			raise TOPException("ZIF out-en mask has too many bits set")

	def getOutMask(self):
		outMask = 0
		for i in range(0, self.nrPins):
			if self.pins[i].state():
				outMask |= bit(i)
		return outMask

	def setOutMask(self, mask):
		for i in range(0, self.nrPins):
			if mask & bit(i):
				self.pins[i].setState(True)
			else:
				self.pins[i].setState(False)
			mask &= ~bit(i)
		if mask:
			raise TOPException("ZIF out mask has too many bits set")

class UnitestDialog(QDialog):
	def __init__(self, mainWindow):
		QDialog.__init__(self, mainWindow)
		self.setWindowTitle("Universal logic tester")
		self.mainWindow = mainWindow
		self.setLayout(QGridLayout())

		self.inputPollBlocked = 0
		self.uiChangeBlocked = 0

		# Initialize the unitest chip
		(failed, returnValue) = self.mainWindow.runOperationSync(
					HwThread.TASK_INITCHIP,
					"unitest")
		if failed:
			raise TOPException("Failed to load 'unitest' chip: %s" % str(returnValue))
		self.queryTop("top.getChip().reset()")

		# Query the hardware layer for common parameters
		self.param_topType = self.queryTop("top.getProgrammerType()")
		self.param_gndLayouts = self.queryTop("top.gnd.supportedLayouts()")
		self.param_nrZifPins = self.queryTop("top.gnd.getNrOfPins()")
		self.param_vccLayouts = self.queryTop("top.vcc.supportedLayouts()")
		self.param_minVccVolt = self.queryTop("top.vcc.minVoltage()")
		self.param_maxVccVolt = self.queryTop("top.vcc.maxVoltage()")
		self.param_vppLayouts = self.queryTop("top.vpp.supportedLayouts()")
		self.param_minVppVolt = self.queryTop("top.vpp.minVoltage()")
		self.param_maxVppVolt = self.queryTop("top.vpp.maxVoltage()")
		self.param_oscFreq = self.queryTop("top.getOscillatorHz()")

		assert(self.param_nrZifPins % 2 == 0)
		self.param_vppLayouts.sort(key=lambda (layId, layMask): layMask)

		self.menuBar = QMenuBar(self)
		self.menuBar.addAction("&Load settings...", self.loadSettings)
		self.menuBar.addAction("&Save settings...", self.saveSettings)
		self.menuBar.addAction("&Raw command...", self.mainWindow.sendRawCommand)
		self.layout().addWidget(self.menuBar, 0, 0, 1, 3)

		self.zifWidget = ZifWidget(self, self.param_nrZifPins)
		self.layout().addWidget(self.zifWidget, 1, 0, 10, 1)

		group = QGroupBox("GND layout", self)
		group.setLayout(QGridLayout())
		self.gndLayout = QComboBox(self)
		self.gndLayout.addItem("Not connected", 0)
		for (layId, layMask) in self.param_gndLayouts:
			if not layMask:
				continue
			descr = "GND on pin "
			for i in range(0, self.param_nrZifPins):
				if layMask & bit(i):
					descr += str(i + 1) + " "
			self.gndLayout.addItem(descr, layId)
		group.layout().addWidget(self.gndLayout, 0, 0)
		self.layout().addWidget(group, 1, 1)

		group = QGroupBox("VCC layout", self)
		group.setLayout(QGridLayout())
		self.vccVoltage = QDoubleSpinBox(self)
		self.vccVoltage.setSuffix(" V")
		self.vccVoltage.setMinimum(self.param_minVccVolt)
		self.vccVoltage.setMaximum(self.param_maxVccVolt)
		self.vccVoltage.setSingleStep(0.1)
		group.layout().addWidget(self.vccVoltage, 0, 0)
		self.vccLayout = QComboBox(self)
		self.vccLayout.addItem("Not connected", 0)
		for (layId, layMask) in self.param_vccLayouts:
			if not layMask:
				continue
			descr = "VCC on pin "
			for i in range(0, self.param_nrZifPins):
				if layMask & bit(i):
					descr += str(i + 1) + " "
			self.vccLayout.addItem(descr, layId)
		group.layout().addWidget(self.vccLayout, 1, 0)
		self.layout().addWidget(group, 2, 1)

		group = QGroupBox("Input polling", self)
		group.setLayout(QGridLayout())
		self.inputPollEn = QCheckBox("Enabled", self)
		self.inputPollEn.setCheckState(Qt.Checked)
		group.layout().addWidget(self.inputPollEn, 0, 0)
		self.inputPollInterval = QDoubleSpinBox(self)
		self.inputPollInterval.setPrefix("Interval ")
		self.inputPollInterval.setSuffix(" seconds")
		self.inputPollInterval.setMinimum(0.25)
		self.inputPollInterval.setSingleStep(0.25)
		self.inputPollInterval.setValue(1.0)
		group.layout().addWidget(self.inputPollInterval, 1, 0)
		self.layout().addWidget(group, 3, 1)

		group = QGroupBox("Frequency counter", self)
		group.setLayout(QGridLayout())
		self.fcntEn = QCheckBox("Enabled", self)
		self.fcntEn.setCheckState(Qt.Unchecked)
		group.layout().addWidget(self.fcntEn, 0, 0)
		self.fcntPosEdge = QCheckBox("Positive edge", self)
		self.fcntPosEdge.setCheckState(Qt.Checked)
		group.layout().addWidget(self.fcntPosEdge, 1, 0)
		self.fcntPin = QComboBox(self)
		group.layout().addWidget(self.fcntPin, 2, 0)
		self.fcntValueLabel = QLabel(self)
		group.layout().addWidget(self.fcntValueLabel, 3, 0)
		self.fcntValue = 0
		self.layout().addWidget(group, 4, 1)

		group = QGroupBox("Oscillator", self)
		group.setLayout(QGridLayout())
		self.oscPin = QComboBox(self)
		self.oscPin.addItem("Disabled", Wrapper(0))
		for i in range(0, self.param_nrZifPins):
			self.oscPin.addItem("On pin %d" % (i + 1),
					    Wrapper(bit(i)))
		group.layout().addWidget(self.oscPin, 0, 0)
		self.oscDiv = QSpinBox(self)
		self.oscDiv.setPrefix("Divider ")
		self.oscDiv.setSingleStep(1)
		self.oscDiv.setMinimum(1)
		self.oscDiv.setMaximum(self.param_oscFreq)
		self.oscDiv.setValue(self.param_oscFreq // 1000)
		group.layout().addWidget(self.oscDiv, 1, 0)
		self.oscFreq = QLabel(self)
		group.layout().addWidget(self.oscFreq, 2, 0)
		self.layout().addWidget(group, 5, 1)

		group = QGroupBox("VPP layout", self)
		group.setLayout(QGridLayout())
		self.vppVoltage = QDoubleSpinBox(self)
		self.vppVoltage.setSuffix(" V")
		self.vppVoltage.setMinimum(self.param_minVppVolt)
		self.vppVoltage.setMaximum(self.param_maxVppVolt)
		self.vppVoltage.setSingleStep(0.1)
		group.layout().addWidget(self.vppVoltage, 0, 0, 1, 2)
		self.vppLayouts = {}
		xOffset = 0
		yOffset = 0
		for (layId, layMask) in self.param_vppLayouts:
			if not layMask:
				continue
			for i in range(0, self.param_nrZifPins):
				if layMask & bit(i):
					descr = str(i + 1) + " "
			self.vppLayouts[layId] = QCheckBox(descr, self)
			self.vppLayouts[layId].stateChanged.connect(
				     self.vppLayoutChanged)
			group.layout().addWidget(self.vppLayouts[layId],
					yOffset + 1, xOffset)
			yOffset += 1
			if yOffset == len(self.param_vppLayouts) // 2:
				yOffset = 0
				xOffset += 1
		self.layout().addWidget(group, 1, 2, 8, 1)

		self.inputPollTimer = QTimer()
		self.inputPollTimer.setSingleShot(True)
		self.inputPollTimer.timeout.connect(self.doInputPollTimer)

		self.inputPollEn.stateChanged.connect(self.inputPollChanged)
		self.inputPollInterval.valueChanged.connect(self.inputPollChanged)
		self.gndLayout.currentIndexChanged.connect(self.gndLayoutChanged)
		self.vccVoltage.valueChanged.connect(self.vccLayoutChanged)
		self.vccLayout.currentIndexChanged.connect(self.vccLayoutChanged)
		self.vppVoltage.valueChanged.connect(self.vppLayoutChanged)
		self.fcntEn.stateChanged.connect(self.fcntChanged)
		self.fcntPosEdge.stateChanged.connect(self.fcntChanged)
		self.fcntPin.currentIndexChanged.connect(self.fcntChanged)
		self.oscPin.currentIndexChanged.connect(self.oscChanged)
		self.oscDiv.valueChanged.connect(self.oscChanged)

		self.__modeChanged()
		self.gndLayoutChanged()
		self.vccLayoutChanged()
		self.inputPollChanged()
		self.oscChanged()

	def __readFcntValue(self):
		try:
			self.fcntValue = self.queryTop("top.getChip().getFreqCount()")
		except (TOPException), e:
			QMessageBox.critical(self, "TOP communication failed",
				"Failed to read frequency counter value:\n" +\
				str(e))
			return False
		return True

	def __updateFcntValueLabel(self):
		if self.getMode() != Chip_Unitest.MODE_FCNT:
			self.fcntValueLabel.clear()
			return
		if self.fcntValue:
			hz = "%.3f" % (float(self.param_oscFreq) / self.fcntValue)
		else:
			hz = "~~~"
		self.fcntValueLabel.setText("Measured: %s Hz" % hz)

	def __modeChanged(self):
		mode = self.getMode()
		activePinMask = self.queryTop("top.getChip().getActivePinMask()")

		self.uiChangeBlocked += 1

		# Update freq count UI
		self.fcntValue = 0
		self.fcntPin.clear()
		self.fcntPin.setEnabled(False)
		self.fcntPosEdge.setEnabled(False)
		if mode == Chip_Unitest.MODE_FCNT:
			for i in range(0, self.param_nrZifPins):
				if bit(i) & activePinMask == 0:
					continue
				self.fcntPin.addItem("On pin %d" % (i + 1), i)
			self.fcntPin.setEnabled(True)
			self.fcntPosEdge.setEnabled(True)
		self.__updateFcntValueLabel()

		# Update the ZIF widget
		self.updateZifCheckboxes()

		self.uiChangeBlocked -= 1

	def switchMode(self, mode):
		if self.getMode() == mode:
			return
		self.queryTop("top.getChip().setMode(...)", mode)
		self.__modeChanged()

	def __loadFile(self, filename):
		try:
			p = ConfigParser.SafeConfigParser()
			p.read((filename,))

			sect = "TOPRAMMER-UNITEST-SETTINGS"
			if not p.has_section(sect):
				raise TOPException("Invalid file format")
			ver = p.getint(sect, "fileVersion")
			verExpected = 1
			if ver != verExpected:
				raise TOPException("Unsupported file version (got %d, expected %d)" %\
						   (ver, verExpected))
			pType = p.get(sect, "programmerType")
			if pType.upper() != self.param_topType.upper():
				raise TOPException("Programmer type mismatch (file = %s, connected = %s)" %\
						   (pType, self.param_topType))

			layout = p.getint(sect, "gndLayout")
			idx = self.gndLayout.findData(layout)
			if idx < 0:
				raise TOPException("Invalid GND layout")
			self.gndLayout.setCurrentIndex(idx)

			layout = p.getint(sect, "vccLayout")
			idx = self.vccLayout.findData(layout)
			if idx < 0:
				raise TOPException("Invalid VCC layout")
			self.vccLayout.setCurrentIndex(idx)

			voltage = p.getfloat(sect, "vccVoltage")
			self.vccVoltage.setValue(voltage)

			layouts = p.get(sect, "vppLayout").split(",")
			for layId in self.vppLayouts.keys():
				if layId in layouts:
					self.vppLayouts[layId].setCheckState(Qt.Checked)
				else:
					self.vppLayouts[layId].setCheckState(Qt.Unchecked)

			voltage = p.getfloat(sect, "vppVoltage")
			self.vppVoltage.setValue(voltage)

			interval = p.getfloat(sect, "inputPollInterval")
			self.inputPollInterval.setValue(interval)

			enabled = p.getboolean(sect, "inputPollEnabled")
			if enabled:
				self.inputPollEn.setCheckState(Qt.Checked)
			else:
				self.inputPollEn.setCheckState(Qt.Unchecked)

			div = p.getint(sect, "oscillatorDiv")
			self.oscDiv.setValue(div)

			mask = int(p.get(sect, "oscillatorMask"), 16)
			for i in range(0, self.oscPin.count()):
				if self.oscPin.itemData(i).obj == mask:
					break
			else:
				raise TOPException("Invalid oscillator mask")
			self.oscPin.setCurrentIndex(i)

			mask = int(p.get(sect, "zifOutEnMask"), 16)
			self.zifWidget.setOutEnMask(mask)

			mask = int(p.get(sect, "zifOutMask"), 16)
			self.zifWidget.setOutMask(mask)

			enabled = p.getboolean(sect, "fcntEnabled")
			if enabled:
				self.fcntEn.setCheckState(Qt.Checked)
			else:
				self.fcntEn.setCheckState(Qt.Unchecked)
			pos = p.getboolean(sect, "fcntPosEdge")
			if pos:
				self.fcntPosEdge.setCheckState(Qt.Checked)
			else:
				self.fcntPosEdge.setCheckState(Qt.Unchecked)
			pin = p.getint(sect, "fcntPin")
			if pin >= 0:
				idx = self.fcntPin.findData(pin)
				if idx < 0:
					raise TOPException("Invalid fcntPin")
				self.fcntPin.setCurrentIndex(idx)

		except (ConfigParser.Error, TOPException, ValueError), e:
			QMessageBox.critical(self, "Failed to load settings",
					     "Failed to load settings: %s" % str(e))

	def loadSettings(self):
		(fn, selFltr) = QFileDialog.getOpenFileName(
			self, "Load settings", "",
			"Toprammer-unitest settings (*.tus);;"
			"All files (*)")
		if not fn:
			return
		self.__loadFile(fn)

	def __saveFile(self, filename):
		try:
			fd = open(filename, "w+b")

			fd.write("[TOPRAMMER-UNITEST-SETTINGS]\r\n")
			fd.write("fileVersion=%d\r\n" % 1)
			fd.write("programmerType=%s\r\n" % self.param_topType)
			idx = self.gndLayout.currentIndex()
			fd.write("gndLayout=%d\r\n" % self.gndLayout.itemData(idx))
			idx = self.vccLayout.currentIndex()
			fd.write("vccLayout=%d\r\n" % self.vccLayout.itemData(idx))
			fd.write("vccVoltage=%f\r\n" % self.vccVoltage.value())
			vppLayouts = ""
			for layId in self.vppLayouts.keys():
				if self.vppLayouts[layId].checkState() == Qt.Checked:
					if vppLayouts:
						vppLayouts += ","
					vppLayouts += str(layId)
			if not vppLayouts:
				vppLayouts = "0"
			fd.write("vppLayout=%s\r\n" % vppLayouts)
			fd.write("vppVoltage=%f\r\n" % self.vppVoltage.value())
			fd.write("inputPollEnabled=%d\r\n" % int(self.inputPollEn.checkState() == Qt.Checked))
			fd.write("inputPollInterval=%f\r\n" % self.inputPollInterval.value())
			fd.write("fcntEnabled=%d\r\n" % (int(self.fcntEn.checkState() == Qt.Checked)))
			fd.write("fcntPosEdge=%d\r\n" % (int(self.fcntPosEdge.checkState() == Qt.Checked)))
			idx = self.fcntPin.currentIndex()
			pin = -1
			if idx >= 0:
				pin = self.fcntPin.itemData(idx)
			fd.write("fcntPin=%d\r\n" % pin)
			idx = self.oscPin.currentIndex()
			fd.write("oscillatorMask=%X\r\n" % self.oscPin.itemData(idx).obj)
			fd.write("oscillatorDiv=%d\r\n" % self.oscDiv.value())
			fd.write("zifOutEnMask=%X\r\n" % self.zifWidget.getOutEnMask())
			fd.write("zifOutMask=%X\r\n" % self.zifWidget.getOutMask())
		except (IOError), e:
			QMessageBox.critical(self, "Failed to save settings",
					     "Failed to write settings to file: %s" % str(e))

	def saveSettings(self):
		(fn, selFltr) = QFileDialog.getSaveFileName(
			self, "Save settings", "",
			"Toprammer-unitest settings (*.tus)")
		if not fn:
			return
		if not fn.endswith(".tus"):
			fn += ".tus"
		self.__saveFile(fn)

	def closeEvent(self, e):
		self.inputPollTimer.stop()

	def queryTop(self, funcname, *parameters):
		self.inputPollBlocked += 1 # Avoid recursion
		(failed, returnValue) = self.mainWindow.runOperationSync(
				HwThread.TASK_GENERICTOPCALL,
				GenericTopCall(funcname, *parameters))
		self.inputPollBlocked -= 1
		if failed:
			raise TOPException("Failed to query TOP %s\n%s" % (funcname, str(returnValue)))
		return returnValue

	def getMode(self):
		return self.queryTop("top.getChip().getMode()")

	def shutdown(self):
		self.inputPollTimer.stop()

	def updateZifCheckboxes(self):
		mode = self.getMode()
		blockedPins = []
		# Basic mask
		activePinMask = self.queryTop("top.getChip().getActivePinMask()")
		for i in range(0, self.zifWidget.nrPins):
			if activePinMask & bit(i) == 0:
				blockedPins.append(i + 1)
		# GND
		idx = self.gndLayout.currentIndex()
		lay = self.gndLayout.itemData(idx)
		blockedPins.extend(self.queryTop("top.gnd.ID2pinlist(...)", lay))
		# VCC
		idx = self.vccLayout.currentIndex()
		lay = self.vccLayout.itemData(idx)
		blockedPins.extend(self.queryTop("top.vcc.ID2pinlist(...)", lay))
		# VPP
		for key in self.vppLayouts.keys():
			if self.vppLayouts[key].checkState() == Qt.Checked:
				blockedPins.extend(self.queryTop("top.vpp.ID2pinlist(...)", key))
		# OSC
		idx = self.oscPin.currentIndex()
		mask = self.oscPin.itemData(idx).obj
		for i in range(0, self.zifWidget.nrPins):
			if mask & bit(i):
				blockedPins.append(i + 1)
		# Freq counter
		if mode == Chip_Unitest.MODE_FCNT:
			idx = self.fcntPin.currentIndex()
			pinNumber = self.fcntPin.itemData(idx)
			blockedPins.append(pinNumber + 1)
		# Set blocked pins in ZIF widget
		self.zifWidget.setBlockedPins(tuple(set(blockedPins)))

	def gndLayoutChanged(self, unused=None):
		if self.uiChangeBlocked:
			return
		idx = self.gndLayout.currentIndex()
		selLayout = self.gndLayout.itemData(idx)
		try:
			self.queryTop("top.getChip().setGND(...)", selLayout)
		except (TOPException), e:
			QMessageBox.critical(self, "TOP communication failed",
				"Failed to set GND layout:\n" +\
				str(e))
			return
		self.updateZifCheckboxes()

	def vccLayoutChanged(self, unused=None):
		if self.uiChangeBlocked:
			return
		selVoltage = self.vccVoltage.value()
		idx = self.vccLayout.currentIndex()
		selLayout = self.vccLayout.itemData(idx)
		try:
			self.queryTop("top.getChip().setVCC(...)", selVoltage, selLayout)
		except (TOPException), e:
			QMessageBox.critical(self, "TOP communication failed",
				"Failed to set VCC layout:\n" +\
				str(e))
			return
		self.updateZifCheckboxes()

	def vppLayoutChanged(self, unused=None):
		if self.uiChangeBlocked:
			return
		selVoltage = self.vppVoltage.value()
		selLayouts = []
		for key in self.vppLayouts.keys():
			if self.vppLayouts[key].checkState() == Qt.Checked:
				selLayouts.append(key)
		try:
			self.queryTop("top.getChip().setVPP(...)", selVoltage, selLayouts)
		except (TOPException), e:
			QMessageBox.critical(self, "TOP communication failed",
				"Failed to set VPP layout:\n" +\
				str(e))
			return
		self.updateZifCheckboxes()

	def doInputPollTimer(self):
		if self.inputPollBlocked:
			# Blocked. Reschedule.
			self.inputPollTimer.start(1)
			return
		ok = self.zifWidget.readInputs()
		if ok:
			if self.fcntEn.checkState() == Qt.Checked:
				ok = self.__readFcntValue()
				if ok:
					self.__updateFcntValueLabel()
		if not ok:
			# Whoops, error. Disable input polling
			self.inputPollEn.setCheckState(Qt.Unchecked)
			return False
		# Reschedule
		inter = int(self.inputPollInterval.value() * 1000)
		self.inputPollTimer.start(inter)
		return True

	def inputPollChanged(self, unused=None):
		if self.uiChangeBlocked:
			return
		if self.inputPollEn.checkState() == Qt.Checked:
			self.inputPollInterval.setEnabled(True)
			if self.doInputPollTimer():
				inter = int(self.inputPollInterval.value() * 1000)
				self.inputPollTimer.start(inter)
		else:
			self.inputPollInterval.setEnabled(False)
			self.inputPollTimer.stop()

	def fcntChanged(self, unused=None):
		if self.uiChangeBlocked:
			return
		try:
			if self.fcntEn.checkState() == Qt.Checked:
				self.switchMode(Chip_Unitest.MODE_FCNT)
				idx = self.fcntPin.currentIndex()
				pinNumber = self.fcntPin.itemData(idx)
				inv = (self.fcntPosEdge.checkState() != Qt.Checked)
				self.queryTop("top.getChip().setFreqCountPin(...)",
					      pinNumber, inv)
				self.__readFcntValue()
				self.__updateFcntValueLabel()
				# Force enable input polling
				self.inputPollEn.setCheckState(Qt.Checked)
				self.inputPollEn.setEnabled(False)
			else:
				self.switchMode(Chip_Unitest.MODE_UNITEST)
				self.__updateFcntValueLabel()
				self.inputPollEn.setEnabled(True)
		except (TOPException), e:
			QMessageBox.critical(self, "TOP communication failed",
				"Failed configure frequency counter:\n" +\
				str(e))
			return
		self.updateZifCheckboxes()

	def oscChanged(self, unused=None):
		if self.uiChangeBlocked:
			return
		try:
			div = self.oscDiv.value()
			self.queryTop("top.getChip().setOscDivider(...)", div)
			idx = self.oscPin.currentIndex()
			mask = self.oscPin.itemData(idx).obj
			self.queryTop("top.getChip().setOscMask(...)", mask)
		except (TOPException), e:
			QMessageBox.critical(self, "TOP communication failed",
				"Failed configure oscillator:\n" +\
				str(e))
			return
		self.oscFreq.setText("%.03f Hz" % (float(self.param_oscFreq) / div))
		self.updateZifCheckboxes()

class GuiUserInterface(AbstractUserInterface):
	# Global progress
	PROGRESSMETER_USER_GLOBAL	= AbstractUserInterface.PROGRESSMETER_USER + 0

	def __init__(self, hwThread):
		self.hwThread = hwThread

	def progressMeterInit(self, meterId, message, nrSteps):
		self.hwThread.appendMessage("progrInit", (meterId, message, nrSteps))

	def progressMeterFinish(self, meterId):
		self.hwThread.appendMessage("progrFinish", meterId)

	def progressMeter(self, meterId, step):
		self.hwThread.appendMessage("progress", (meterId, step))

	def __consoleMessage(self, message):
		self.hwThread.appendMessage("console", message + "\n")

	def warningMessage(self, message):
		self.__consoleMessage("WARNING: " + message)

	def infoMessage(self, message):
		self.__consoleMessage(message)

	def debugMessage(self, message):
		self.__consoleMessage(message)

class GenericTopCall(object):
	"One call to 'class Top'. Used by TASK_GENERICTOPCALL"

	def __init__(self, methodName, *parameters, **userData):
		self.methodName = methodName
		self.parameters = parameters
		self.result = None
		self.userData = userData

class HwThread(QThread):
	TASK_SHUTDOWN		= 0
	TASK_INITCHIP		= 1
	TASK_GENERICTOPCALL	= 2

	class CancelException(Exception):
		def __init__(self):
			Exception.__init__(self, "Operation cancelled")

	def __init__(self, mainWindow):
		QThread.__init__(self, mainWindow)

		self.mainWindow = mainWindow
		self.killRequest = False
		self.messageQueue = []
		self.top = None
		self.task = None
		self.opaqueId = None
		self.taskParameter = None
		self.cancel = False
		self.cancellationBlocked = 0

		self.waitCondition = QWaitCondition()
		self.mutex = QMutex()

		self.setTopParameters()
		self.setDevice()

		self.start()

	def killThread(self):
		if self.isRunning():
			self.mutex.lock()
			self.task = self.TASK_SHUTDOWN
			self.killRequest = True
			self.waitCondition.wakeAll()
			self.mutex.unlock()
			self.wait()

	def setDevice(self, devIdentifier=None):
		assert(self.top is None and self.task is None)
		self.param_devIdentifier = devIdentifier

	def setTopParameters(self, verbose=2, forceLevel=0,
			     usebroken=True, forceBitfileUpload=False):
		assert(self.top is None and self.task is None)
		self.param_verbose = verbose
		self.param_forceLevel = forceLevel
		self.param_usebroken = usebroken
		self.param_forceBitfileUpload = forceBitfileUpload

	def triggerTask(self, task, taskParameter=None,
			opaqueId=None, mutexIsLocked=False):
		if not mutexIsLocked:
			self.mutex.lock()
		self.cancel = False
		self.task = task
		self.opaqueId = opaqueId
		self.taskParameter = taskParameter
		self.waitCondition.wakeAll()
		if not mutexIsLocked:
			self.mutex.unlock()

	def run(self):
		self.mutex.lock()
		while True:
			if not self.killRequest and self.task is None:
				self.waitCondition.wait(self.mutex)
			self.mutex.unlock()
			self.__taskWorker()
			self.mutex.lock()
			if self.killRequest and self.task is None:
				break
		self.mutex.unlock()

	def cancelTask(self):
		self.mutex.lock()
		self.cancel = True
		self.mutex.unlock()

	def __blockCancellation(self):
		self.cancellationBlocked += 1

	def __unblockCancellation(self):
		self.cancellationBlocked -= 1

	def __cancellationPoint(self):
		# Mutex must be locked
		if not self.cancel:
			return
		if self.cancellationBlocked:
			return
		self.cancel = False
		self.mutex.unlock()
		raise HwThread.CancelException() # Caught in __taskWorker

	def __doCancelTask(self):
		# Make sure the device is in a consistent state.
		self.__blockCancellation()
		if self.top:
			print "Operation cancelled. Resetting chip."
			self.top.resetChip()
		self.__unblockCancellation()

	def appendMessage(self, message, data, nocancel=False):
		# Append a message to the message queue.
		# This is a cancellation point!
		self.mutex.lock()
		if not nocancel:
			self.__cancellationPoint()
		self.messageQueue.append( (message, data) )
		self.mutex.unlock()
		self.__notifyMainWindow()

	def __taskWorker(self):
		failed = True
		try:
			self.cancellationBlocked = 0
			result = self.__runTask(self.task)
			failed = False
		except (TOPException), e:
			result = e
		except (HwThread.CancelException), e:
			self.__doCancelTask()
			result = e
		except (Exception), e:
			result = e
		self.appendMessage("finished", (self.opaqueId, failed, result),
				   nocancel=True)
		self.task = None
		self.taskParameter = None
		self.opaqueId = None

	def __runTask(self, task):
		retval = None
		if task == self.TASK_SHUTDOWN or task == self.TASK_INITCHIP:
			if self.top:
				self.__blockCancellation()
				self.top.shutdownChip()
				self.top.shutdownProgrammer()
				self.top = None
				self.__unblockCancellation()
			if task == self.TASK_SHUTDOWN:
				return None
		if not self.top:
			# Initialize Hardware access
			self.__blockCancellation()
			self.top = TOP(devIdentifier = self.param_devIdentifier,
				       verbose = self.param_verbose,
				       forceLevel = self.param_forceLevel,
				       usebroken = self.param_usebroken,
				       forceBitfileUpload = self.param_forceBitfileUpload,
				       userInterface = GuiUserInterface(self))
			self.__unblockCancellation()
		if task == self.TASK_INITCHIP:
			self.__blockCancellation()
			self.top.initializeChip(self.taskParameter)
			chip = self.top.getChip()
			asciiArtLayout = None
			layoutGen = chip.getLayoutGenerator()
			if layoutGen:
				asciiArtLayout = layoutGen.zifLayoutAsciiArt()
			self.__unblockCancellation()
			retval = (chip, asciiArtLayout)
		elif task == self.TASK_GENERICTOPCALL:
			# The parameter is one GenericTopCall
			# or a list of calls.
			topCallList = self.taskParameter
			if not isinstance(topCallList, list) and\
			   not isinstance(topCallList, tuple):
				# It is only a single call. Make an iterable.
				topCallList = (topCallList, )
			self.__globalProgressInit(len(topCallList))
			# Iterate over the list of GenericTopCalls
			for topCallIndex, topCall in enumerate(topCallList):
				method = topCall.methodName.strip()
				if method.endswith(")"): # strip (...) suffix
					method = method[:method.rfind("(")]
				if method.startswith("top."): # strip 'top.' prefix
					method = method[4:]
				paramList = []
				for i in range(len(topCall.parameters)):
					paramList.append("topCall.parameters[%d]" % i)
				result = eval("self.top.%s(%s)" % (method, ", ".join(paramList)))
				topCall.result = result
				self.__globalProgress(topCallIndex + 1)
			# If there was only one call, return the result.
			# Otherwise return the complete call-list including results.
			if len(topCallList) == 1:
				retval = topCallList[0].result
			else:
				retval = topCallList
		else:
			raise TOPException("INTERNAL ERROR: HwThread: unknown task")
		return retval

	def __globalProgressInit(self, nrSteps):
		self.appendMessage("progrInit",
				   (GuiUserInterface.PROGRESSMETER_USER_GLOBAL,
				    None, nrSteps))

	def __globalProgress(self, step):
		self.appendMessage("progress",
				   (GuiUserInterface.PROGRESSMETER_USER_GLOBAL,
				    step))
		return step

	def __notifyMainWindow(self):
		QApplication.postEvent(self.mainWindow, QEvent(EVENT_HWTHREAD))

	def handleMessageQueue(self):
		self.mutex.lock()
		for (message, data) in self.messageQueue:
			if message == "finished":
				self.mainWindow.hardwareTaskFinished(
					opaqueId=data[0], failed=data[1], returnValue=data[2])
			elif message == "console":
				self.mainWindow.console.showMessage(data)
			elif message == "progrInit":
				(meterId, message, nrSteps) = data
				self.mainWindow.console.progressMeterInit(meterId, nrSteps)
			elif message == "progrFinish":
				meterId = data
				self.mainWindow.console.progressMeter(meterId, -1)
			elif message == "progress":
				(meterId, step) = data
				self.mainWindow.console.progressMeter(meterId, step)
			else:
				assert(0)
		self.messageQueue = []
		self.mutex.unlock()

class Console(QDockWidget):
	STAT_OK		= 0
	STAT_ERROR	= 1
	STAT_PROGRESS	= 2

	def __init__(self, mainWindow):
		QDockWidget.__init__(self, "Console", mainWindow)

		self.addPrefix = True
		self.statusUpdateBlocked = 0

		self.setFeatures(self.DockWidgetMovable | self.DockWidgetFloatable)
		self.setWidget(QWidget(self))
		self.widget().show()
		self.widget().setLayout(QGridLayout(self.widget()))

		self.consoleMsgs = []
		self.consoleText = QTextEdit(self)
		self.consoleText.setReadOnly(True)
		self.widget().layout().addWidget(self.consoleText, 0, 0, 1, 3)

		self.statusLabel = QLabel(self)
		self.widget().layout().addWidget(self.statusLabel, 1, 0, 2, 1)

		self.chipaccessProgress = QProgressBar(self)
		self.widget().layout().addWidget(self.chipaccessProgress, 1, 1)

		self.globalProgress = QProgressBar(self)
		self.widget().layout().addWidget(self.globalProgress, 2, 1)

		self.cancelButton = QPushButton("Cancel", self)
		self.cancelButton.setEnabled(False)
		self.widget().layout().addWidget(self.cancelButton, 1, 2, 2, 1)

		self.setStatus(self.STAT_OK)

		self.idToProgressBar = {
			GuiUserInterface.PROGRESSMETER_CHIPACCESS	: self.chipaccessProgress,
			GuiUserInterface.PROGRESSMETER_USER_GLOBAL	: self.globalProgress,
		}

		self.cancelButton.released.connect(mainWindow.cancelHardwareTask)

	def blockStatusUpdate(self):
		self.statusUpdateBlocked += 1

	def unblockStatusUpdate(self):
		self.statusUpdateBlocked -= 1

	def setTaskRunning(self, running, success=True):
		if self.statusUpdateBlocked:
			return
		self.cancelButton.setEnabled(running)
		if running:
			self.setStatus(Console.STAT_PROGRESS)
			# Set progress meters to "busy"
			for meterId in self.idToProgressBar.keys():
				self.progressMeterInit(meterId, 0)
		else:
			if success:
				self.setStatus(Console.STAT_OK)
			else:
				self.setStatus(Console.STAT_ERROR)
			# Reset progress meters to 0%
			for meterId in self.idToProgressBar.keys():
				self.progressMeterInit(meterId, 2)

	def setStatus(self, status):
		if self.statusUpdateBlocked:
			return
		if status == self.STAT_OK:
			path = getIconPath("ok")
		elif status == self.STAT_ERROR:
			path = getIconPath("error")
		elif status == self.STAT_PROGRESS:
			path = getIconPath("progress")
		else:
			assert(0)
		self.statusLabel.setPixmap(QPixmap(path))

	def __commitText(self):
		limit = 100
		if len(self.consoleMsgs) > limit:
			self.consoleMsgs.pop(0)
			assert(len(self.consoleMsgs) == limit)
		html = "<HTML><BODY>" + "".join(self.consoleMsgs) + "</BODY></HTML>"
		self.consoleText.setHtml(html)
		# Scroll to end
		scroll = self.consoleText.verticalScrollBar()
		scroll.setTracking(True)
		scroll.setSliderPosition(scroll.maximum())
		scroll.setValue(scroll.maximum())

	def showMessage(self, message, bold=False):
		message = str(message)
		if not message:
			return
		newline = False
		if message.endswith("\n"):
			newline = True
			message = message[:-1]
		message = htmlEscape(message)
		if bold:
			message = "<B>" + message + "</B>"
		if self.addPrefix:
			time = str(QTime.currentTime().toString("hh:mm:ss"))
			message = "<I>[%s]</I>&nbsp;&nbsp;%s" % (time, message)
		self.addPrefix = newline
		if newline:
			message += "<BR />"
		lastmsg = None
		if self.consoleMsgs:
			lastmsg = self.consoleMsgs[-1]
		if lastmsg and not lastmsg.endswith("<BR />"):
			self.consoleMsgs[-1] = self.consoleMsgs[-1] + message
		else:
			self.consoleMsgs.append(message)
		self.__commitText()

	def progressMeterInit(self, meterId, nrSteps):
		if self.statusUpdateBlocked:
			return
		progress = self.idToProgressBar[meterId]
		progress.setMinimum(0)
		progress.setMaximum(max(0, nrSteps - 1))
		progress.setValue(progress.maximum())
		progress.setValue(0)

	def progressMeter(self, meterId, step):
		if self.statusUpdateBlocked:
			return
		progress = self.idToProgressBar[meterId]
		if progress.maximum() == 0:
			progress.setMaximum(1)
			progress.setValue(1)
		else:
			progress.setValue(step)

class HexEditWidget(QWidget):
	def __init__(self, scrollArea, parent=None):
		QWidget.__init__(self, parent)
		self.scrollArea = scrollArea

		self.bgColor = QColor("#FFFFFF")
		self.cursor0Color = QColor("#A0A07F")
		self.cursor1Color = QColor("#D0D0AF")

		font = self.font()
		font.setFamily("monospace")
		font.setFixedPitch(True)
		font.setPointSize(10)
		self.setFont(font)
		self.charWidth = self.fontMetrics().width("x")
		self.charHeight = self.fontMetrics().height()

		self.bytesPerLine = 16

		self.previousData = b""
		self.setData(b"")
		self.__setCursor(0, False)

		self.setFocusPolicy(Qt.StrongFocus)

	def updateText(self):
		lines = []
		if self.data:
			for i in range(0, len(self.data), self.bytesPerLine):
				end = min(i + self.bytesPerLine, len(self.data))
				data = self.data[i : end]
				try:
					prevData = self.previousData[i : end]
				except IndexError:
					prevData = None
				if prevData == data:
					lines.append(self.textLines[i // self.bytesPerLine])
				else:
					text = [ "[%08X]: " % i ]
					for byte in data:
						text.append(" " + byte2hex(byte))
					if len(data) % self.bytesPerLine:
						# padding
						nrLeft = self.bytesPerLine - (len(data) % self.bytesPerLine)
						text.append("   " * nrLeft)
					text.append("  |")
					for byte in data:
						text.append(bytes2ascii(byte))
					text.append("|")
					lines.append("".join(text))
		else:
			lines = [ "<The buffer is empty>", ]
		self.textLines = lines
		self.nrLines = len(lines)
		self.previousData = self.data

		width = self.fontMetrics().width(self.textLines[0])
		height = self.nrLines * self.charHeight
		self.resize(width + 20, height + 20)
		self.repaint()

	def getData(self):
		return self.data

	def setData(self, data):
		if not data:
			data = ""
		self.data = data
		self.updateText()
		self.__setCursor(0, False)

	def charInput(self, char):
		if not self.data:
			return
		data = list(self.data)
		assert(self.cursorByte < len(data))
		if self.cursorOnAscii:
			data[self.cursorByte] = char
			self.__setCursor(self.cursorByte + 1, True)
		else:
			dataByte = byte2int(data[self.cursorByte])
			char = ord(char.upper())
			if char >= ord("0") and char <= ord("9"):
				nibble = char - ord("0")
			elif char >= ord("A") and char <= ord("F"):
				nibble = char - ord("A") + 10
			else:
				return
			if self.cursorNibble == 0:
				dataByte = (dataByte & 0xF0) | nibble
			else:
				dataByte = (dataByte & 0x0F) | (nibble << 4)
			data[self.cursorByte] = chr(dataByte)
			if self.cursorNibble == 1:
				self.cursorNibble = 0
			else:
				self.__setCursor(self.cursorByte + 1, False)
		self.data = "".join(data)
		self.updateText()

	def keyPressEvent(self, e):
		linesOnScreen = self.scrollArea.viewport().height() // self.charHeight

		if e.matches(QKeySequence.Delete) or\
		   e.key() == Qt.Key_Backspace:
			self.__setCursor(self.cursorByte - 1, self.cursorOnAscii)
			return

		if e.matches(QKeySequence.MoveToNextChar):
			self.__setCursor(self.cursorByte + 1, self.cursorOnAscii)
			return
		if e.matches(QKeySequence.MoveToPreviousChar):
			self.__setCursor(self.cursorByte - 1, self.cursorOnAscii)
			return
		if e.matches(QKeySequence.MoveToStartOfLine):
			self.__setCursor(self.cursorByte - self.cursorByte % self.bytesPerLine,
					 self.cursorOnAscii)
			return
		if e.matches(QKeySequence.MoveToEndOfLine):
			self.__setCursor(self.cursorByte - self.cursorByte % self.bytesPerLine
					 + self.bytesPerLine - 1,
					 self.cursorOnAscii)
			return
		if e.matches(QKeySequence.MoveToNextLine):
			self.__setCursor(self.cursorByte + self.bytesPerLine, self.cursorOnAscii)
			return
		if e.matches(QKeySequence.MoveToPreviousLine):
			self.__setCursor(self.cursorByte - self.bytesPerLine, self.cursorOnAscii)
			return
		if e.matches(QKeySequence.MoveToStartOfDocument):
			self.__setCursor(0, self.cursorOnAscii)
			return
		if e.matches(QKeySequence.MoveToEndOfDocument):
			self.__setCursor(len(self.data) - 1, self.cursorOnAscii)
			return
		if e.matches(QKeySequence.MoveToNextPage):
			self.__setCursor(self.cursorByte + int(linesOnScreen * 0.8) * self.bytesPerLine,
					 self.cursorOnAscii)
			return
		if e.matches(QKeySequence.MoveToPreviousPage):
			self.__setCursor(self.cursorByte - int(linesOnScreen * 0.8) * self.bytesPerLine,
					 self.cursorOnAscii)
			return

		text = str(e.text())
		if text:
			key = ord(text[0])
			if self.cursorOnAscii:
				self.charInput(chr(key))
			else:
				if (key >= ord("0") and key <= ord("9")) or\
				   (key >= ord("a") and key <= ord("f")) or\
				   (key >= ord("A") and key <= ord("F")):
					self.charInput(chr(key))

	def __setCursor(self, byteNr, asciiArea):
		byteNr = min(byteNr, len(self.data) - 1)
		byteNr = max(byteNr, 0)
		self.cursorOnAscii = asciiArea
		self.cursorByte = byteNr
		self.cursorNibble = 1
		self.repaint()
		(x, y) = self.__cursorUpperLeftEdge()
		self.scrollArea.ensureVisible(x, y)

	def mousePressEvent(self, e):
		x = e.pos().x()
		y = e.pos().y()
		byteAreaX = self.charWidth * 13
		byteAreaY = 3
		asciiAreaX = self.charWidth * (13 + 3 * self.bytesPerLine + 3 - 1)
		asciiAreaY = 3
		if x >= byteAreaX and\
		   y >= byteAreaY and\
		   x <= byteAreaX + self.charWidth * 3 * self.bytesPerLine and\
		   y <= byteAreaY + self.charHeight * self.nrLines:
			# Click in byte area.
			x -= byteAreaX
			y -= byteAreaY
			line = y // self.charHeight
			column = x // (self.charWidth * 3)
			self.__setCursor(line * self.bytesPerLine + column,
					 False)
			return
		if x >= asciiAreaX and\
		   y >= asciiAreaY and\
		   x <= asciiAreaX + self.charWidth * self.bytesPerLine and\
		   y <= asciiAreaY + self.charHeight * self.nrLines:
			# Click on ascii area.
			x -= asciiAreaX
			y -= asciiAreaY
			line = y // self.charHeight
			column = x // self.charWidth
			self.__setCursor(line * self.bytesPerLine + column,
					 True)
			return

	def __cursorUpperLeftEdge(self):
		if self.cursorOnAscii:
			x = self.charWidth * (13 + 3 * self.bytesPerLine + 3 - 1)
			x += self.charWidth * (self.cursorByte % self.bytesPerLine)
			y = self.charHeight * (self.cursorByte // self.bytesPerLine)
			y += 3
		else:
			x = self.charWidth * 13
			x += self.charWidth * 3 * (self.cursorByte % self.bytesPerLine)
			y = self.charHeight * (self.cursorByte // self.bytesPerLine)
			y += 3
		return (x, y)

	def paintEvent(self, e):
		p = QPainter(self)

		# Background
		p.fillRect(0, 0, self.width(), self.height(), self.bgColor)

		# Cursor
		if self.data and self.hasFocus():
			(x, y) = self.__cursorUpperLeftEdge()
			if self.cursorOnAscii:
				p.fillRect(x, y, self.charWidth, self.charHeight,
					   self.cursor0Color)
			else:
				p.fillRect(x, y, self.charWidth * 2, self.charHeight,
					   self.cursor1Color)
				if self.cursorNibble == 0:
					x += self.charWidth
				p.fillRect(x, y, self.charWidth, self.charHeight,
					   self.cursor0Color)

		# Text
		y = self.charHeight
		for line in self.textLines:
			p.drawText(0, y, line)
			y += self.charHeight

class HexEdit(QScrollArea):
	def __init__(self, parent=None):
		QScrollArea.__init__(self, parent)

		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.setWidgetResizable(False)
		self.setWidget(HexEditWidget(self, self))

	def setData(self, data):
		self.widget().setData(data)

	def getData(self):
		return self.widget().getData()

class BufferWidget(QWidget):
	def __init__(self, mainWindow, name):
		QWidget.__init__(self, mainWindow)
		self.mainWindow = mainWindow
		self.name = name
		self.hide()
		self.setLayout(QGridLayout(self))
		self.setAvailable(False)
		self.setReadOnly()

	def getName(self):
		return self.name

	def setAvailable(self, available):
		self.available = available

	def isAvailable(self):
		return self.available

	def setReadOnly(self, readOnly=True):
		self.readOnly = readOnly

	def isReadOnly(self):
		return self.readOnly

	def getRawData(self):
		return None

	def setRawData(self, data):
		return False

	def setDataWithIHexInterpreter(self, interp, readRaw):
		return False

	def clear(self):
		pass

class InfoBufferWidget(BufferWidget):
	def __init__(self, mainWindow, name):
		BufferWidget.__init__(self, mainWindow, name)

		self.zifLayout = QLabel(self)
		font = self.zifLayout.font()
		font.setFixedPitch(True)
		font.setFamily("monospace")
		font.setPointSize(7)
		self.zifLayout.setFont(font)
		self.layout().addWidget(self.zifLayout, 0, 0, 6, 1)

		def addLabel(name, y):
			l = QLabel(name, self)
			l.setAlignment(Qt.AlignTop | Qt.AlignLeft)
			self.layout().addWidget(l, y, 1)
			label = QLabel(self)
			label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
			font = label.font()
			font.setBold(True)
			label.setFont(font)
			self.layout().addWidget(label, y, 2)
			return label

		self.chipName = addLabel("Chip name:", 0)
		self.comment = addLabel("Comment:", 1)
		self.packages = addLabel("Packages:", 2)
		self.chipSig = addLabel("Chip signature bytes:", 3)
		self.maintainer = addLabel("Chip maintainer:", 4)

		self.layout().setColumnStretch(3, 99)
		self.layout().setRowStretch(5, 99)

		self.clear()

	def clear(self):
		self.chipName.setText("<No chip selected>")
		self.setComment(None)
		self.setChipSignature(None)
		self.setChipLayout(None)
		self.setPackages(None)
		self.setMaintainer(None)

	def setChipSignature(self, bindata):
		if bindata:
			self.chipSig.setText(bytes2hex(bindata))
		else:
			self.chipSig.setText("None")

	def setComment(self, comment):
		if comment:
			self.comment.setText(comment)
		else:
			self.comment.setText("None")

	def setPackages(self, packages):
		def p2str(param):
			(packageName, description) = param
			text = packageName
			if description:
				text += " (%s)" % description
			return text

		if packages:
			pckgs = map(p2str, packages)
			self.packages.setText("\n".join(pckgs))
		else:
			self.packages.setText("Unknown")

	def setMaintainer(self, maintainer):
		if maintainer:
			# Remove email address
			idx = maintainer.find("<")
			if idx >= 0:
				maintainer = maintainer[:idx]
			self.maintainer.setText(maintainer.strip())
		else:
			self.maintainer.setText("None")

	def setupDescription(self, chipDescription):
		self.chipName.setText(chipDescription.description)
		self.setComment(chipDescription.comment)
		self.setPackages(chipDescription.packages)
		self.setMaintainer(chipDescription.maintainer)

	def setChipLayout(self, asciiArtLayout):
		if asciiArtLayout:
			self.zifLayout.setText(asciiArtLayout)
			self.zifLayout.setFrameShape(QFrame.StyledPanel)
		else:
			self.zifLayout.clear()
			self.zifLayout.setFrameShape(QFrame.NoFrame)

class ImageBufferWidget(BufferWidget):
	def __init__(self, mainWindow, name):
		BufferWidget.__init__(self, mainWindow, name)

		self.browser = HexEdit(self)
		self.layout().addWidget(self.browser, 0, 0)

	def loadImage(self, image):
		self.browser.setData(image)

	def getRawData(self):
		return self.browser.getData()

	def setRawData(self, data):
		if self.isReadOnly():
			return False
		self.loadImage(data)
		return True

	def clear(self):
		self.loadImage(None)

class BitBufferWidget(BufferWidget):
	def __init__(self, mainWindow, name, bitDescriptionsAttr):
		BufferWidget.__init__(self, mainWindow, name)
		self.bitDescriptionsAttr = bitDescriptionsAttr

		self.bitsAreaScroll = QScrollArea(self)
		self.layout().addWidget(self.bitsAreaScroll, 0, 0)
		self.bitsAreaScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.bitsAreaScroll.setWidgetResizable(False)

		self.bitsArea = None
		self.image = None
		self.checkboxes = []

	def __getBitDescription(self, bitNr):
		if not self.mainWindow.currentChipDescription:
			return ""
		bitDescList = getattr(self.mainWindow.currentChipDescription,
				      self.bitDescriptionsAttr, None)
		if not bitDescList:
			return ""
		bitDesc = filter(lambda x: x.bitNr == bitNr,
				 bitDescList)
		if not bitDesc:
			return ""
		return bitDesc[0].description

	def loadImage(self, image):
		self.image = image
		for checkbox in self.checkboxes:
			checkbox.deleteLater()
		self.checkboxes = []
		if self.bitsArea:
			self.bitsArea.deleteLater()
			self.bitsArea = None
		if not self.image:
			return
		self.bitsArea = QWidget(self)
		self.bitsArea.setLayout(QGridLayout(self.bitsArea))
		self.bitsArea.layout().addWidget(QLabel("Currently set %s:" % self.getName(),
							self.bitsArea),
						 0, 0)
		self.hexView = QLabel(self.bitsArea)
		font = self.hexView.font()
		font.setBold(True)
		self.hexView.setFont(font)
		self.bitsArea.layout().addWidget(self.hexView, 0, 1)
		for i in range(0, len(image) * 8):
			desc = self.__getBitDescription(i)
			if desc:
				desc = " (%s)" % desc
			checkbox = QCheckBox("bit %d%s" % (i, desc), self.bitsArea)
			if byte2int(image[i // 8]) & bit(i % 8):
				checkbox.setCheckState(Qt.Checked)
			self.bitsArea.layout().addWidget(checkbox, 1 + i, 0, 1, 2)
			checkbox.stateChanged.connect(self.__bitStateChanged)
			self.checkboxes.append(checkbox)
		self.__updateHexView()

	def __updateHexView(self):
		self.hexView.setText(bytes2hex(self.image))
		self.bitsAreaScroll.setWidget(self.bitsArea)

	def __bitStateChanged(self, unused):
		self.image = ""
		tmp = 0
		i = 0
		for checkbox in self.checkboxes:
			if checkbox.checkState() == Qt.Checked:
				tmp |= bit(i)
			i += 1
			if i == 8:
				self.image += chr(tmp)
				i = 0
				tmp = 0
		assert(i == 0)
		self.__updateHexView()

	def getRawData(self):
		return self.image

	def setRawData(self, data):
		if self.isReadOnly():
			return False
		if len(data) > 32: # Don't want huge files
			return False
		self.loadImage(data)
		return True

	def clear(self):
		self.loadImage(None)

class ProgmemBufferWidget(ImageBufferWidget):
	def __init__(self, mainWindow):
		ImageBufferWidget.__init__(self, mainWindow, "program memory")

	def setDataWithIHexInterpreter(self, interp, readRaw):
		return self.setRawData(interp.getProgmem(dontInterpretSections = readRaw))

class EEPROMBufferWidget(ImageBufferWidget):
	def __init__(self, mainWindow):
		ImageBufferWidget.__init__(self, mainWindow, "(E)EPROM memory")

	def setDataWithIHexInterpreter(self, interp, readRaw):
		return self.setRawData(interp.getEEPROM(dontInterpretSections = readRaw))

class RAMBufferWidget(ImageBufferWidget):
	def __init__(self, mainWindow):
		ImageBufferWidget.__init__(self, mainWindow, "RAM memory")

	def setDataWithIHexInterpreter(self, interp, readRaw):
		return self.setRawData(interp.getRAM(dontInterpretSections = readRaw))

class FuseBufferWidget(BitBufferWidget):
	def __init__(self, mainWindow):
		BitBufferWidget.__init__(self, mainWindow, "fuse bits", "fuseDesc")

	def setDataWithIHexInterpreter(self, interp, readRaw):
		return self.setRawData(interp.getFusebits(dontInterpretSections = readRaw))

class LockBufferWidget(BitBufferWidget):
	def __init__(self, mainWindow):
		BitBufferWidget.__init__(self, mainWindow, "lock bits", "lockbitDesc")

	def setDataWithIHexInterpreter(self, interp, readRaw):
		return self.setRawData(interp.getLockbits(dontInterpretSections = readRaw))

class BufferTabWidget(QTabWidget):
	def __init__(self, mainWindow):
		QTabWidget.__init__(self, mainWindow)
		self.mainWindow = mainWindow

		self.infoBuffer = InfoBufferWidget(mainWindow, "chip info")
		self.progmemBuffer = ProgmemBufferWidget(mainWindow)
		self.eepromBuffer = EEPROMBufferWidget(mainWindow)
		self.fuseBuffer = FuseBufferWidget(mainWindow)
		self.lockBuffer = LockBufferWidget(mainWindow)
		self.ramBuffer = RAMBufferWidget(mainWindow)

		self.setTabPosition(self.South)
		self.__addBufferTab(self.infoBuffer, readOnly=True)
		self.removeAll()

	def __addBufferTab(self, bufferWidget, readOnly=False):
		self.addTab(bufferWidget, bufferWidget.getName())
		bufferWidget.setReadOnly(readOnly)
		bufferWidget.setAvailable(True)

	def __removeBufferTab(self, bufferWidget):
		self.removeTab(self.indexOf(bufferWidget))
		bufferWidget.clear()
		bufferWidget.setAvailable(False)

	def __removeAll(self):
		self.__removeBufferTab(self.progmemBuffer)
		self.__removeBufferTab(self.eepromBuffer)
		self.__removeBufferTab(self.fuseBuffer)
		self.__removeBufferTab(self.lockBuffer)
		self.__removeBufferTab(self.ramBuffer)

	def removeAll(self):
		self.__removeAll()

	def setupBuffers(self, chipSupportFlags):
		prevSelect = self.getCurrentBuffer()
		self.__removeAll()
		for (bufferWidget, flagsMask) in (
		    (self.progmemBuffer, Chip.SUPPORT_PROGMEMREAD | Chip.SUPPORT_PROGMEMWRITE),
		    (self.eepromBuffer, Chip.SUPPORT_EEPROMREAD | Chip.SUPPORT_EEPROMWRITE),
		    (self.fuseBuffer, Chip.SUPPORT_FUSEREAD | Chip.SUPPORT_FUSEWRITE),
		    (self.lockBuffer, Chip.SUPPORT_LOCKREAD | Chip.SUPPORT_LOCKWRITE),
		    (self.ramBuffer, Chip.SUPPORT_RAMREAD | Chip.SUPPORT_RAMWRITE)):
			if chipSupportFlags & flagsMask:
				self.__addBufferTab(bufferWidget)
		if prevSelect and prevSelect.isAvailable():
			self.setCurrentIndex(self.indexOf(prevSelect))

	def loadBuffers(self, images):
		try:
			self.progmemBuffer.loadImage(images["progmem"])
		except KeyError:
			pass # Ignore
		try:
			self.eepromBuffer.loadImage(images["eeprom"])
		except KeyError:
			pass # Ignore
		try:
			self.fuseBuffer.loadImage(images["fusebits"])
		except KeyError:
			pass # Ignore
		try:
			self.lockBuffer.loadImage(images["lockbits"])
		except KeyError:
			pass # Ignore
		try:
			self.ramBuffer.loadImage(images["ram"])
		except KeyError:
			pass # Ignore

	def verifyBuffers(self, images):
		fail = False
		for (imageName, bufferWidget) in (("progmem", self.progmemBuffer),
						  ("eeprom", self.eepromBuffer),
						  ("fusebits", self.fuseBuffer),
						  ("ram", self.ramBuffer)):
			try:
				image = images[imageName]
			except KeyError:
				continue
			bufImage = bufferWidget.getRawData()
			if not bufImage:
				if not image:
					# Both images are empty. Go on...
					continue
				self.mainWindow.console.showMessage(
					"Chip verify of %s FAILED! "
					"There is no data in the "
					"%s buffer. First load data into "
					"the buffer tab, please.\n" %\
					(bufferWidget.getName(),
					 bufferWidget.getName()),
					bold=True)
				fail = True
				continue
			if len(bufImage) > len(image):
				self.mainWindow.console.showMessage(
					"Chip verify of %s FAILED! "
					"Buffer data is larger than "
					"chip memory.\n" %\
					bufferWidget.getName(),
					bold=True)
				fail = True
				continue
			compareSize = min(len(image), len(bufImage))
			if len(image) != len(bufImage):
				self.mainWindow.console.showMessage(
					"%s: Only comparing the first 0x%X bytes due "
					"to a mismatch of the buffer size (0x%X) "
					"with the actual device image size (0x%X).\n" %\
					(bufferWidget.getName(), compareSize,
					 len(bufImage), len(image)))
			if bufImage[:compareSize] != image[:compareSize]:
				self.mainWindow.console.showMessage(
					"Chip verify of %s FAILED! "
					"Image data mismatch.\n" %\
					bufferWidget.getName(),
					bold=True)
				fail = True
				continue
		if fail:
			self.mainWindow.console.setStatus(Console.STAT_ERROR)
		else:
			self.mainWindow.console.showMessage("Chip verify succeed\n", bold=True)
			self.mainWindow.console.setStatus(Console.STAT_OK)
		return not fail

	def getCurrentBuffer(self):
		return self.currentWidget()

class ChipSelectDialog(QDialog):
	ALL_VENDORS	= "--- All vendors ---"

	def __init__(self, parent):
		QDialog.__init__(self, parent)
		self.setWindowTitle("Select chip")
		self.setLayout(QGridLayout(self))

		groupBox = QGroupBox("Chip type", self)
		groupBox.setLayout(QGridLayout(groupBox))
		self.allRadio = QRadioButton("All types", groupBox)
		self.allRadio.setChecked(Qt.Checked)
		groupBox.layout().addWidget(self.allRadio, 0, 0)
		self.mcuRadio = QRadioButton("Microcontrollers", groupBox)
		groupBox.layout().addWidget(self.mcuRadio, 1, 0)
		self.epromRadio = QRadioButton("EPROMs", groupBox)
		groupBox.layout().addWidget(self.epromRadio, 2, 0)
		self.eepromRadio = QRadioButton("EEPROMs", groupBox)
		groupBox.layout().addWidget(self.eepromRadio, 3, 0)
		self.galRadio = QRadioButton("PALs / GALs", groupBox)
		groupBox.layout().addWidget(self.galRadio, 4, 0)
		self.sramRadio = QRadioButton("Static RAM", groupBox)
		groupBox.layout().addWidget(self.sramRadio, 5, 0)
		self.logicRadio = QRadioButton("Logic chips", groupBox)
		groupBox.layout().addWidget(self.logicRadio, 6, 0)
		self.showBroken = QCheckBox("Show broken implementations", groupBox)
		groupBox.layout().addWidget(self.showBroken, 7, 0)
		self.layout().addWidget(groupBox, 0, 0, 2, 2)

		l = QLabel("Vendor:", self)
		self.layout().addWidget(l, 0, 2, 1, 2)
		self.vendorList = QListWidget(self)
		self.layout().addWidget(self.vendorList, 1, 2, 1, 2)

		l = QLabel("Chip:", self)
		self.layout().addWidget(l, 0, 4, 1, 2)
		self.chipList = QListWidget(self)
		self.layout().addWidget(self.chipList, 1, 4, 1, 2)

		self.okButton = QPushButton("&Ok", self)
		self.layout().addWidget(self.okButton, 2, 0, 1, 3)

		self.cancelButton = QPushButton("&Cancel", self)
		self.layout().addWidget(self.cancelButton, 2, 3, 1, 3)

		self.okButton.released.connect(self.accept)
		self.cancelButton.released.connect(self.reject)
		self.vendorList.itemSelectionChanged.connect(self.vendorSelectionChanged)
		self.chipList.itemSelectionChanged.connect(self.chipSelectionChanged)
		self.chipList.itemDoubleClicked.connect(self.accept)
		self.showBroken.stateChanged.connect(self.typeToggled)
		for radio in (self.allRadio, self.mcuRadio, self.epromRadio,
			      self.eepromRadio, self.galRadio,
			      self.sramRadio, self.logicRadio):
			radio.toggled.connect(self.typeToggled)

		self.__updateVendorList()
		self.__updateChipList()

	def __updateVendorList(self):
		previousVendor = self.__getSelectedVendor()
		selType = self.__getSelectedChipType()
		vendors = getRegisteredVendors()
		self.vendorList.clear()
		QListWidgetItem(self.ALL_VENDORS, self.vendorList)
		for vendorName in vendors.keys():
			descriptors = vendors[vendorName]
			if self.showBroken.checkState() != Qt.Checked:
				descriptors = filter(lambda d: not d.broken,
						     descriptors)
			descriptors = filter(lambda d: (d.chipType == selType or selType == -1) and\
						       (d.chipType != ChipDescription.TYPE_INTERNAL),
					     descriptors)
			if not descriptors:
				continue
			item = QListWidgetItem(vendorName, self.vendorList)
			item.setData(Qt.UserRole, descriptors)
		self.vendorList.sortItems()
		if previousVendor:
			items = self.vendorList.findItems(previousVendor, Qt.MatchExactly)
			if len(items) == 1:
				self.vendorList.setCurrentItem(items[0])
			else:
				self.vendorList.setCurrentRow(0)
		else:
			self.vendorList.setCurrentRow(0)

	def __descriptorText(self, descriptor):
		text = descriptor.description
		if not descriptor.maintainer:
			text += "  (Orphaned)"
		return text

	def __updateChipList(self):
		previousChip = self.getSelectedChip()
		selType = self.__getSelectedChipType()
		selVendor = self.__getSelectedVendor()
		self.chipList.clear()
		for descriptor in getRegisteredChips():
			if descriptor.broken and\
			   self.showBroken.checkState() != Qt.Checked:
				continue
			if descriptor.chipType != selType and selType != -1:
				continue
			if descriptor.chipType == ChipDescription.TYPE_INTERNAL:
				continue
			if selVendor != self.ALL_VENDORS and selVendor not in descriptor.chipVendors:
				continue
			item = QListWidgetItem(self.__descriptorText(descriptor),
					       self.chipList)
			item.setData(Qt.UserRole, descriptor)
		self.chipList.sortItems()
		if previousChip:
			items = self.chipList.findItems(self.__descriptorText(previousChip),
							Qt.MatchExactly)
			if len(items) == 1:
				self.chipList.setCurrentItem(items[0])
			else:
				self.chipList.setCurrentRow(0)
		else:
			self.chipList.setCurrentRow(0)

	def typeToggled(self, unused):
		self.__updateVendorList()
		self.__updateChipList()

	def vendorSelectionChanged(self):
		self.__updateChipList()

	def chipSelectionChanged(self):
		item = self.chipList.currentItem()
		self.okButton.setEnabled(bool(item))

	def __getSelectedVendor(self):
		item = self.vendorList.currentItem()
		if not item:
			return None
		return str(item.text())

	def __getSelectedChipType(self):
		# Returns ChipDescription.TYPE_... or -1 if all are selected
		for (typeId, radioButton) in (
				(ChipDescription.TYPE_MCU,	self.mcuRadio),
				(ChipDescription.TYPE_EPROM,	self.epromRadio),
				(ChipDescription.TYPE_EEPROM,	self.eepromRadio),
				(ChipDescription.TYPE_GAL,	self.galRadio),
				(ChipDescription.TYPE_SRAM,	self.sramRadio),
				(ChipDescription.TYPE_LOGIC,	self.logicRadio)):
			if radioButton.isChecked():
				return typeId
		assert(self.allRadio.isChecked())
		return -1

	def getSelectedChip(self):
		item = self.chipList.currentItem()
		if not item:
			return None
		chipDescription = item.data(Qt.UserRole)
		return chipDescription

class StatusBar(QStatusBar):
	def __init__(self, mainWindow):
		QStatusBar.__init__(self, mainWindow)

class TopToolBar(QToolBar):
	def __init__(self, mainWindow):
		QToolBar.__init__(self, "Toolbar", mainWindow)
		self.mainWindow = mainWindow
		self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
		self.setup(0)

	def setup(self, chipSupportFlags):
		mainWindow = self.mainWindow
		self.clear()
		a = self.addAction(getIcon("open"), "Load buffer", mainWindow.loadBuffer)
		a.setEnabled(chipSupportFlags != 0)
		a = self.addAction(getIcon("save"), "Save buffer", mainWindow.saveBuffer)
		a.setEnabled(chipSupportFlags != 0)
		self.addSeparator()
		self.addAction(getIcon("chip"), "Run logic tester", mainWindow.startUnitest)
		self.addAction(getIcon("chip"), "Select chip", mainWindow.selectChip)
		self.addSeparator()
		a = self.addAction(getIcon("up"), "Read chip", mainWindow.readChip)
		a.setEnabled(chipSupportFlags != 0)
		a = self.addAction(getIcon("verify"), "Verify all", mainWindow.verifyChip)
		a.setEnabled(chipSupportFlags != 0)

class RightToolBar(QToolBar):
	def __init__(self, mainWindow):
		QToolBar.__init__(self, "Toolbar", mainWindow)
		self.mainWindow = mainWindow
		self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
		self.setup(0)

	def setup(self, chipSupportFlags):
		mainWindow = self.mainWindow
		self.clear()
		if chipSupportFlags & Chip.SUPPORT_ERASE:
			self.addAction(getIcon("erase"), "Erase", mainWindow.eraseChip)
		if chipSupportFlags & Chip.SUPPORT_PROGMEMWRITE:
			self.addAction(getIcon("memory"), "Write progmem", mainWindow.writeChipProgmem)
		if chipSupportFlags & Chip.SUPPORT_EEPROMWRITE:
			self.addAction(getIcon("memory"), "Write EPROM", mainWindow.writeChipEeprom)
		if chipSupportFlags & Chip.SUPPORT_FUSEWRITE:
			self.addAction(getIcon("memory"), "Write fuses", mainWindow.writeChipFuses)
		if chipSupportFlags & Chip.SUPPORT_RAMWRITE:
			self.addAction(getIcon("memory"), "Write RAM", mainWindow.writeRam)
		if chipSupportFlags & Chip.SUPPORT_LOCKWRITE:
			self.addAction(getIcon("lock"), "Write lockbits", mainWindow.writeChipLockbits)
		if chipSupportFlags & Chip.SUPPORT_TEST:
			self.addAction(getIcon("test"), "Run unit-test", mainWindow.runTest)

class AutorunWidget(QDockWidget):
	def __init__(self, mainWindow):
		QDockWidget.__init__(self, "Autorun", mainWindow)
		self.mainWindow = mainWindow

		self.running = False
		self.currentAction = -1

		self.setFeatures(self.DockWidgetMovable | self.DockWidgetFloatable)
		self.setup(0)

	def __addCheckBox(self, row, condition, text, checked):
		if condition:
			checkbox = QCheckBox(text, self.widget())
			if checked:
				checkbox.setCheckState(Qt.Checked)
			self.widget().layout().addWidget(checkbox, row, 0)
			row += 1
			return (checkbox, row)
		return (None, row)

	def setup(self, chipSupportFlags):
		self.setWidget(QWidget(self))
		self.widget().show()
		self.widget().setLayout(QGridLayout(self.widget()))
		row = 0

		(self.testCheckBox, row) = self.__addCheckBox(row,
				chipSupportFlags & Chip.SUPPORT_TEST,
				"Run unit-test", True)
		(self.eraseCheckBox, row) = self.__addCheckBox(row,
				chipSupportFlags & Chip.SUPPORT_ERASE,
				"Erase", True)
		(self.progmemCheckBox, row) = self.__addCheckBox(row,
				chipSupportFlags & Chip.SUPPORT_PROGMEMWRITE,
				"Write program memory", True)
		(self.eepromCheckBox, row) = self.__addCheckBox(row,
				chipSupportFlags & Chip.SUPPORT_EEPROMWRITE,
				"Write (E)EPROM", True)
		(self.ramCheckBox, row) = self.__addCheckBox(row,
				chipSupportFlags & Chip.SUPPORT_RAMWRITE,
				"Write RAM", True)
		(self.fusesCheckBox, row) = self.__addCheckBox(row,
				chipSupportFlags & Chip.SUPPORT_FUSEWRITE,
				"Write fuses", True)
		(self.verifyCheckBox, row) = self.__addCheckBox(row,
				chipSupportFlags != 0,
				"Verify selected memories", True)
		(self.lockbitsCheckBox, row) = self.__addCheckBox(row,
				chipSupportFlags & Chip.SUPPORT_LOCKWRITE,
				"Write lock bits", False)

		self.runButton = None
		if chipSupportFlags != 0:
			self.runButton = QPushButton("Run", self.widget())
			self.runButton.setIconSize(QSize(32, 32))
			self.runButton.setIcon(getIcon("run"))
			self.widget().layout().addWidget(self.runButton, row, 0)
			row += 1
			self.runButton.released.connect(self.runNextChip)

		self.widget().layout().setRowStretch(row, 99)

	def isRunning(self):
		return self.running

	def abortRunWithMessage(self):
		self.abortRun(withMessage=True)

	def abortRun(self, withMessage=False):
		if withMessage:
			QMessageBox.critical(self, "Aborting autorun",
				"One action failed. Aborting autorun.\n"
				"See console messages for details.")
		self.running = False
		self.currentAction = -1;
		self.mainWindow.guiUpdateEnable()

	def runNextChip(self):
		self.running = True
		self.currentAction = 0
		res = QMessageBox.information(self, "Autorun - Please insert chip",
			"Please insert a new %s chip into the ZIF socket "
			"and press Ok to perform the operations..." %\
			self.mainWindow.currentChipDescription.description,
			QMessageBox.Ok | QMessageBox.Cancel,
			QMessageBox.Ok)
		if res != QMessageBox.Ok:
			self.abortRun()
			return
		self.runNextAction()

	def runNextAction(self):
		assert(self.currentAction >= 0)
		action = 0
		if self.testCheckBox:
			if self.currentAction == action:
				if self.__runAction(self.mainWindow.runTest,
						    self.testCheckBox,
						    "Run unit-test"):
					return
			action += 1
		if self.eraseCheckBox:
			if self.currentAction == action:
				if self.__runAction(self.mainWindow.eraseChip,
						    self.eraseCheckBox,
						    "Erase"):
					return
			action += 1
		if self.progmemCheckBox:
			if self.currentAction == action:
				if self.__runAction(self.mainWindow.writeChipProgmem,
						    self.progmemCheckBox,
						    "Write program memory"):
					return
			action += 1
		if self.eepromCheckBox:
			if self.currentAction == action:
				if self.__runAction(self.mainWindow.writeChipEeprom,
						    self.eepromCheckBox,
						    "Write (E)EPROM"):
					return
			action += 1
		if self.ramCheckBox:
			if self.currentAction == action:
				if self.__runAction(self.mainWindow.writeRam,
						    self.ramCheckBox,
						    "Write RAM"):
					return
			action += 1
		if self.fusesCheckBox:
			if self.currentAction == action:
				if self.__runAction(self.mainWindow.writeChipFuses,
						    self.fusesCheckBox,
						    "Write fuses"):
					return
			action += 1
		if self.verifyCheckBox:
			if self.currentAction == action:
				if self.__runAction(self.__verifySelectedMemories,
						    self.verifyCheckBox,
						    "Verify selected memories"):
					return
			action += 1
		if self.lockbitsCheckBox:
			if self.currentAction == action:
				if self.__runAction(self.mainWindow.writeChipLockbits,
						    self.lockbitsCheckBox,
						    "Write lock bits"):
					return
			action += 1
		self.runNextChip()

	def __runAction(self, function, checkbox, actionName):
		self.currentAction += 1
		if checkbox.checkState() == Qt.Checked:
			self.mainWindow.console.showMessage(
				"Running action: %s\n" % actionName, bold=True)
			if not function():
				self.abortRun(withMessage=True)
			return True
		return False

	def __verifySelectedMemories(self):
		def checked(cb):
			return cb and (cb.checkState() == Qt.Checked)
		return self.mainWindow.verifySelectedMemories(
			verifyProgmem = checked(self.progmemCheckBox),
			verifyEEPROM = checked(self.eepromCheckBox),
			verifyFuse = checked(self.fusesCheckBox),
			verifyRAM = checked(self.ramCheckBox))

class ProgrammerSelectDialog(QDialog):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		self.setWindowTitle("Select programmer device")
		self.setLayout(QGridLayout(self))

		self.deviceList = QListWidget(self)
		self.layout().addWidget(self.deviceList, 0, 0, 1, 2)

		self.rescanButton = QPushButton("&Rescan USB busses", self)
		self.layout().addWidget(self.rescanButton, 1, 0, 1, 2)

		self.okButton = QPushButton("&OK", self)
		self.layout().addWidget(self.okButton, 2, 0)

		self.cancelButton = QPushButton("&Cancel", self)
		self.layout().addWidget(self.cancelButton, 2, 1)

		self.rescan()

		self.deviceList.currentRowChanged.connect(self.selectionChanged)
		self.deviceList.itemDoubleClicked.connect(self.accept)
		self.okButton.released.connect(self.accept)
		self.cancelButton.released.connect(self.reject)
		self.rescanButton.released.connect(self.rescan)

	def rescan(self):
		self.deviceList.clear()
		for foundDev in TOP.findDevices():
			text = "%s  (%s)" % (foundDev.toptype,
					     foundDev.devIdentifier)
			item = QListWidgetItem(text, self.deviceList)
			item.setData(Qt.UserRole, foundDev.devIdentifier)
		self.deviceList.setCurrentRow(0)

	def getIdentifier(self):
		item = self.deviceList.currentItem()
		if not item:
			return None
		return item.data(Qt.UserRole)

	def selectionChanged(self, unused):
		if self.deviceList.currentItem():
			self.okButton.setEnabled(True)
		else:
			self.okButton.setEnabled(False)

class Operation(object):
	OP_NONE		= 0
	OP_SHUTDOWN	= 1
	OP_INITCHIP	= 2
	OP_READALL	= 3
	OP_ERASE	= 4
	OP_WRITEPROG	= 5
	OP_WRITEEPROM	= 6
	OP_WRITEFUSE	= 7
	OP_WRITELOCK	= 8
	OP_WRITERAM	= 9
	OP_TEST		= 10
	OP_VERIFY	= 11
	OP_RAWCOMMAND	= 12
	OP_SYNCHRONOUS	= 13

	def __init__(self, op, hwTask, hwTaskParam=None):
		self.op = op
		self.hwTask = hwTask
		self.hwTaskParam = hwTaskParam
		self.returnValue = None
		self.failed = False
		self.finished = False

class MainWindow(QMainWindow):
	def __init__(self, parent=None):
		QMainWindow.__init__(self, parent)
		self.setWindowTitle("TOPrammer v%s - Open Source programming suite" % VERSION)

		self.guiDisable = 0
		self.chip = None # Chip instance 
		self.currentChipDescription = None
		self.previousRawCommand = ""

		self.setStatusBar(StatusBar(self))
		self.topToolBar = TopToolBar(self)
		self.rightToolBar = RightToolBar(self)
		self.addToolBar(Qt.TopToolBarArea, self.topToolBar)
		self.addToolBar(Qt.RightToolBarArea, self.rightToolBar)

		self.setMenuBar(QMenuBar(self))

		menu = QMenu("&File", self)
		menu.addAction("&Load buffer...", self.loadBuffer)
		menu.addAction("&Save buffer...", self.saveBuffer)
		menu.addSeparator()
		menu.addAction("&Exit", self.close)
		self.menuBar().addMenu(menu)

		self.runMenu = QMenu("&Run", self)
		self.setupRunMenu(0)
		self.menuBar().addMenu(self.runMenu)

		menu = QMenu("&Programmer", self)
		menu.addAction("&Universal logic tester...", self.startUnitest)
		menu.addSeparator()
		menu.addAction("Select &programmer...", self.selectProgrammer)
		menu.addAction("&Send raw command...", self.sendRawCommand)
		self.menuBar().addMenu(menu)

		menu = QMenu("&Help", self)
		menu.addAction("&About", self.showAbout)
		self.menuBar().addMenu(menu)

		self.bufferTab = BufferTabWidget(self)
		self.setCentralWidget(self.bufferTab)

		self.console = Console(self)
		self.addDockWidget(Qt.BottomDockWidgetArea, self.console)

		self.autorun = AutorunWidget(self)
		self.addDockWidget(Qt.LeftDockWidgetArea, self.autorun)

		self.hwThread = HwThread(self)
		self.threadRunning = False
		self.queuedOps = []
		self.runningOps = {}

	def setupRunMenu(self, chipSupportFlags):
		menu = self.runMenu
		menu.clear()

		menu.addAction("&Select chip", self.selectChip)
		menu.addSeparator()

		a = menu.addAction("&Read chip", self.readChip)
		a.setEnabled(chipSupportFlags != 0)
		a = menu.addAction("&Erase", self.eraseChip)
		a.setEnabled(bool(chipSupportFlags & Chip.SUPPORT_ERASE))
		a = menu.addAction("Write &program memory", self.writeChipProgmem)
		a.setEnabled(bool(chipSupportFlags & Chip.SUPPORT_PROGMEMWRITE))
		a = menu.addAction("Write (E)EP&ROM", self.writeChipEeprom)
		a.setEnabled(bool(chipSupportFlags & Chip.SUPPORT_EEPROMWRITE))
		a = menu.addAction("Write &fuses", self.writeChipFuses)
		a.setEnabled(bool(chipSupportFlags & Chip.SUPPORT_FUSEWRITE))
		a = menu.addAction("Write &lock bits", self.writeChipLockbits)
		a.setEnabled(bool(chipSupportFlags & Chip.SUPPORT_LOCKWRITE))
		a = menu.addAction("Write R&AM", self.writeRam)
		a.setEnabled(bool(chipSupportFlags & Chip.SUPPORT_RAMWRITE))
		a = menu.addAction("Run &Unit-test", self.runTest)
		a.setEnabled(bool(chipSupportFlags & Chip.SUPPORT_TEST))
		a = menu.addAction("&Verify whole chip", self.verifyChip)
		a.setEnabled(chipSupportFlags != 0)

	def event(self, e):
		if e.type() == EVENT_HWTHREAD:
			self.hwThread.handleMessageQueue()
			e.accept()
			return True
		return QMainWindow.event(self, e)

	def closeEvent(self, e):
		if self.threadRunning:
			res = QMessageBox.critical(self, "Task running",
				"A hardware access task is running.\n\n"
				"'Cancel' the close request and continue, or\n"
				"'Abort' the task an quit the application?",
				QMessageBox.Cancel | QMessageBox.Abort,
				QMessageBox.Cancel)
			if res == QMessageBox.Abort:
				e.accept()
				# Force quit
				QApplication.exit(1)
				return
			e.ignore()
			return
		self.threadRunning = False
		self.hwThread.killThread()
		e.accept()

	def showAbout(self):
		QMessageBox.information(self, "About TOPrammer",
			"Copyright (c) Michael Buesch <m@bues.ch>")

	def startUnitest(self):
		self.bufferTab.setupBuffers(0)
		self.bufferTab.infoBuffer.clear()
		self.autorun.setup(0)

		self.guiDisable += 1
		self.console.blockStatusUpdate()
		try:
			dlg = UnitestDialog(self)
			dlg.exec_()
		except (TOPException), e:
			self.console.showMessage("Failed to start Unitest: %s\n" % str(e),
						 bold=True)
		self.console.unblockStatusUpdate()
		self.guiDisable -= 1
		self.guiUpdateEnable()
		self.runOperation(Operation(Operation.OP_SHUTDOWN,
					    HwThread.TASK_SHUTDOWN))

	def selectProgrammer(self):
		dlg = ProgrammerSelectDialog(self)
		if dlg.exec_() != QDialog.Accepted:
			return
		devIdentifier = dlg.getIdentifier()
		self.runOperationSync(HwThread.TASK_SHUTDOWN)
		self.hwThread.setDevice(devIdentifier)
		if self.currentChipDescription:
			self.runOperation(Operation(Operation.OP_INITCHIP,
						    HwThread.TASK_INITCHIP,
						    self.currentChipDescription.chipID))

	def sendRawCommand(self):
		(string, ok) = QInputDialog.getText(self,
			"Send raw command to programmer",
			"Enter raw command to send, in " +\
			"hex format (AABB1122...).\n" +\
			"WARNING: The programmer will malfunction on invalid commands.",
			QLineEdit.Normal,
			self.previousRawCommand)
		if not ok:
			return
		string = str(string).strip().upper()
		string = stringRemoveChars(string, " \t\r\n")
		if stringRemoveChars(string, "0123456789ABCDEF"):
			QMessageBox.critical(self, "Invalid characters",
				"Invalid characters in raw command string.\n" +\
				"Only hex characters 0-9,a-f allowed.")
			return
		if len(string) % 2 != 0 or len(string) // 2 > 64:
			QMessageBox.critical(self, "Invalid length",
				"Invalid command length. Length must be even " +\
				"and smaller or equal to 64 bytes.")
			return
		self.previousRawCommand = string
		command = hex2bin(string)
		if len(command) == 0:
			return
		self.runOperation(Operation(Operation.OP_RAWCOMMAND,
					    HwThread.TASK_GENERICTOPCALL,
					    GenericTopCall("top.hw.runCommandSync(...)", command)))

	def loadBuffer(self):
		bufWidget = self.bufferTab.getCurrentBuffer()
		data = None
		if not bufWidget:
			return
		if bufWidget.isReadOnly():
			QMessageBox.critical(self, "Buffer is read only",
				"Cannot load data into the %s buffer.\n"
				"The buffer is read-only." %\
				bufWidget.getName())
			return
		(fn, selectedFilter) = QFileDialog.getOpenFileName(self,
			"%s - open file" % bufWidget.getName(),
			"",
			"Autodetect file format (*);;"
			"Intel hex file (*.ihex *.hex);;"
			"Hex file with ASCII dump (*.ahex);;"
			"Binary file (*.bin)")
		if not fn:
			return
		extensions = str(selectedFilter).split("(")[1].\
				 split(")")[0].replace("*", "").strip().split()
		try:
			dataIn = open(fn, "rb").read()
		except (IOError), e:
			QMessageBox.critical(self, "Failed to read file",
				"Failed to read %s:\n%s" %\
				(str(fn), str(e.strerror)))
			return
		try:
			if ".bin" in extensions:
				handler = IO_binary()
			elif ".ahex" in extensions:
				handler = IO_ahex()
			elif ".ihex" in extensions:
				handler = IO_ihex()
			elif not extensions: # auto
				handler = IO_autodetect(dataIn)()
			else:
				assert(0)
			if isinstance(handler, IO_ihex):
				interp = self.chip.getIHexInterpreter()
				interp.interpret(dataIn)
				if interp.cumulativeSupported():
					res = QMessageBox.question(self,
						"Parse IHEX sections?",
						"This IHEX file might contain sections for "
						"the different memory areas (progmem, eeprom, etc...).\n"
						"\n"
						"Should the sections be interpreted?\n"
						"\n"
						"If 'Yes' is selected, only the section corresponding "
						"to the current buffer is extracted from the IHEX file.\n"
						"If 'No' is selected, the IHEX file will be read "
						"in raw mode and all of its data will be "
						"put into the current buffer.",
						QMessageBox.Yes | QMessageBox.No,
						QMessageBox.Yes)
					readRaw = (res != QMessageBox.Yes)
				else:
					readRaw = True
				ok = bufWidget.setDataWithIHexInterpreter(interp, readRaw)
			else:
				ok = bufWidget.setRawData(handler.toBinary(dataIn))
			if not ok:
				QMessageBox.critical(self, "Failed to load data",
					"Failed to load the file into the buffer")
		except (TOPException), e:
			QMessageBox.critical(self, "Failed to convert data",
				"Failed to convert the input file data to binary\n%s" % str(e))
			return

	def saveBuffer(self):
		bufWidget = self.bufferTab.getCurrentBuffer()
		if not bufWidget:
			return
		data = bufWidget.getRawData()
		if not data:
			return
		(fn, selectedFilter) = QFileDialog.getSaveFileName(self,
			"%s - save file" % bufWidget.getName(),
			"",
			"Intel hex file (*.ihex *.hex);;"
			"Hex file with ASCII dump (*.ahex);;"
			"Binary file (*)")
		if not fn:
			return
		extensions = str(selectedFilter).split("(")[1].\
				 split(")")[0].replace("*", "").strip().split()
		if not extensions:
			extensions = [ "" ]
		if not '.' in fn or\
		   not '.' + fn.split('.')[-1] in extensions:
			fn += extensions[0] # Default ext
		if ".ihex" in extensions:
			data = IO_ihex().fromBinary(data)
		elif ".ahex" in extensions:
			data = IO_ahex().fromBinary(data)
		elif not extensions[0]:
			data = IO_binary().fromBinary(data)
		else:
			assert(0)
		try:
			open(fn, "wb").write(data)
		except (IOError), e:
			QMessageBox.critical(self, "Failed to write file",
				"Failed to write %s:\n%s" %\
				(str(fn), str(e.strerror)))
			return

	def selectChip(self):
		dlg = ChipSelectDialog(self)
		if dlg.exec_() != QDialog.Accepted:
			return
		chipDescription = dlg.getSelectedChip()
		if not chipDescription:
			return
		self.currentChipDescription = chipDescription
		return self.runOperation(Operation(Operation.OP_INITCHIP,
						   HwThread.TASK_INITCHIP,
						   chipDescription.chipID))

	def __makeReadCallChain(self, mayReadSig=True, mayReadProgmem=True,
				mayReadEEPROM=True, mayReadFuse=True,
				mayReadLockbits=True, mayReadRAM=True):
		callChain = []
		suppFlags = self.chip.getSupportFlags()
		callChain.append(GenericTopCall("top.checkChip()",
						name = "check"))
		if mayReadSig and (suppFlags & Chip.SUPPORT_SIGREAD):
			callChain.append(GenericTopCall("top.readSignature()",
							name = "signature"))
		if mayReadProgmem and (suppFlags & Chip.SUPPORT_PROGMEMREAD):
			callChain.append(GenericTopCall("top.readProgmem()",
							name = "progmem"))
		if mayReadEEPROM and (suppFlags & Chip.SUPPORT_EEPROMREAD):
			callChain.append(GenericTopCall("top.readEEPROM()",
							name = "eeprom"))
		if mayReadFuse and (suppFlags & Chip.SUPPORT_FUSEREAD):
			callChain.append(GenericTopCall("top.readFuse()",
							name = "fusebits"))
		if mayReadLockbits and (suppFlags & Chip.SUPPORT_LOCKREAD):
			callChain.append(GenericTopCall("top.readLockbits()",
							name = "lockbits"))
		if mayReadRAM and (suppFlags & Chip.SUPPORT_RAMREAD):
			callChain.append(GenericTopCall("top.readRAM()",
							name = "ram"))
		return callChain

	def __readCallChain_GetResultImages(self, callChain):
		images = {}
		for topCall in (callChain if callChain else []):
			name = topCall.userData["name"]
			if name in ("signature", "progmem", "eeprom",
				    "fusebits", "lockbits", "ram"):
				images[name] = topCall.result
			elif name == "check":
				pass # Nothing to do
			else:
				assert(0)
		return images

	def readChip(self):
		return self.runOperation(Operation(Operation.OP_READALL,
						   HwThread.TASK_GENERICTOPCALL,
					 self.__makeReadCallChain()))

	def eraseChip(self):
		return self.runOperation(Operation(Operation.OP_ERASE,
						   HwThread.TASK_GENERICTOPCALL,
						   GenericTopCall("top.eraseChip()")))

	def writeChipProgmem(self):
		bufferWidget = self.bufferTab.progmemBuffer
		data = bufferWidget.getRawData()
		if not bufferWidget.isAvailable() or not data:
			QMessageBox.critical(self, "No program memory",
				"No program memory available")
			return False
		return self.runOperation(Operation(Operation.OP_WRITEPROG,
						   HwThread.TASK_GENERICTOPCALL,
						   GenericTopCall("top.writeProgmem(...)", data)))

	def writeChipEeprom(self):
		bufferWidget = self.bufferTab.eepromBuffer
		data = bufferWidget.getRawData()
		if not bufferWidget.isAvailable() or not data:
			QMessageBox.critical(self, "No (E)EPROM memory",
				"No (E)EPROM memory available")
			return False
		return self.runOperation(Operation(Operation.OP_WRITEEPROM,
						   HwThread.TASK_GENERICTOPCALL,
						   GenericTopCall("top.writeEEPROM(...)", data)))

	def writeChipFuses(self):
		bufferWidget = self.bufferTab.fuseBuffer
		data = bufferWidget.getRawData()
		if not bufferWidget.isAvailable() or not data:
			QMessageBox.critical(self, "No fuse bits",
				"No fuse bits available")
			return False
		return self.runOperation(Operation(Operation.OP_WRITEFUSE,
						   HwThread.TASK_GENERICTOPCALL,
						   GenericTopCall("top.writeFuse(...)", data)))

	def writeChipLockbits(self):
		bufferWidget = self.bufferTab.lockBuffer
		data = bufferWidget.getRawData()
		if not bufferWidget.isAvailable() or not data:
			QMessageBox.critical(self, "No lock bits",
				"No lock bits available")
			return False
		return self.runOperation(Operation(Operation.OP_WRITELOCK,
						   HwThread.TASK_GENERICTOPCALL,
						   GenericTopCall("top.writeLockbits(...)", data)))

	def writeRam(self):
		bufferWidget = self.bufferTab.ramBuffer
		data = bufferWidget.getRawData()
		if not bufferWidget.isAvailable() or not data:
			QMessageBox.critical(self, "No RAM memory",
				"No RAM memory available")
			return False
		return self.runOperation(Operation(Operation.OP_WRITERAM,
						   HwThread.TASK_GENERICTOPCALL,
						   GenericTopCall("top.writeRAM(...)", data)))

	def runTest(self):
		return self.runOperation(Operation(Operation.OP_TEST,
						   HwThread.TASK_GENERICTOPCALL,
						   GenericTopCall("top.testChip()")))

	def verifyChip(self):
		return self.verifySelectedMemories() # defaults to "all".

	def verifySelectedMemories(self, verifyProgmem=True,
				   verifyEEPROM=True,
				   verifyFuse=True,
				   verifyRAM=True):
		callChain = self.__makeReadCallChain(
			mayReadSig = False,
			mayReadProgmem = verifyProgmem,
			mayReadEEPROM = verifyEEPROM,
			mayReadFuse = verifyFuse,
			mayReadLockbits = False,
			mayReadRAM = verifyRAM)
		return self.runOperation(Operation(Operation.OP_VERIFY,
						   HwThread.TASK_GENERICTOPCALL,
					 callChain))

	def guiUpdateEnable(self):
		enable = not self.guiDisable and\
			 not self.threadRunning and\
			 not self.autorun.isRunning()
		self.menuBar().setEnabled(enable)
		self.topToolBar.setEnabled(enable)
		self.rightToolBar.setEnabled(enable)
		self.autorun.setEnabled(enable)
		self.bufferTab.setEnabled(enable)

	def cancelHardwareTask(self):
		if self.autorun.isRunning():
			self.autorun.abortRun()
		if self.threadRunning:
			self.hwThread.cancelTask()

	def __triggerOperation(self, op, threadMutexIsLocked=False):
		self.hwThread.triggerTask(op.hwTask, op.hwTaskParam,
					  id(op), threadMutexIsLocked)
		self.threadRunning = True
		self.runningOps[id(op)] = op
		self.console.setTaskRunning(True)
		self.guiUpdateEnable()

	def __triggerNextOperation(self, threadMutexIsLocked=False):
		assert(self.queuedOps)
		op = self.queuedOps.pop(0)
		self.__triggerOperation(op, threadMutexIsLocked)

	def runOperation(self, op):
		self.queuedOps.append(op)
		if not self.threadRunning:
			self.__triggerNextOperation()
		return True

	def runOperationSync(self, hwTask, taskParameter=None):
		op = Operation(Operation.OP_SYNCHRONOUS,
			       hwTask, taskParameter)
		self.runOperation(op)
		while not op.finished:
			QApplication.processEvents(QEventLoop.AllEvents, 50)
		self.runningOps.pop(id(op))
		return (op.failed, op.returnValue)

	def setOperationFinished(self, failed):
		self.console.setTaskRunning(running=False, success=not failed)
		if self.autorun.isRunning():
			if failed:
				QTimer.singleShot(0, self.autorun.abortRunWithMessage)
			else:
				QTimer.singleShot(0, self.autorun.runNextAction)

	def __hardwareTaskFinished(self, op):
		if op.op == Operation.OP_SYNCHRONOUS:
			self.console.setTaskRunning(running=False, success=True)
			return
		self.runningOps.pop(id(op))
		if op.failed:
			self.console.showMessage("[op %d task %d failed] %s\n" %\
					(op.op, op.hwTask, str(op.returnValue)),
					bold=True)
			self.setOperationFinished(failed=True)
			return
		# Task succeed
		if op.op == Operation.OP_INITCHIP:
			assert(op.hwTask == HwThread.TASK_INITCHIP)
			(self.chip, asciiArtLayout) = op.returnValue
			self.bufferTab.setupBuffers(self.chip.getSupportFlags())
			self.bufferTab.infoBuffer.clear()
			self.bufferTab.infoBuffer.setupDescription(self.currentChipDescription)
			self.bufferTab.infoBuffer.setChipLayout(asciiArtLayout)
			self.autorun.setup(self.chip.getSupportFlags())
			self.topToolBar.setup(self.chip.getSupportFlags())
			self.rightToolBar.setup(self.chip.getSupportFlags())
			self.setupRunMenu(self.chip.getSupportFlags())
		elif op.op == Operation.OP_SHUTDOWN:
			pass # Nothing to do
		elif op.op == Operation.OP_READALL:
			assert(op.hwTask == HwThread.TASK_GENERICTOPCALL)
			topCallList = op.returnValue
			images = self.__readCallChain_GetResultImages(topCallList)
			self.bufferTab.setupBuffers(self.chip.getSupportFlags())
			self.bufferTab.loadBuffers(images)
			try:
				self.bufferTab.infoBuffer.setChipSignature(images["signature"])
			except KeyError:
				pass
		elif op.op == Operation.OP_ERASE:
			pass # Nothing to do
		elif op.op == Operation.OP_WRITEPROG:
			pass # Nothing to do
		elif op.op == Operation.OP_WRITEEPROM:
			pass # Nothing to do
		elif op.op == Operation.OP_WRITEFUSE:
			pass # Nothing to do
		elif op.op == Operation.OP_WRITELOCK:
			pass # Nothing to do
		elif op.op == Operation.OP_WRITERAM:
			pass # Nothing to do
		elif op.op == Operation.OP_TEST:
			self.console.showMessage("Unit-test success. The chip seems to be OK.\n",
						 bold=True)
		elif op.op == Operation.OP_VERIFY:
			assert(op.hwTask == HwThread.TASK_GENERICTOPCALL)
			topCallList = op.returnValue
			images = self.__readCallChain_GetResultImages(topCallList)
			op.failed = not self.bufferTab.verifyBuffers(images)
		elif op.op == Operation.OP_RAWCOMMAND:
			self.console.showMessage("Successfully sent raw command\n", bold=True)
		else:
			print "ERROR: No handler for op %d task %d" % (op.op, op.hwTask)
		self.setOperationFinished(op.failed)

	def hardwareTaskFinished(self, opaqueId, failed, returnValue):
		if opaqueId is None:
			return
		op = self.runningOps[opaqueId]
		op.returnValue = returnValue
		op.failed = failed
		self.threadRunning = False
		self.__hardwareTaskFinished(op)
		op.op = Operation.OP_NONE
		op.finished = True
		if self.queuedOps:
			self.__triggerNextOperation(threadMutexIsLocked=True)
			return
		self.guiUpdateEnable()

def main():
	app = QApplication(sys.argv)
	mainwnd = MainWindow()
	mainwnd.show()
	mainwnd.resize(int(mainwnd.width() * 1.6),
		       int(mainwnd.height() * 1.2))
	return app.exec_()

if __name__ == "__main__":
	sys.exit(main())
