import json

class ExpFile:
    "Read and process experimental description file from Bruker"
    def __init__(self, filename):
        self.filename = filename
        self.runs = []

    def readexp(self):
        with open(self.filename, 'r') as expfile:
            "remove header comment"
            jsondata = ''.join(line for line in expfile if not line.startswith('#'))
            "replace invalid json values"
            jsondata = jsondata.replace("'", "\"")
            jsondata = jsondata.replace("None", "\"None\"")
            jsondata = jsondata.replace("True", "1")
            jsondata = jsondata.replace("False", "0")
            allexp = json.loads(jsondata)
            self.exp = allexp['scanset']

    """
    extract information from runs
    """
    def getinfo(self):
        wl = json.loads(json.dumps(self.exp[0]))
        " debugging: print wavelength"
        self.wavelength = wl['wavelength']
        print (f"Lambda = {self.wavelength}")
        self.json_runs = json.loads(json.dumps(self.exp[1:-1]))
        """
        access information in self.json_runs with e.g.
        run = self.json_runs[0]['p']['chi']
        or 
        axis = self.json_runs[0]['angle']
        keys: attenutation, sensitivity, frametime, readout,step, active, end, angle
        keys in p: phi, type (?),dx (Delta), chi,theta, omega
        """
        for run in self.json_runs:
            if run['active']:
                "create a list of active runs"
                self.runs.append(run)
        print(f"Number of active runs: {len(self.runs)}")
        # a run as a subkeyword ['active'] which is 1 or 0
        # looping: for j in (self.json_runs):
        #  if j['active'] -> paramters in j['p']
        #  run.params = json.loads(json.dumps(j['p'])
