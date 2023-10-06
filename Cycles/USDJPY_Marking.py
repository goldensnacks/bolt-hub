import pickle
import sys
import os
from Cycles import UnderlierMarkingCycle

shrug = Shrugs("IBKR")
UnderlierMarkingCycle("USDJPY", shrug).cycle()