class Measure:
    def __init__(self, Narr, Ndep, Nlos, NAverageUser, OldTimeEvent, AverageDelay):
        self.arr = Narr
        self.dep = Ndep
        self.los = Nlos
        self.ut = NAverageUser
        self.oldT = OldTimeEvent
        self.delay = AverageDelay