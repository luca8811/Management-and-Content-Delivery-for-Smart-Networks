import copy


class Measurement:
    """
    Represents a collection of different measurements (such as arrivals, departures, etc..) taken
    at a specified time.
    """

    def __init__(self):
        self.time = 0  # changed from 'oldT'
        self.arrivals = 0  # changed from 'arr'
        self.departures = 0  # changed from 'dep'
        self.losses = 0  # changed from 'los'
        self.users = 0
        self.drones = 0
        self.charging_drones = 0
        self.average_users = 0  # changed from ut
        self.delay = 0


class Measurements:
    """
    Represents the full collection of all the measurements taken over time. Used to gather
    information about how the simulation evolved and to plot the results
    """

    def __init__(self):
        self.history = [Measurement()]
        self._last_measurement = self.history[-1]

    def get_last_measurement(self):
        return self._last_measurement

    def get_last_time(self):
        return self._last_measurement.time

    def add_measurement(self, measurement: Measurement):
        self.history.append(copy.deepcopy(measurement))
