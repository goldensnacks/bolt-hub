from cycles import Cycle
import securities as Sc
from tradables import Underlier
class UnderlierMarkingCycle(Cycle):
    def __init__(self, underliers, shrug):
        self.underliers = underliers
        self.shrug = shrug

    def mark_spot(self, underlier, spot):
        sec = Sc.get_security(underlier)
        sec.obj.mark_spot(spot)
        sec.save()
        print(f"Marked {underlier} spot at {spot}")

    def mark_spots(self):
        spots = self.get_spots()
        for underlier in self.underliers:
            self.mark_spot(underlier, spots[underlier])

    def get_spots(self):
        return self.shrug.datasource.get_spots(self.underliers)
    def cycle(self):
        while True:
            self.mark_spots()

