import pickle
import sys
from datetime import datetime, date, timedelta
import sys
import os
import openpyxl
import xlwings as xw

# Add the parent directory (my_project) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname('boltmarket-main'), '..')))
from Shrugs import Shrugs
from Securities import get_security, Security

class Cycle:
    def __init__(self):
        pass

class UnderlierMarkingCycle(Cycle):
    def __init__(self, underlier, shrug):
        self.underlier = underlier
        self.shrug = shrug

    def mark_spot(self):
        spot = self.shrug.get_val(self.underlier, "spot")
        sec = get_security(self.underlier)
        sec.mark_spot(spot)
        sec.save()

    def cycle(self):
        while True:
            self.mark_spot()

class GUICycle(Cycle):
    def __init__(self, excel, tab, mappings):
        self.excel = excel
        self.tab = tab
        self.mappings = mappings


        super().__init__()

    def cycle(self):
        while True:
            wb = xw.Book(r'C:\Users\jacob\bolt-hub\GUI.xlsx')
            sht = wb.sheets[0]
            for item in self.mappings.items():
                sht.range(item[0]).value = item[1]()


