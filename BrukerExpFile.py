import ast
import numpy as np

class ExpFile:
    "Read and process experimental description file from Bruker"

    def __init__(self, filename, verbosity=0):
        self.filename = filename
        self.allruns = []
        self.runs = []
        self.total_images = 0
        self.verbosity = verbosity
        """
        EXP file contains a comment block, followed by a 'dict' with the key 'scanset'
        content of scanset is a list of the individual runs:
        Runs are dictioneries with the entries:
        attenuation - number, expect '1'
        sensitivity - int 3 (?)
        frametime   - tuple, e.g. ('replace', 120.0)
        readout     - int, 3: shutterless
        step        - float, rad
        active      - Bool True/False
        end         - float, rad; end - start = SWEEP
        angle       - word, rotation axis
        p           - dict with parameters
        detectorsizemargin - float
        start       - float, radians; end - start = SWEEP
        frameangle  - tuple, e.g. ('replace', 1.0471975511965976) = WIDTH (per frame)
        anglemargin - float, radians?
        invertscan -  direction, True/False
        content of p (all floats except type):
          phi
          type 
          dx [mm]
          chi
          theta
          omega
        """


    """
    wrapper that calls all necessary functions to extract information from EXP-file
    """

    def extract(self):
        self.readexp()
        self.getinfo()

    """
    Bruker EXP looks close to JSON. Some conversions seem to make it compatible with JSON format
    for reading it
    """

    def readexp(self):
        with open(self.filename, "r") as f:
            expf = f.read()

        data = ast.literal_eval(expf)
        self.allruns = data["scanset"] # runs is a list; each list entry is a run, including one for setting wavelength
        if self.verbosity > 1:
            print(f"---> Reading {len(self.runs)} run entries from file {self.filename}")

    """
    extract information from runs
    """

    def getinfo(self):
        """
        find active runs, find wavelength setting
        and for each experimental run, extract the geometry settings.
        """
        active_runs = []
        run: dict
        for run in self.allruns:
            if run["active"] is True and "wavelength" in run:
                self.wavelength = run["wavelength"]
                if self.verbosity > 0:
                    print(f"---> Lambda = {self.wavelength}")
            if run["active"] is True and "p" in run:
                "create a list of active runs"
                active_runs.append(run)
            else:
                if self.verbosity > 1:
                    print(f"---> Inactive or setting run: {run}")
        if self.verbosity > 0:
            print(f"---> Number of active runs: {len(active_runs)}")
        """convert run structure to something reasonable for easier processing"""
        for run in active_runs:
            """start angle in parameters.end, end angles in end outside p"""
            if self.verbosity > 1:
                print(f"{run['p']}")
            params = run["p"]
            myrun = {}
            myrun["angle"] = run["angle"]
            myrun["start"] = run["start"]
            myrun["end"] = run["end"]
            myrun["phi"] = params["phi"]
            myrun["distance"] = params["dx"]
            myrun["chi"] = params["chi"]
            myrun["theta"] = params["theta"]
            myrun["omega"] = params["omega"]
            ft = run["frametime"]
            if ft is not None:
                myrun["frametime"] = ft[1]
            fa = run["frameangle"]
            if fa is not None:
                # frameangle: width per image recorded by APEX
                myrun["frameangle"] = fa[1]
                myrun["nimages"] = abs(myrun["end"] - myrun["start"]) / myrun["frameangle"]
                myrun["nimages"] = round(myrun["nimages"])
                self.total_images = self.total_images + myrun["nimages"]
                if self.verbosity > 1:
                    print(f"---> rounded number of images: {myrun['nimages']}")
            if "frametime" in myrun and "frameangle" in myrun:
                myrun["runtime"] = (
                    myrun["frametime"]
                    * (abs(myrun["end"] - myrun["start"]))
                    / myrun["frameangle"]
                )
                if self.verbosity > 1:
                    print(f"---> frametime = {myrun['frametime']}s, runtime = {round(myrun['runtime'], ndigits=2)}")
            else:
                print("### Cannot calculate runtime,  take from GUI")
            self.runs.append(myrun)
        if self.verbosity > 0:
            print(f"Number of active runs: {len(self.runs)}")
