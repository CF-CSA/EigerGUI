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

import sys
import time

from DectrisDetectors_frontend import DetectorFrontend

from BrukerExpFile import ExpFile
from XDSparams import XDSparams


class EigerGUI(QtWidgets.QMainWindow):
    "A simple GUI to run the Dectris SINGLA"

    def __init__(self, ip="131.130.27.207"):
        super(EigerGUI, self).__init__()

        # list of parameters used for workflow
        # self.outdir = os.path.join('D:', os.sep, 'frames', 'D8', 'screening')
        self.datadir = os.path.join(
            os.sep, "home", "tg", "univie", "instruments", "D8", "EIGER2", "data"
        )
        self.workdir = os.path.join(
            os.sep, "home", "tg", "univie", "instruments", "D8", "EIGER2"
        )
        self.xdstemplate = "/xtal/Integration/XDS/CCSA-templates/XDS-D8-Eiger2R500.INP"
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
        self.frame_time = 1.0  # seconds
        self.s_per_degree = 1
        self.nimages = 0
        self.triggermode = "exts"
        self.ntriggers = 1
        self.ntriggers_widget = QtWidgets.QSpinBox(self, value=self.ntriggers, minimum=1)
        #

        # buttons that need to be disabled or enabled
        self.btn_arm = QtWidgets.QPushButton("Arm", self)
        self.btn_record = QtWidgets.QPushButton("Record", self)

        self.setGeometry(50, 50, 600, 500)
        self.setWindowTitle(f"EIGER2 R500 @ UniVie Bruker D8 {ip}")
        self.show()

        self.detector = DetectorFrontend(ip)
        self.frame_time = 1.0
        self.scan_range = 5.0
        self.image_width = 0.5
        self.detector.setup(frame_time=self.frame_time, datadir=self.datadir)

        # generate the stem for output file and display filename
        self.updatefilename()
        self.setup()

    def setup(self):
        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.detector_info())

        layout.addWidget(self.outputfiles())
        layout.addWidget(self.screening())
        layout.addWidget(self.setupDataCollection())
        #exp_geometry is for manual triggering, not used anymore
        # layout.addWidget(self.exp_geometry())
        layout.addWidget(self.control())

        main = QtWidgets.QWidget()
        main.setLayout(layout)
        self.setCentralWidget(main)

    def detector_info(self):
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

    def outputfiles(self):
        "Setup directories for output data and working dir"
        my = QtWidgets.QGroupBox("Output data")

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
        le = QtWidgets.QLineEdit(maxLength=100)
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
        self.experiment.extract()
        self.ntriggers = len(self.experiment.runs)
        self.ntriggers_widget.setValue(self.ntriggers)
        self.new_tmode("exts")

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
        """ updates XDS paramters and creates run directories """
        if self.detector.get_state("detector") not in [ "ready", "acquire"]:
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
            rundir = self.workdir+os.path.sep+f"run{idx+1:02d}"
            data_range = f"{1+idx*self.nimages} {(idx+1)*self.nimages}"
            xds=XDSparams(name_template, data_range)
            sweep = run['end'] - run['start']
            self.new_scan_range(np.abs(sweep)*180. / np.pi)
            # nimages = np.abs(sweep)*180. / np.pi / self.de
            print(f"Updateing Scan range to {np.abs(sweep)*180. / np.pi}")
            if "runtime" in run:
                "Check consistency between EXP-file and GUI"
                """ runtime means frametime and frameangle are present. Together
		with sweep, exposure time can be calculated from image width self.image_width
		"""
                rt_Dectris = self.frame_time*self.nimages
                if abs(rt_Dectris - run["runtime"]) > 0.001:
                    print(f"TODO: update GUI instead of breaking the program")
                    raise ValueError("Inconsistency between EXP and GUI frame time")
            dir = np.sign(sweep)
            xds.settings(self.image_width, self.experiment.wavelength, run['theta'], run['angle'], run['omega'], run['chi'], dir, run['start'])
            xds.update(self.xdstemplate)
            xds.xdswrite(rundir)


    """
    Geometry settings, need to be copied from APEX3Server
    """

    def exp_geometry(self):
        "Setup measurement"
        my = QtWidgets.QGroupBox(
            "Experimental Geometry (update manually from APEX Server"
        )

        layout = QtWidgets.QGridLayout()

        layout.addWidget(QtWidgets.QLabel(text="Distance:"), 0, 0)
        db = QtWidgets.QDoubleSpinBox(self, value=self.D_mm, minimum=33.6, maximum=247)
        db.setSuffix(" mm")
        db.valueChanged.connect(self.new_distance)
        layout.addWidget(db, 0, 1)

        layout.addWidget(QtWidgets.QLabel(text="2Theta:"), 0, 2)
        db = QtWidgets.QDoubleSpinBox(
            self, value=self.twoTheta, minimum=-180, maximum=180
        )
        db.setSuffix("°")
        db.valueChanged.connect(self.new_twotheta)
        layout.addWidget(db, 0, 3)

        layout.addWidget(QtWidgets.QLabel(text="Omega"), 0, 4)
        db = QtWidgets.QDoubleSpinBox(self, value=self.Omega, minimum=-180, maximum=180)
        db.setSuffix("°")
        db.valueChanged.connect(self.new_omega)
        layout.addWidget(db, 0, 5)

        layout.addWidget(QtWidgets.QLabel(text="Phi"))
        db = QtWidgets.QDoubleSpinBox(
            self, value=self.Phi, minimum=-180.0, maximum=360.0
        )
        db.setSuffix("°")
        db.valueChanged.connect(self.new_phi)
        layout.addWidget(db)

        layout.addWidget(QtWidgets.QLabel(text="Chi"))
        db = QtWidgets.QDoubleSpinBox(self, value=self.Chi, minimum=-99.0, maximum=99.0)
        db.setSuffix("°")
        db.valueChanged.connect(self.new_chi)
        layout.addWidget(db)

        layout.addWidget(QtWidgets.QLabel(text="Rotation Axis:"), 2, 0)
        rb = QtWidgets.QRadioButton(text="Omega")
        rb.clicked.connect(lambda: self.new_axis("OMEGA"))
        rb.setChecked(True)
        layout.addWidget(rb, 2, 1)
        rb = QtWidgets.QRadioButton(text="Phi")
        rb.clicked.connect(lambda: self.new_axis("PHI"))
        layout.addWidget(rb, 2, 2)
        self.new_axis(self.Axis)

        my.setLayout(layout)
        return my

    """ 
    Settings for screening
    """

    def screening(self):
        my = QtWidgets.QGroupBox("Screen Sample")
        layout = QtWidgets.QGridLayout()

        layout.addWidget(QtWidgets.QLabel(text="Scan Range: (APEX)"), 0, 0)
        sb = QtWidgets.QDoubleSpinBox(
            self, value=self.scan_range, minimum=0.1, maximum=360
        )
        sb.valueChanged.connect(self.new_scan_range)
        layout.addWidget(sb, 0, 1)

        layout.addWidget(QtWidgets.QLabel(text="Image Width: (Actual)"), 1, 0)
        sb = QtWidgets.QDoubleSpinBox(
            self, value=self.image_width, minimum=0.1, maximum=2
        )
        sb.valueChanged.connect(self.new_image_width)
        layout.addWidget(sb, 1, 1)

        layout.addWidget(QtWidgets.QLabel(text="Exposure time: (Actual)"), 2, 0)
        sb = QtWidgets.QDoubleSpinBox(
            self, value=self.frame_time, minimum=0.025, maximum=360000
        )
        sb.valueChanged.connect(self.new_frame_time)
        layout.addWidget(sb, 2, 1)

        qc = QtWidgets.QComboBox()
        qc.addItems(["s/°", "s/image"])
        qc.currentIndexChanged.connect(self.new_exposure_unit)
        qc.setCurrentIndex(self.s_per_degree)
        layout.addWidget(qc, 2, 2)

        layout.addWidget(QtWidgets.QLabel(text="Exposure time: (APEX):"), 3, 0)
        apex_time = self.scan_range / self.image_width * self.frame_time
        self.lbl_apex_time = QtWidgets.QLabel(text=f"{apex_time:.2f}")
        layout.addWidget(self.lbl_apex_time, 3, 1)

        layout.addWidget(QtWidgets.QLabel(text="nimages: (actual):"), 3, 2)
        self.nimages = int(self.scan_range / self.image_width)
        self.lbl_nimages = QtWidgets.QLabel(text=f"{self.nimages}")
        layout.addWidget(self.lbl_nimages, 3, 3)

        my.setLayout(layout)
        return my

    def setupDataCollection(self):
        """Setup actual measurement, ideally through Bruker EXP file"""
        my = QtWidgets.QGroupBox("Setup data Collection")

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

        layout.addWidget(QtWidgets.QLabel(text="# runs (ntrigger):"), 2, 0)
        self.ntriggers_widget.valueChanged.connect(self.new_ntriggers)
        if self.triggermode == "exts":
            self.ntriggers_widget.setEnabled(1)
        layout.addWidget(self.ntriggers_widget, 2, 1)

        pb = QtWidgets.QPushButton(text="Process EXP")
        pb.clicked.connect(self.process_exp)
        layout.addWidget(pb, 3, 0)

        pb = QtWidgets.QPushButton(text="Setup XDS")
        pb.clicked.connect(self.setup_xds)
        layout.addWidget(pb, 3, 1)

        my.setLayout(layout)
        return my

    def control(self):
        """control buttons at bottom of GUI"""
        my = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()

        self.btn_arm.clicked.connect(self.arm)
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
    def arm(self):
        """Prepares the recording of data"""
        s = self.update_state()
        if s == "ready":
            self.detector.stop()
        self.updatefilename()
        self.updateId()
        self.detector.triggermode(self.triggermode, self.ntriggers)
        self.detector.set_frame_time(self.frame_time)
        self.detector.set_name_pattern(self.name_pattern)
        self.nimages = int(self.scan_range / self.image_width)
        self.detector.set_nimages(self.nimages)
        self.detector.detector.set_config("mode", "enabled", "filewriter")
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
        self.detector.stop()
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
            self.experiment = ExpFile(self.expfile)

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
        "Browse for Bruker Apex EXP file to setup up runs"
        xf = QtWidgets.QFileDialog.getOpenFileName(
            caption="Choose XDS.INP Template",
            filter="*.INP",
            directory="/xtal/Integration/XDS/CCSA-templates",
        )
        if xf[0]:
            self.xdstemplate = xf[0]
            self.le_xdstemplate.setText(self.xdstemplate)

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
    def new_frame_time(self, value):
        self.frame_time = value
        nimages = int(self.scan_range / self.image_width)
        apex_time = nimages * self.frame_time
        self.lbl_nimages.setText(f"{nimages}")
        self.lbl_apex_time.setText(f"{apex_time:.2f}")

    @QtCore.pyqtSlot("int")
    def new_exposure_unit(self, value):
        if value == 0:
            self.s_per_degree = 1
        else:
            self.s_per_degree = 0

    @QtCore.pyqtSlot("double")
    def new_scan_range(self, value):
        self.scan_range = value
        nimages = int(self.scan_range / self.image_width)
        apex_time = nimages * self.frame_time
        self.lbl_nimages.setText(f"{nimages}")
        self.lbl_apex_time.setText(f"{apex_time:.2f}")

    @QtCore.pyqtSlot("double")
    def new_image_width(self, value):
        self.image_width = value
        nimages = int(self.scan_range / self.image_width)
        apex_time = nimages * self.frame_time
        self.lbl_nimages.setText(f"{nimages}")
        self.lbl_apex_time.setText(f"{apex_time:.2f}")

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

    @QtCore.pyqtSlot("double")
    def new_twotheta(self, value):
        self.twoTheta = value

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
