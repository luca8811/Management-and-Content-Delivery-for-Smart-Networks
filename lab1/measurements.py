class Measure:
    def __init__(self):
        self.arr = 0  # Number of arrivals
        self.dep = 0  # Number of departures
        self.los = 0  # Number of lost packets
        self.ut = 0  # Time-weighted number of users in the system
        self.oldT = 0  # Previous event time
        self.delay = 0  # Total delay
        self.transmitted_packets = 0  # Number of transmitted packets
        self.average_packets = 0  # Sum of packets in the system for calculating average
        self.queue_delay = 0  # Total queue delay
        self.waiting_delay = 0  # Total waiting delay
        self.buffer_occupancy = 0  # Average buffer occupancy
        self.loss_probability = 0  # Loss probability
        self.busy_time = 0  # Total busy time of the server
        self.queue_delays = []  # List of individual queue delays for distribution
        self.waiting_delays = []  # List of individual waiting delays for distribution
        self.time_series = []  # Time series data for further analysis

# Example usage:
# data_points = [1, 2, 3, 4, 5]  # This should be replaced with actual data from simulations
# confidence_level = 0.95
# ci_lower, ci_upper = compute_confidence_interval(data_points, confidence_level)
# print("Confidence Interval:", ci_lower, ci_upper)
