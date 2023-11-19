from Securities.Shrugs import Shrugs
from cycles import UnderlierMarkingCycle


def main():
    shrug = Shrugs("IBKR")
    UnderlierMarkingCycle(["EURUSD", "USDJPY"], shrug).cycle()


if __name__ == "__main__":
    main()
