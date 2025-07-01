#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 22:46:21 2023

@author: Tim Gruene
"""
import os.path
from os.path import exists
import numpy as np

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import QTimer

import sys
import time

from DectrisDetectors_frontend import DetectorFrontend

from BrukerExpFile import ExpFile
from XDSparams import XDSparams


"""
A GUI to run the Dectris EIGER2 (API version 1.7.0) in connection with a
Bruker D8 (APEX3)
"""


class EigerGUI(QtWidgets.QMainWindow):
    def __init__(self, ip="131.130.170.233"):
        super(EigerGUI, self).__init__()

        # list of parameters used for workflow
        # self.outdir = os.path.join('D:', os.sep, 'frames', 'D8', 'screening')
        self.datadir = os.path.join(
            os.sep, "home", "tg", "univie", "instruments", "D8", "EIGER2", "data"
        )
        self.workdir = os.path.join(
            os.sep, "home", "tg", "univie", "instruments", "D8", "EIGER2"
        )
        self.timer = QTimer()
        self.xdstemplate = "/xtal/Integration/XDS/CCSA-templates/XDS-D8-Eiger2R500.INP"
        self.xdstemplate = "D:/frames/guest/XDS-D8-Eiger2R500.INP"
        self.xdsoffsets = "D:/frames/guest/XDS-D8-Eiger2R500_OFFSETS.INP"
        self.expfile = ""
        self.sampleID = "YourSampleID_no_Spaces"
        self.xID = 0
        self.armID = 0
        self.name_pattern = "myfile"
        self.twoTheta = -30.0
        self.Omega = 60.0
        self.Phi = 0.0
        self.Chi = -35.0
        self.D_mm = 34  # mm
        self.Axis = "OMEGA"
        self.source = "Cu"
        # parameters with reasonable defaults
        self.nimages = 1
        self.triggermode = "exts"
        self.nruns = 1
        self.ntriggers = 1
        # self.nshutter_buffer = 1
        self.nshutter_buffer = 2
        self.storage_mode = "per_dataset" # 'per_dataset','per_run', 'per_frame'

        self.nruns_widget = QtWidgets.QSpinBox(
            self, value=self.nruns, minimum=1, maximum=1000
        )
        self.ntriggers_widget = QtWidgets.QSpinBox(
            self, value=self.ntriggers, minimum=1, maximum=1000
        )

        self.apex_frame_time = 1.0
        self.napeximages = 1
        self.s_per_degree = 1
        self.scan_range = 5.0
        self.image_width = 0.5
        self.frame_time = self.apex_frame_time * self.image_width / self.scan_range
        print (f"frame_time: {self.frame_time}")

        # buttons that need to be disabled or enabled
        self.btn_arm = QtWidgets.QPushButton("Arm", self)
        self.btn_record = QtWidgets.QPushButton("Record", self)

        self.setGeometry(50, 50, 600, 500)
        self.setWindowTitle(f"EIGER2 R500 @ UniVie Bruker D8 {ip}")
        self.show()

        self.detector = DetectorFrontend(ip)
        self.detector.setup(frame_time=self.apex_frame_time, datadir=self.datadir)

        self.update_intervall = 1000 # millisecond
        self.timer.timeout.connect(self.update_state)
        self.timer.start(self.update_intervall)

        # generate the stem for output file and display filename
        self.updatefilename()
        self.setup()

    def setup(self):
        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.ui_DetectorInfo())

        layout.addWidget(self.ui_OutputData)
        layout.addWidget(self.ui_ScreenSample())
        layout.addWidget(self.ui_SetupDataCollection())
        layout.addWidget(self.control())

        main = QtWidgets.QWidget()
        main.setLayout(layout)
        self.setCentralWidget(main)

    def ui_DetectorInfo(self):
        "Show IP address of detector, status, etc"
        my = QtWidgets.QGroupBox("Detector Info")

        layout = QtWidgets.QHBoxLayout()

        layout.addWidget(QtWidgets.QLabel(text="IP:"))
        layout.addWidget(QtWidgets.QLabel(text=self.detector.detector.ip_))

        layout.addWidget(QtWidgets.QLabel(text="Status:"))
        self.det_state = QtWidgets.QLabel(
            text="idle"
        )  # self.detector.get_state('detector'))
        layout.addWidget(self.det_state)
        btn = QtWidgets.QPushButton(text="Update")
        btn.clicked.connect(self.update_state)
        layout.addWidget(btn)

        btn = QtWidgets.QPushButton(text="Initialize")
        btn.clicked.connect(lambda: self.detector.initialize())
        layout.addWidget(btn)

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addLayout(layout)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel(text=f"Update intervall for detector state: {0.001*self.update_intervall:.1f}s"))
        vlayout.addLayout(layout)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel(text="Select source:"))
        cb = QtWidgets.QComboBox()
        cb.addItems(["Mo", "Cu"])
        cb.setCurrentIndex(1)
        cb.currentIndexChanged.connect(self.new_source)
        layout.addWidget(cb)

        vlayout.addLayout(layout)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel(text="Trigger Mode:"))
        rb = QtWidgets.QRadioButton(text="INTS (manual trigger)")
        rb.clicked.connect(lambda: self.new_tmode("ints"))
        rb.setChecked(False)
        layout.addWidget(rb)
        rb = QtWidgets.QRadioButton(text="EXTS (trigger each run)")
        rb.clicked.connect(lambda: self.new_tmode("exts"))
        rb.setChecked(True)
        layout.addWidget(rb)
        "EXTE not yet implemented"
        #        rb = QtWidgets.QRadioButton(text="EXTE (trigger each frame)")
        #        rb.clicked.connect(lambda: self.new_tmode("exte"))
        #        layout.addWidget(rb)
        vlayout.addLayout(layout)
        self.new_tmode(self.triggermode)

        my.setLayout(vlayout)
        return my

    @property
    def ui_OutputData(self):
        "Setup directories for output data and working dir"
        my = QtWidgets.QGroupBox("Output Data")

        layout = QtWidgets.QGridLayout()

        layout.addWidget(QtWidgets.QLabel(text="Data Dir:"), 0, 0)
        self.le_datadir = QtWidgets.QLineEdit(text=self.datadir)
        layout.addWidget(self.le_datadir, 0, 1)
        pb = QtWidgets.QPushButton(text="Browse")
        pb.clicked.connect(self.new_datadir)
        layout.addWidget(pb, 0, 2)

        layout.addWidget(QtWidgets.QLabel(text="Working Dir:"), 1, 0)
        self.le_workdir = QtWidgets.QLineEdit(text=self.workdir)
        layout.addWidget(self.le_workdir, 1, 1)
        pb = QtWidgets.QPushButton(text="Browse")
        pb.clicked.connect(self.new_workdir)
        layout.addWidget(pb, 1, 2)

        layout.addWidget(QtWidgets.QLabel(text="Sample ID"), 2, 0)
        le = QtWidgets.QLineEdit(maxLength=100, text=self.sampleID)
        le.setValidator(
            QtGui.QRegularExpressionValidator(
                QtCore.QRegularExpression("[A-Za-z0-9-_:]{100}")
            )
        )
        le.textChanged.connect(self.new_sampleId)
        layout.addWidget(le, 2, 1)

        layout.addWidget(QtWidgets.QLabel("$id", self), 2, 2)
        self.lbl_armID = QtWidgets.QLabel("0")
        layout.addWidget(self.lbl_armID, 2, 3)
        pb = QtWidgets.QPushButton("Update $id", self)
        pb.clicked.connect(self.updateId)
        layout.addWidget(pb, 2, 4)

        pb = QtWidgets.QPushButton(text="list files")
        pb.clicked.connect(self.file_list)
        layout.addWidget(pb, 3, 0)

        pb = QtWidgets.QPushButton(text="Download")
        pb.clicked.connect(self.download)
        layout.addWidget(pb, 3, 1)

        pb = QtWidgets.QPushButton(text="Clear DCU files")
        pb.clicked.connect(self.clearfiles)
        layout.addWidget(pb, 3, 2)

        my.setLayout(layout)
        return my

    @QtCore.pyqtSlot()
    def process_exp(self):
        "if exp-file exists, process it"
        if not exists(self.expfile):
            pass
        self.experiment = ExpFile(self.expfile)
        self.experiment.extract()
        self.nruns = len(self.experiment.runs)
        self.nruns_widget.setValue(self.nruns)

        # should be automated: shutterless of shuttered mode?
        # self.ntriggers = self.experiment.total_images
        self.ntriggers = self.nruns
        self.ntriggers_widget.setValue(self.ntriggers)
        self.new_tmode("exts")
        for idx, run in enumerate(self.experiment.runs):
            sweep = run["end"] - run["start"]
            self.new_scan_range(np.abs(sweep) * 180.0 / np.pi)
            # in case nruns is subdivided into ntriggers, less images between triggers
            self.nimages = 180. / np.pi * np.abs(sweep) / self.image_width
            self.nimages = round(self.nimages * self.nruns / self.ntriggers)
            # round and add one image as buffer, because Photon-100 is too slow for EIGER
            self.nimages = round(self.nimages) + self.nshutter_buffer
            if "frametime" in run and "frameangle" in run:
                # 1st: time per degree
                self.frame_time = np.pi / 180. * run["frametime"] / run["frameangle"]
                # 2nd: time per EIGER frame
                self.frame_time = self.frame_time * self.image_width
                self.napeximages = round(sweep / run["frameangle"])
                print(f'Calculated frametime as {self.frame_time} with per frame and {self.image_width} deg/frame')
                self.lbl_frame_time.setText(f"{self.frame_time:.2f}")
            else:
                print("Cannot determine frame time from EXP file. Use Screening time")
                print("This will most likely lead to a mismatch between XDS.INP and data range")
            print(f"Updating Scan range to {np.abs(sweep)*180. / np.pi:.2} and nimages to {self.nimages}")


    """
    Steps for setting up XDS
    for each run:
     create dir ID-nn
     create XDS.INP
      - update template (based on wavelength?)
      - set geometry
      - set up data_range (DATA_RANGE = (id-1)*nimages+1 id*nimages
      - write XDS.INP
    """

    @QtCore.pyqtSlot()
    def setup_xds(self):
        """updates XDS paramters and creates run directories"""
        if self.detector.get_state("detector") not in ["ready", "acquire"]:
            print("Detector not armed and not acquiring")
            msg = QtWidgets.QMessageBox()
            msg.setText("To ensure consistent filenames, Detector must be armed first")
            msg.exec()
            return

        """ name pattern contains literal $id, and does not end in _master.h5 """
        name_template = self.detector.get_name_pattern()
        print(f"name template from detector reads {name_template}")
        name_template = name_template.replace("$id", str(self.armID))
        print(f"name template with ID reads {name_template}")
        name_template = name_template + "_??????.h5"

        print(f"name template with suffix reads {name_template}")
        for idx, run in enumerate(self.experiment.runs):
            rundir = self.workdir + os.path.sep + f"run{idx+1:02d}"
            # data_range = f"{1+idx*self.napeximages*self.nimages} {(idx+1) * self.napeximages * self.nimages}"
            data_range = f"{1+idx*self.nimages} {(idx+1) * self.nimages - self.nshutter_buffer}"
            xds = XDSparams(name_template, data_range)
            rt_Dectris = self.apex_frame_time * self.nimages
            sweep = run["end"] - run["start"]
            dir = np.sign(sweep)
            xds.settings(
                self.image_width,
                self.experiment.wavelength,
                run["theta"],
                run["angle"],
                run["omega"],
                run["chi"],
                run["distance"],
                dir,
                run["start"],
                self.xdsoffsets
            )
            xds.update(self.xdstemplate)

            """ 
            In true shutterless mode, this should not be necessary.
            Unsure, when the shutter is used
            for i in range(1, self.napeximages+1):
                exclude_data = idx*self.napeximages*self.nimages + i*self.nimages
                xds.exclude_data(f'{exclude_data} {exclude_data}')
            """
            xds.xdswrite(rundir)

    """ 
    Settings for screening
    """
    def ui_ScreenSample(self):
        my = QtWidgets.QGroupBox("Screen Sample")
        self.lbl_frame_time = QtWidgets.QLabel(text=f"{self.frame_time:.2f}")

        layout = QtWidgets.QGridLayout()

        layout.addWidget(QtWidgets.QLabel(text="Scan Range: (APEX)"), 0, 0)
        sb = QtWidgets.QDoubleSpinBox(
            self, value=self.scan_range, minimum=0.1, maximum=360
        )
        sb.valueChanged.connect(self.new_scan_range)
        layout.addWidget(sb, 0, 1)
        layout.addWidget(QtWidgets.QLabel(text=" =Image Width (APEX)"), 0, 2)

        layout.addWidget(QtWidgets.QLabel(text="Exposure time: (APEX)"), 1, 0)
        sb = QtWidgets.QDoubleSpinBox(
            self, value=self.apex_frame_time, minimum=0.025, maximum=360000
        )
        sb.valueChanged.connect(self.new_apex_frame_time)
        layout.addWidget(sb, 1, 1)

        qc = QtWidgets.QComboBox()
        qc.addItems(["s/°", "s/image"])
        qc.currentIndexChanged.connect(self.new_exposure_unit)
        qc.setCurrentIndex(self.s_per_degree)
        layout.addWidget(qc, 1, 2)

        layout.addWidget(QtWidgets.QLabel(text="Image Width: (Actual)"), 2, 0)
        sb = QtWidgets.QDoubleSpinBox(
            self, value=self.image_width, minimum=0.1, maximum=2
        )
        sb.valueChanged.connect(self.new_image_width)
        layout.addWidget(sb, 2, 1)

        """
        layout.addWidget(QtWidgets.QLabel(text="Exposure time: (Actual)"), 2, 0)
        sb = QtWidgets.QDoubleSpinBox(
            self, value=self.frame_time, minimum=0.025, maximum=360000
        )
        sb.valueChanged.connect(self.new_frame_time)
        layout.addWidget(sb, 2, 1)
        """

        layout.addWidget(QtWidgets.QLabel(text="Exposure time: (Actual):"), 3, 0)
        self.frame_time = self.image_width / self.scan_range * self.apex_frame_time

        layout.addWidget(self.lbl_frame_time, 3, 1)

        layout.addWidget(QtWidgets.QLabel(text="nimages: (actual):"), 3, 2)
        self.nimages = int(self.scan_range / self.image_width)
        self.lbl_nimages = QtWidgets.QLabel(text=f"{self.nimages}")
        layout.addWidget(self.lbl_nimages, 3, 3)

        qb = QtWidgets.QPushButton("Arm (Screen)")
        qb.clicked.connect(self.arm_screen)
        layout.addWidget(qb, 4,0)

        my.setLayout(layout)
        return my

    def ui_SetupDataCollection(self):
        """Setup actual measurement, ideally through Bruker EXP file"""
        my = QtWidgets.QGroupBox("Setup Data Collection")

        layout = QtWidgets.QGridLayout()

        layout.addWidget(QtWidgets.QLabel(text="Bruker EXP file:"), 0, 0)
        self.le_expfile = QtWidgets.QLineEdit(text=self.expfile)
        layout.addWidget(self.le_expfile, 0, 1)
        pb = QtWidgets.QPushButton(text="Browse")
        pb.clicked.connect(self.new_expfile)
        layout.addWidget(pb, 0, 2)

        layout.addWidget(QtWidgets.QLabel(text="XDS.INP Template:"), 1, 0)
        self.le_xdstemplate = QtWidgets.QLineEdit(text=self.xdstemplate)
        layout.addWidget(self.le_xdstemplate, 1, 1)
        pb = QtWidgets.QPushButton(text="Browse")
        pb.clicked.connect(self.new_xdstemplate)
        layout.addWidget(pb, 1, 2)

        layout.addWidget(QtWidgets.QLabel(text="XDS.INP OFFSETS:"), 2, 0)
        self.le_xdsoffsets = QtWidgets.QLineEdit(text=self.xdsoffsets)
        layout.addWidget(self.le_xdsoffsets, 2, 1)
        pb = QtWidgets.QPushButton(text="Browse")
        pb.clicked.connect(self.new_xdsoffsets)
        layout.addWidget(pb, 2, 2)

        layout.addWidget(QtWidgets.QLabel(text="# runs:"), 3, 0)
        self.nruns_widget.valueChanged.connect(self.new_nruns)
        layout.addWidget(self.nruns_widget, 3, 1)

        layout.addWidget(QtWidgets.QLabel(text="# ntrigger:"), 3, 2)
        self.ntriggers_widget.valueChanged.connect(self.new_ntriggers)
        if self.triggermode == "exts":
            self.ntriggers_widget.setEnabled(1)
        layout.addWidget(self.ntriggers_widget, 3, 3)

        lt = QtWidgets.QHBoxLayout()

        layout.addWidget(QtWidgets.QLabel(text="Output files:"), 4, 0)
        rb = QtWidgets.QRadioButton("1 file / frame")
        rb.clicked.connect(lambda: self.new_nimages_per_file("per_frame"))
        rb.setChecked(False)
        lt.addWidget(rb)

        rb = QtWidgets.QRadioButton("1 file / run")
        rb.clicked.connect(lambda: self.new_nimages_per_file("per_run"))
        rb.setChecked(False)
        lt.addWidget(rb)

        rb = QtWidgets.QRadioButton("all in one")
        rb.clicked.connect(lambda: self.new_nimages_per_file("per_dataset"))
        rb.setChecked(True)
        lt.addWidget(rb)

        layout.addLayout(lt, 4,1)

        pb = QtWidgets.QPushButton(text="Process EXP")
        pb.clicked.connect(self.process_exp)
        layout.addWidget(pb, 5, 0)

        my.setLayout(layout)
        return my

    def control(self):
        """control buttons at bottom of GUI"""
        my = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()

        self.btn_arm.clicked.connect(self.arm_expfile)
        layout.addWidget(self.btn_arm)

        self.btn_record.clicked.connect(self.record)
        layout.addWidget(self.btn_record)

        btn = QtWidgets.QPushButton("Stop", self)
        btn.clicked.connect(self.stop)
        layout.addWidget(btn)

        btn = QtWidgets.QPushButton("Quit", self)
        btn.clicked.connect(self.quitgui)
        layout.addWidget(btn)

        my.setLayout(layout)
        return my
    @QtCore.pyqtSlot()
    def arm_screen(self):
        """Prepares the recording of data"""
        s = self.update_state()
        if s == "ready":
            self.detector.stop()
        self.updatefilename()
        self.updateId()
        # screening always should only have one trigger
        self.detector.triggermode(self.triggermode, 1)
        self.detector.set_frame_time(self.frame_time)
        self.detector.set_name_pattern(self.name_pattern)
        self.nimages = int(self.scan_range / self.image_width)
        self.detector.set_nimages(self.nimages)
        self.detector.detector.set_config("mode", "enabled", "filewriter")
        self.detector.arm()
        self.update_state()
        self.updateId()

    @QtCore.pyqtSlot()
    def arm_expfile(self):
        """Prepares the recording of data"""
        s = self.update_state()
        if s == "ready":
            self.detector.stop()
        self.updatefilename()
        print(f"Setting up data collection with {self.ntriggers} triggers, {self.frame_time}s frame time, and {self.nimages} images per trigger")
        self.detector.triggermode(self.triggermode, self.ntriggers)
        self.detector.set_frame_time(self.frame_time)
        self.detector.set_name_pattern(self.name_pattern)
        self.detector.set_nimages(self.nimages)
        self.detector.detector.set_config("mode", "enabled", "filewriter")
        """ determine number of images per file """
        self.detector.set_nimages_per_file(self.nimages * self.ntriggers)
        if self.storage_mode == 'per_run':
            self.detector.set_nimages_per_file(self.nimages)
        elif self.storage_mode == 'per_frame':
            self.detector.set_nimages_per_file(1)
        self.detector.arm()
        self.update_state()
        self.updateId()
        # probably a try block reasonable in case user forgot to provide some information
        if self.expfile is not None and os.path.exists(self.expfile):
            self.setup_xds()

    @QtCore.pyqtSlot()
    def record(self):
        "Starts the recording of data"
        s = self.update_state()
        if s == "ready":
            self.detector.record()
        else:
            print("Error: detector needs to be armed first")
        self.xdsparams()
        self.update_state()

    @QtCore.pyqtSlot()
    def stop(self):
        "Stops recording, stops rotations"
        self.detector.stop()
        self.updateId()
        self.update_state()
        print("Detector disarmed")

    @QtCore.pyqtSlot()
    def quitgui(self):
        "Stop the detector, then quit GUI"
        # self.detector.stop()
        QtCore.QCoreApplication.instance().quit()

    """
    generates the filename for data recording. Contains the timestamp.
    Therefore, this function should be called by the record button
    before starting data recording
    """

    @QtCore.pyqtSlot()
    def updatefilename(self):
        "generate the filename string displayed in GUI"
        now = time.strftime("_%Y-%m-%d_%H%M%S")
        self.name_pattern = self.sampleID + "_ID-$id" + now

    """
    The following functions receive data from the GUI elements
    """

    @QtCore.pyqtSlot()
    def new_datadir(self):
        dd = QtWidgets.QFileDialog.getExistingDirectory(
            directory=self.datadir, caption="Choose Directory"
        )
        self.datadir = dd
        self.le_datadir.setText(dd)

    @QtCore.pyqtSlot()
    def new_expfile(self):
        "Browse for Bruker Apex EXP file to setup up runs"
        xf = QtWidgets.QFileDialog.getOpenFileName(
            caption="Choose EXP file",
            filter="*.exp",
            directory="/home/tg/univie/instruments/D8/EIGER2/data/CCSA/calibration",
        )
        if xf[0]:
            self.expfile = xf[0]
            self.le_expfile.setText(self.expfile)

    @QtCore.pyqtSlot()
    def new_workdir(self):
        dd = QtWidgets.QFileDialog.getExistingDirectory(
            directory=self.workdir, caption="Choose Directory"
        )
        self.workdir = dd
        self.le_workdir.setText(dd)

    @QtCore.pyqtSlot(str)
    def new_sampleId(self, text):
        self.sampleID = text
        self.updatefilename()

    @QtCore.pyqtSlot(int)
    def new_xID(self, value):
        self.xID = value
        self.updatefilename()

    @QtCore.pyqtSlot()
    def new_xdstemplate(self):
        "Browse for XDS.INP as template file"
        xf = QtWidgets.QFileDialog.getOpenFileName(
            caption="Choose XDS.INP Template",
            filter="*.INP",
            directory="/xtal/Integration/XDS/CCSA-templates",
        )
        if xf[0]:
            self.xdstemplate = xf[0]
            self.le_xdstemplate.setText(self.xdstemplate)

    @QtCore.pyqtSlot()
    def new_xdsoffsets(self):
        "Browse for OFFSETS file for XDS.INP"
        xf = QtWidgets.QFileDialog.getOpenFileName(
            caption="Choose XDS_OFFSETS.INP Template",
            filter="*.INP",
            directory="/xtal/Integration/XDS/CCSA-templates",
        )
        if xf[0]:
            self.xdsoffsets = xf[0]
            self.le_xdsoffsets.setText(self.xdsoffsets)

    QtCore.pyqtSlot(str)
    def new_axis(self, value):
        self.Axis = value

    @QtCore.pyqtSlot()
    def updateId(self):
        "retrieve the current ID from Detector"
        self.armID = self.detector.armID
        self.lbl_armID.setText(str(self.armID))
        self.updatefilename()

    @QtCore.pyqtSlot("double")
    def new_apex_frame_time(self, value):
        self.apex_frame_time = value
        if self.s_per_degree == 1:
            self.frame_time = value * self.image_width
        else:
            self.frame_time = self.apex_frame_time * self.image_width / self.scan_range
        self.lbl_frame_time.setText(f"{self.frame_time:.2f}")

    @QtCore.pyqtSlot("int")
    def new_exposure_unit(self, value):
        if value == 0:
            self.s_per_degree = 1
        else:
            self.s_per_degree = 0
        # update display
        self.new_apex_frame_time(self.apex_frame_time)

    @QtCore.pyqtSlot("double")
    def new_scan_range(self, value):
        self.scan_range = value
        nimages = int(self.scan_range / self.image_width)
        self.frame_time = self.image_width / self.scan_range * self.apex_frame_time
        self.lbl_nimages.setText(f"{nimages}")
        self.lbl_frame_time.setText(f"{self.frame_time:.2f}")

    @QtCore.pyqtSlot("double")
    def new_image_width(self, value):
        self.image_width = value
        nimages = int(self.scan_range / self.image_width)
        self.frame_time = self.apex_frame_time / nimages
        self.lbl_nimages.setText(f"{nimages}")
        self.lbl_frame_time.setText(f"{self.frame_time:.2f}")

    @QtCore.pyqtSlot("double")
    def new_phidot(self, rate=2.0):
        self.phidot = rate
        print("New rate: {}".format(self.phidot))

    @QtCore.pyqtSlot("double")
    def new_distance(self, value):
        self.D_mm = value

    @QtCore.pyqtSlot()
    def new_tmode(self, value):
        self.triggermode = value
        if value == "exts":
            self.ntriggers_widget.setEnabled(1)
            self.btn_record.setEnabled(0)
        else:
            self.ntriggers_widget.setEnabled(0)
            self.btn_record.setEnabled(1)
    @QtCore.pyqtSlot()
    def new_nimages_per_file(self, value):
        if value != 'per_dataset' and value != 'per_run' and value != 'per_frame':
            print(f" programming Error: value {value} for storage mode unknown")
            raise Exception(f"Unknown storage mode for H5 file: {value}")
        self.storage_mode = value
        print(f"Debug: Setting nimages per file to {value}")

    @QtCore.pyqtSlot("double")
    def new_twotheta(self, value):
        self.twoTheta = value

    @QtCore.pyqtSlot("int")
    def new_nruns(self, value):
        self.nruns = value

    @QtCore.pyqtSlot("int")
    def new_ntriggers(self, value):
        self.ntriggers = value

    @QtCore.pyqtSlot("double")
    def new_omega(self, value):
        self.Omega = value

    @QtCore.pyqtSlot("double")
    def new_phi(self, value):
        self.Phi = value

    @QtCore.pyqtSlot("double")
    def new_chi(self, value):
        self.Chi = value

    @QtCore.pyqtSlot()
    def update_state(self):
        res = self.detector.get_state("detector")
        self.det_state.setText(res)
        return res

    @QtCore.pyqtSlot("int")
    def new_source(self, idx):
        sources = ["Mo", "Cu"]
        self.source = sources[idx]
        self.detector.set_element(self.source)

    @QtCore.pyqtSlot()
    def file_list(self):
        flist = self.detector.filelist()
        print(f"Number of files on DCU: {len(flist)}")
        for f in flist:
            print(f"{f}")

    @QtCore.pyqtSlot()
    def download(self):
        flist = self.detector.filelist()
        for f in flist:
            self.detector.save_file(f, self.datadir)

    @QtCore.pyqtSlot()
    def clearfiles(self):
        print("Deleting files on DCU")
        self.detector.clear_files()

    def xdsparams(self):
        # make sure ID is up to date
        self.updateId()
        fname = f"PARAMS_{self.sampleID}_ID{str(self.armID)}.INP"
        fname = os.path.join(self.datadir, fname)
        nimg = int(self.scan_range / self.image_width)
        if self.source == "Cu":
            wavelength = 1.54184  # from APEX server listing
        else:
            wavelength = 0.70931

        name_pattern = self.detector.get_name_pattern()
        name_pattern = name_pattern.replace("$id", str(self.armID))

        with open(fname, "w") as f:
            f.write(f"DETECTOR_DISTANCE= {self.D_mm}\n")
            f.write(f"2THETA= {self.twoTheta}\n")
            f.write(f"OMEGA= {self.Omega}\n")
            f.write(f"PHI= {self.Phi}\n")
            f.write(f"CHI= {self.Chi}\n")
            f.write(f"AXIS= {self.Axis}\n")
            f.write(f"NIMAGES= {nimg}\n")
            f.write(f"SWEEP= {str(self.scan_range)}\n")
            f.write(f"DATA_RANGE= 2 {str(nimg-1)}\n")
            f.write(f"X-RAY_WAVELENGTH= {wavelength:.5f}\n")
            f.write(f"NAME_TEMPLATE_OF_DATA_FRAMES= {name_pattern}_??????.h5\n")
        print(f"Parameters for sfrmtools written to {fname}\n")


if __name__ == "__main__":
    print("Starting main")
    app = QtWidgets.QApplication(sys.argv)
    eigerGui = EigerGUI()
    app.exec()
