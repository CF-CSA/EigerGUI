import json


class ExpFile:
    "Read and process experimental description file from Bruker"

    def __init__(self, filename):
        self.filename = filename
        self.runs = []

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
        with open(self.filename, "r") as expfile:
            "remove header comment"
            jsondata = "".join(line for line in expfile if not line.startswith("#"))
            "replace invalid json values"
            jsondata = jsondata.replace(" ('replace',", "")
            jsondata = jsondata.replace(")", "")
            jsondata = jsondata.replace("'", '"')
            jsondata = jsondata.replace("None", '"None"')
            jsondata = jsondata.replace("True", "1")
            jsondata = jsondata.replace("False", "0")
            allexp = json.loads(jsondata)
            self.exp = allexp["scanset"]

    """
    extract information from runs
    """

    def getinfo(self):
        wl = json.loads(json.dumps(self.exp[0]))
        " debugging: print wavelength"
        self.wavelength = wl["wavelength"]
        print(f"Lambda = {self.wavelength}")
        self.json_runs = json.loads(json.dumps(self.exp[1:]))
        """
        access information in self.json_runs with e.g.
        run = self.json_runs[0]['p']['chi']
        or 
        axis = self.json_runs[0]['angle']
        keys: attenutation, sensitivity, frametime, readout,step, active, end, angle
        keys in p: phi, type (?),dx (Delta), chi,theta, omega
        """
        apexruns = []
        for run in self.json_runs:
            if run["active"]:
                "create a list of active runs"
                apexruns.append(run)
            else:
                print(f"Inactive run: {run}")
        print(f"Number of apexruns: {len(apexruns)}")
        "convert run structure to something reasonable for easier processing"
        for run in apexruns:
            "start angle in parameters.end, end angles in end outside p"
            params = json.loads(json.dumps(run["p"]))
            myrun = {}
            ft = run["frametime"]
            if not ft == "None":
                myrun["frametime"] = float(ft)
            fa = run["frameangle"]
            if not fa == "None":
                myrun["frameangle"] = float(fa)
            myrun["angle"] = run["angle"]
            myrun["start"] = run["start"]
            myrun["end"] = run["end"]
            myrun["phi"] = params["phi"]
            myrun["distance"] = params["dx"]
            myrun["chi"] = params["chi"]
            myrun["theta"] = params["theta"]
            myrun["omega"] = params["omega"]
            if "frametime" in myrun and "frameangle" in myrun:
                myrun['runtime'] = myrun["frametime"] * (myrun["end"] - myrun["start"])/
                print(f"frametime = {myrun['frametime']}s")
            else:
                print("Cannot calculate runtime take from GUI")
            self.runs.append(myrun)
        print(f"Number of active runs: {len(self.runs)}")

        # a run as a subkeyword ['active'] which is 1 or 0
        # looping: for j in (self.json_runs):
        #  if j['active'] -> paramters in j['p']
        #  run.params = json.loads(json.dumps(j['p'])
