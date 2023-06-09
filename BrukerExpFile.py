import json

class Exp:
    "Read and process experimental description file from Bruker"
    def __init(self, filename):
        self.filename = filename

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
        wl = json.loads(json.dumps(self.exp['scanset'][0]))
        self.wavelength = wl['wavelength']
        self.json_runs = json.loads(json.dumps(self.exp['scanset'][1:-1]))
        # a run as a subkeyword ['active'] which is 1 or 0
        # looping: for j in (self.json_runs):
        #  if j['active'] -> paramters in j['p']
        #  run.params = json.loads(json.dumps(j['p'])

    def num_runs(self):
        self.runs =