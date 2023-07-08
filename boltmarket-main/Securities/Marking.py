import pickle
from Cycles import UnderlierMarkingCycle
import sys
import os
import openpyxl

# Add the parent directory (my_project) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname('boltmarket-main'), '..')))
from Shrugs import Shrugs


shrug = Shrugs("EURUSD")
UnderlierMarkingCycle("EURUSD", shrug).cycle()
