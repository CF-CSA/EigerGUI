#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 17:21:54 2022

@author: quadro
"""
from requests import get
from os.path import join, exists

import multiprocessing as mp

from DectrisDetectors_backend import DetectorBackend


class DetectorFrontend:
    "command line front end for convenient commands for Dectris Detectors"

    def __init__(self, ip, vers="1.7.0", port=80):
        self.detector = DetectorBackend(ip, vers, port)
        self.armID = -1

    """
        Basic setup up. This will At startup, the detector has to be initialized first"
    """

    def setup(self, datadir, frame_time=1.0, elements=["Mo", "Cu"], tmode="ints"):
        # self.detector.send_command("initialize")
        "Basic settings"
        # we always use trigger mote 'ints'
        self.detector.set_config("trigger_mode", tmode, "detector")
        # save 10,000 frames per HDF5 file
        self.detector.set_config("nimages_per_file", value=100000, iface="filewriter")
        # set to a very high number for continuous viewing
        self.detector.set_config("nimages", 10000, iface="detector")
        # default count and frame time: 100Hz
        self.set_frame_time(frame_time)
        # enable stream for STRELA viewer
        self.detector.set_config("mode", "enabled", iface="stream")
        # set list of allowed elements (for wavelength etc)
        self.elements = elements
        self.allowed_elements = self.detector.get_allowed("element", "detector")
        # output directory
        self.outdir = datadir

    """
    Get state for iface
    """

    def get_state(self, iface):
        mystate = self.detector.get_status(iface=iface, param="state")
        return mystate

    """ 
    return the list of files stored on DCU
    """

    def filelist(self):
        flist = self.detector.get_status(iface="filewriter", param="data")
        return flist

    """
    set the trigger mode of the detector
    """

    def triggermode(self, tmode, ntrigger=1):
        self.detector.set_config("trigger_mode", tmode, "detector")
        self.detector.set_config("ntrigger", ntrigger, "detector")

    def detector_trigger(self):
        self.detector.send_command("trigger")

    """
    Short cut for viewing w/o recording files:
    - disarm detector (to ensure consistent state)
    - disable filewriter 
    - set nimages to very high number
    - arm
    - trigger as background process
    """

    def view(self):
        "Disable writing and setup for viewing"
        self.detector.send_command("disarm")
        self.detector.set_config("mode", "disabled", "filewriter")
        self.detector.set_config("nimages", 1000000, "detector")
        self.arm()
        triggerproc = mp.Process(target=self.detector_trigger)
        triggerproc.start()

    """
    start recording of data by enabling file writer. nimages must be set
    """

    def record(self):
        "trigger armed detector in background"
        triggerproc = mp.Process(target=self.detector_trigger)
        triggerproc.start()

    """ 
    wrapper for arming the detector which updates the sequence id as variable for 
    self
    """

    def arm(self):
        "arms detector and returns current filename pattern"
        res = self.detector.send_command("arm")
        self.armID = res["sequence id"]
        return self.armID

    def stop(self):
        "Short cut to disarm the detector"
        self.detector.send_command("disarm")

    def initialize(self):
        "Initialize the detector. Resets ID"
        self.detector.send_command("initialize")

    def clear_files(self):
        "Delete all files stored on DCU"
        self.detector.send_command(command="clear", iface="filewriter")

    def set_frame_time(self, value):
        "sets count_ and frame_time"
        self.detector.set_config("count_time", value, "detector")
        self.detector.set_config("frame_time", value, "detector")

    def set_nimages(self, value):
        "sets number of images to be recorded"
        self.detector.set_config("nimages", value, "detector")

    """
    Shortcut for writer. Assumes that filepattern is set
    """

    def set_name_pattern(self, name_pattern):
        "append timestamp and id to name_stem and set name_pattern"
        self.detector.set_config("name_pattern", name_pattern, "filewriter")

    """
    wrapper to return name patterh
    """

    def get_name_pattern(self):
        np = self.detector.get_config(param="name_pattern", iface="filewriter")
        return np

    """ 
    set element type. Must conform to one of the elements supplied during setup
    (default: Mo and Cu)
    """

    def set_element(self, element):
        if element in self.elements and element in self.allowed_elements:
            self.detector.set_config("element", element, "detector")
        else:
            print(f"Element '{element}' not allowed")

    """
    record data for a certain time periond (seconds). Appends '_still' 
    to current name pattern and resets it afterwards. Meant to record
    images from crystals
    """

    def still(self, seconds=5):
        "Record data for seconds seconds"
        mystem = self.detector.get_config("name_pattern", "filewriter")
        frate = self.detector.get_config("frame_time", "detector")

        self.set_name_pattern(mystem + "still")

        nimages = round(seconds / frate)

        self.detector.send_command("disarm")
        self.detector.set_config("mode", "enabled", "filewriter")
        self.detector.set_config("nimages", nimages, "detector")
        self.arm()
        triggerproc = mp.Process(target=self.detector_trigger)
        triggerproc.start()
        triggerproc.join()
        # revert original pattern
        self.detector.set_config("name_pattern", mystem, "filewriter")
        self.view()

    """
    download the given file from the DCU and save it to output directory
    """

    def save_file(self, filename, outdir):
        url = f"http://{self.detector.ip_}:{self.detector.port_}/data/{filename}"
        r = get(url)
        localfile = join(outdir, filename)
        if not exists(localfile):
            open(localfile, "wb").write(r.content)
            # https://www.tutorialspoint.com/downloading-files-from-web-using-python

    """
    write out experimental parameters to a text file
    """

    def statusfile(self, filename):
        print("statusfile is not yet implemented")

    def wavelength(self):
        w = self.detector.get_config(param="wavelength", iface="detector")
        return w


if __name__ == "__main__":
    # univie = Quadro(SIP, SPORT, SVERS)
    print("error: DetectorFrontend should be importet and not run directly\n")
    exit(1)
