import pickle
from Shrugs import Shrugs

class Cycle:
    def __init__(self,
                 cycle_id=None,       cycle_name=None,   cycle_start_date=None,
                 cycle_end_date=None, cycle_status=None, cycle_description=None):
        self.cycle_id = cycle_id
        self.cycle_name = cycle_name
        self.cycle_start_date = cycle_start_date
        self.cycle_end_date = cycle_end_date
        self.cycle_status = cycle_status
        self.cycle_description = cycle_description


class UnderlierMarkingCycle(Cycle):
    def __init__(self, underlier, shrug,
                 cycle_id=None, cycle_name=None, cycle_start_date=None,
                 cycle_end_date=None, cycle_status=None, cycle_description=None
                 ):
        self.underlier = underlier
        self.shrug = shrug
        super().__init__(cycle_id, cycle_name, cycle_start_date, cycle_end_date, cycle_status, cycle_description)

    def mark_spot(self):
        spot = self.shrug.get_val(self.underlier.name, "spot")
        self.underlier.mark_spot(spot)

    def cycle(self):
        while True:
            self.mark_spot()

"""load EURUSD.pkl as underlier"""

with open('Securities/EURUSD.pkl', 'rb') as f:
    underlier = pickle.load(f)

shrug = Shrugs("EURUSD")
UnderlierMarkingCycle(underlier, shrug).cycle()