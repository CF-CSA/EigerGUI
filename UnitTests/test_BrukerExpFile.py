from unittest import TestCase
from BrukerExpFile import ExpFile

class TestExpFile(TestCase):
    def test_readexp(self):
        self.expf = ExpFile("16BM22.exp")
        self.expf.readexp()

    def test_getinfo(self):
        self.test_readexp()
        self.expf.getinfo()

if __name__ == "__main__":
    print("Testing readexp")
    myexp = TestExpFile()
    myexp.test_readexp()