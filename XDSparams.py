import os

import numpy as np

"""
Sets up XDS parameters from experimental parameters. Derived from SFRMtools. Also creates
subdirectories with XDS.INP
"""


class XDSparams:
    def __init__(self, name_template, data_range):
        self.dataprefix = "../../data/"
        self.param_list = {"NAME_TEMPLATE_OF_DATA_FRAMES=": f"{self.dataprefix}{name_template}",
                           "DATA_RANGE=": f"{data_range}"}

    """
    Experimental settings based on oscillation width (float), wavelength (float), axis 
    (string), omega (radians)
    chi (float, radians), rotdir (+/-1), start (float, radians
    """

    def settings(self, oscw, wavelength, theta, axis, omega, chi, rotdir, start):
        self.param_list["OSCILLATION_RANGE="] = f"{oscw:6.3f}"
        self.param_list["X-RAY_WAVELENGTH="] = f"{wavelength:8.6f}"
        self.param_list["STARTING_ANGLE="] = f"{180./np.pi*start:6.4f}"
        if wavelength > 1.5:
            self.param_list["GAIN="] = "1.0"
        elif wavelength < 0.8:
            self.param_list["GAIN="] = "0.7"
        self.detector_x_axis(theta)
        self.rotation_axis(axis, omega, chi, rotdir)

    """
    replace parameters in xdstemplate with given ones
    This function should be last before writing XDS.INP 
    and param_list needs to be populated with keywords and values
    """

    def update(self, xdstemplate):
        self.xdsinp = []  # empty XDS.INP
        with open(xdstemplate, "r") as f:
            for line in f:
                newcmd = None
                for keyw in self.param_list:
                    if newcmd is None and keyw in line:
                        [cmdline, rem] = self.uncomment(line)
                        val = self.param_list[keyw]
                        newcmd = self.replace(cmdline, keyw, val)
                        self.xdsinp.append(f"  {newcmd} {rem}\n")
                """ check each line in template for keyword"""
                """ if newcmd still None, just append THIS LINE """
                if newcmd is None:
                    self.xdsinp.append(line)
    """
    Append lines excluding data ranges; can be called multiple times; 
    must be called after 'update', since update resets self.xdsinp
    """
    def exclude_data(self, excl_range):
        line = f' EXCLUDE_DATA_RANGE= {excl_range}\n'
        self.xdsinp.append(line)

    """
    search for exclamation marks and split the line into keyw (and value) 
    as well as remark. Copied from dectris2xds.py
    """

    @staticmethod
    def uncomment(line):
        """find exclamation mark and separate string at this point"""
        if "!" in line:
            idx = line.index("!")
            keyw = line[:idx]
            rem = line[idx:]
        else:
            keyw = line
            rem = ""
        return [keyw, rem]

    """
    checks whether keyw is present in line (including '=' and
    replaces the subsequent value with val.
    Copied from dectris2xds.py
    """

    @staticmethod
    def replace(line, keyw, val):
        if keyw in line:
            line = " " + keyw + " " + str(val)
            # keep track of replaced parameters
        else:
            line = line
        return line

    """
    Calculate the rotation axis from the input angles
    direction should be a number, positive or negative
    omega and chi are angles in radians
    """

    def rotation_axis(self, axis, omega, chi, direction):
        direction = np.sign(direction)
        if axis == "omega":
            rotaxis = direction * np.array([0, -1, 0])
        elif axis == "phi":
            x = direction * np.cos(omega) * np.sign(chi)
            y = direction * np.cos(chi)
            z = direction * np.sin(omega) * np.sin(chi)
            rotaxis = np.array([x, y, z])
        else:
            raise ValueError("Rotation axes other than omega or phi invalid")
        self.param_list[
            "ROTATION_AXIS="
        ] = f" {rotaxis[0]:6.5f} {rotaxis[1]:6.5f} {rotaxis[2]:6.5f}"

    """ 
    calculate and set the detector X-axis from theta
    """

    def detector_x_axis(self, theta):
        detx = [np.cos(2 * theta), 0.0, np.sin(2 * theta)]
        self.param_list[
            "DIRECTION_OF_DETECTOR_X-AXIS="
        ] = f"{detx[0]:9.6f} {detx[1]} {detx[2]:9.6f}"

    """
    writes content of self.xdsinp into outdir as XDS.INP"""

    def xdswrite(self, outdir):
        fn = outdir + os.path.sep + "XDS.INP"
        os.makedirs(outdir, exist_ok=True)
        with open(fn, "w") as f:
            f.write("! XDS.INP written by EigerGUI")
            for myline in self.xdsinp:
                f.write(myline)
