import copy

class Measurement:
    """
    Represents a collection of different measurements (such as arrivals, departures, etc..) taken
    at a specified time.
    """

    def __init__(self):
        self.time = 0  # Changed from 'oldT'
        self.arrivals = 0  # Changed from 'arr'
        self.departures = 0  # Changed from 'dep'
        self.losses = 0  # Changed from 'los'
        self.users = 0
        self.drones = 0
        self.charging_drones = 0
        self.average_users = 0  # Changed from 'ut'
        self.delay = 0
        self.average_delay = 0
        self.average_losses = 0
        self.transmitted_packets = 0  # Number of transmitted packets
        self.average_packets = 0  # Sum of packets in the system for calculating average
        self.queue_delay = 0  # Total queue delay
        self.waiting_delay = 0  # Total waiting delay
        self.buffer_occupancy = 0  # Average buffer occupancy
        self.loss_probability = 0  # Loss probability
        self.busy_time = 0  # Total busy time of the server
        self.queue_delays = []  # List of individual queue delays for distribution
        self.waiting_delays = []  # List of individual waiting delays for distribution

class Measurements:
    """
    Represents the full collection of all the measurements taken over time. Used to gather
    information about how the simulation evolved and to plot the results.
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
