class Statistics:
    def __init__(self, Narr, Ndep, Nlos, NAverageUser, OldTimeEvent, AverageDelay):
        self.arr = Narr
        self.dep = Ndep
        self.los = Nlos
        self.ut = NAverageUser
        self.oldT = OldTimeEvent
        self.delay = AverageDelay


class Measurements:
    def __init__(self):
        self.users = []
        self.arrivals = []
        self.departures = []
        self.losses = []
        self.delay = []

    def add_record(self, time, users, arrivals, departures, losses, delay):
        self.users.append((time, users))
        self.arrivals.append((time, arrivals))
        self.departures.append((time, departures))
        self.losses.append((time, losses))
        self.delay.append((time, delay))

    def dispatch_users(self, starting_time):
        times = []
        users_t = []
        for time, users in self.users:
            times.append((time + starting_time) / 3600)
            users_t.append(users)
        return times, users_t

    def dispatch_arrivals(self, starting_time):
        times = []
        arrivals_t = []
        for time, arrivals in self.arrivals:
            times.append((time + starting_time) / 3600)
            arrivals_t.append(arrivals)
        return times, arrivals_t

    def dispatch_departures(self, starting_time):
        times = []
        departures_t = []
        for time, departures in self.departures:
            times.append((time + starting_time) / 3600)
            departures_t.append(departures)
        return times, departures_t

    def dispatch_losses(self, starting_time):
        times = []
        losses_t = []
        for time, losses in self.losses:
            times.append((time + starting_time) / 3600)
            losses_t.append(losses)
        return times, losses_t

    def dispatch_delay(self, starting_time):
        times = []
        delay_t = []
        for time, delay in self.delay:
            times.append((time + starting_time) / 3600)
            delay_t.append(delay)
        return times, delay_t
