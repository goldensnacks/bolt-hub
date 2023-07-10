import pickle
import sys
import os
import openpyxl
sys.path.append('C:\\Users\\jacob\\bolt-hub\\boltmarket-main\\Securities')
sys.path.append('C:\\Users\\jacob\\bolt-hub\\boltmarket-main')
from Shrugs import Shrugs
from Cycles import UnderlierMarkingCycle

shrug = Shrugs()
UnderlierMarkingCycle("EURUSD", shrug).cycle()