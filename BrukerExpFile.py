import ast


class ExpFile:
    "Read and process experimental description file from Bruker"

    def __init__(self, filename):
        self.filename = filename
        self.runs = []
        self.total_images = 0

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
        self.exp = data["scanset"]

    """
    extract information from runs
    """

    def getinfo(self):
        self.wavelength = self.exp[0]["wavelength"]
        print(f"Lambda = {self.wavelength}")
        allruns = self.exp[1:]
        """
        access information in self.json_runs with e.g.
        run = self.json_runs[0]['p']['chi']
        or 
        axis = self.json_runs[0]['angle']
        keys: attenutation, sensitivity, frametime, readout,step, active, end, angle
        keys in p: phi, type (?),dx (Delta), chi,theta, omega
        """
        active_runs = []
        for run in allruns:
            if run["active"] and "p" in run:
                "create a list of active runs"
                active_runs.append(run)
            else:
                print(f"Inactive run: {run}")
        print(f"Number of active runs: {len(active_runs)}")
        """convert run structure to something reasonable for easier processing"""
        for run in active_runs:
            """start angle in parameters.end, end angles in end outside p"""
            if "p" not in run:
                """This is not a run, but some other description"""
                print(f"Error, no parameters in run {run}")
            else:
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
                print(f"rounded number of images: {myrun['nimages']}")
            if "frametime" in myrun and "frameangle" in myrun:
                myrun["runtime"] = (
                    myrun["frametime"]
                    * (abs(myrun["end"] - myrun["start"]))
                    / myrun["frameangle"]
                )
                print(f"frametime = {myrun['frametime']}s, runtime = {myrun['runtime']}")
            else:
                print("Cannot calculate runtime,  take from GUI")
            self.runs.append(myrun)
        print(f"Number of active runs: {len(self.runs)}")

        # a run as a subkeyword ['active'] which is 1 or 0
        # looping: for j in (self.json_runs):
        #  if j['active'] -> paramters in j['p']
        #  run.params = json.loads(json.dumps(j['p'])
