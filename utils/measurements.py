class Statistics:
    def __init__(self):
        self.arr = 0
        self.dep = 0
        self.los = 0
        self.users = 0
        self.drones = 0
        self.charging_drones = 0
        self.ut = 0
        self.oldT = 0
        self.delay = 0


class Measurements:
    def __init__(self):
        self.users = []
        self.drones = []
        self.charging_drones = []
        self.arrivals = []
        self.departures = []
        self.losses = []
        self.delay = []

    def add_record(self, time, data: Statistics):
        self.users.append((time, data.users))
        self.drones.append((time, data.drones))
        self.charging_drones.append((time, data.charging_drones))
        self.arrivals.append((time, data.arr))
        self.departures.append((time, data.dep))
        self.losses.append((time, data.los))
        self.delay.append((time, data.delay))

    def dispatch_users(self, starting_time):
        times = []
        users_t = []
        for time, users in self.users:
            times.append((time + starting_time) / 3600)
            users_t.append(users)
        return times, users_t

    def dispatch_drones(self, starting_time):
        times = []
        drones_t = []
        for time, drones in self.drones:
            times.append((time + starting_time) / 3600)
            drones_t.append(drones)
        return times, drones_t

    def dispatch_charging_drones(self, starting_time):
        times = []
        charging_drones_t = []
        for time, charging_drones in self.charging_drones:
            times.append((time + starting_time) / 3600)
            charging_drones_t.append(charging_drones)
        return times, charging_drones_t

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
