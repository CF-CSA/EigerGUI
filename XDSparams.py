import os

"""
Sets up XDS parameters from experimental parameters. Derived from SFRMtools. Also creates
subdirectories with XDS.INP
"""
class XDSparams:
    def __init__(self, xdstemplate):
        self.xdstempl= xdstemplate
        self.wavelength = 1.541840 # default: CuKa
        self.rotation_axis = [ 0, -1, 0] # default :positive rotation about omega

    """
    replace parameters in xdstemplate with given ones
    """
    def update(self, param_list):
        self.xdsinp = [] # empty XDS.INP
        with open (self.xdstemplate, 'r') as f:
            for line in f:
                [keyw, rem] = self.uncomment(line)
                for p in param_list:
                    key = p[0]
                    val = p[1]
                    keyw = self.replace(keyw, key, value)
                    self.xdsinp.append(' '+keyw+' ' +rem)

    def uncomment(self, line):
        "find exclamation mark and separate string at this point"
        if ("!" in line):
            idx = line.index("!")
            key = line[:idx]
            rem = line[idx:]
        else:
            keyw = line
            rem  = ""
        return [keyw, rem]

    """
    checks whether keyw is present in line (including '=' and
    replaces the subsequent value with val"""
    def replace(self, line, keyw, val):
        if (keyw in line):
            line = ' '+keyw+' ' +str(val)
        else:
            line = line
        return line

    """
    writes content of self.xdsinp into outdir as XDS.INP"""
    def xdswrite(self, outdir):
        fn = outdir+os.path.sep()+XDS.INP"
        with open (fn, 'w') as f:
            f.write("! XDS.INP written by EigerGUI")
            for l in self.xdsinp:
                f.write(l)


