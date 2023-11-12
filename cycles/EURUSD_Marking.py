from securities.Shrugs import Shrugs
from cycles import UnderlierMarkingCycle

shrug = Shrugs("IBKR")
UnderlierMarkingCycle("EURUSD", shrug).cycle()