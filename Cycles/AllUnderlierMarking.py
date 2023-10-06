from Securities.Shrugs import Shrugs
from Cycles import UnderlierMarkingCycle

shrug = Shrugs("IBKR")
UnderlierMarkingCycle(["EURUSD", "USDJPY"], shrug).cycle()