import copy
import matplotlib.pyplot as plt


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
        self.total_users = 0
        self.working_interval = 25 * 60  # 25 minutes of work before recharging
        self.charging_cycles = 0  # Number of complete discharge/charge cycles

        # TODO: da controllare - non tutti sono utilizzati
        self.average_delay = 0
        self.average_losses = 0
        # self.transmitted_packets = 0  # Number of transmitted packets
        # self.average_packets = 0  # Sum of packets in the system for calculating average
        self.queue_delay = 0  # Total queue delay
        self.waiting_delay = 0  # Total waiting delay
        self.buffer_occupancy = 0  # Average buffer occupancy
        self.loss_probability = 0  # Loss probability
        self.busy_time = 0  # Total busy time of the server
        # self.queue_delays = []  # List of individual queue delays for distribution
        # self.waiting_delays = []  # List of individual waiting delays for distribution


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


class FilteredMeasurements(Measurement, Measurements):
    def __init__(self, original_measurements, steady_state_list, start_working_time):
        """
        Initialize the FilteredMeasurements class, inheriting from Measurements.
        It filters measurements based on steady-state periods for drone operation.

        Args:
            original_measurements: The original Measurements object containing all data points.
            steady_state_list: A list of tuples, where each tuple contains (start_time, end_time)
                                    representing the steady-state periods for drone operation.
        """
        # Initialize the base Measurements class
        super().__init__()

        # Store the original measurements and intervals
        self.original_measurements = original_measurements

        self.start_working_time = start_working_time
        self.start_steady_state = steady_state_list[0]
        self.end_steady_state = steady_state_list[1]

        self.steady_state_interval = self.end_steady_state - self.start_steady_state
        self.warmup_interval = self.start_steady_state - self.start_working_time

        # Filter the measurements based on steady state and activity
        self.filter_measurements_by_steady_state()

        # Add cumulative attributes
        self.warmup_cumulative_attributes()
        self.cumulative_attributes()

    def filter_measurements_by_steady_state(self):
        """
        Filters the measurements in the history attribute to include only those
        that occur during the drone's steady-state periods.
        """
        filtered_history = []
        warmup_history = []
        erased_history = []
        filtered_I_O = []

        # Loop through all the measurements and filter based on the steady-state intervals and drone activity
        for measurement in self.original_measurements.history:
            # If the measurement is within a steady-state period and the drone is active
            if self.start_steady_state <= measurement.time <= self.end_steady_state and measurement.drones > 0:
                # Append the current measurement since the drone is active in steady state
                filtered_history.append(measurement)
                filtered_I_O.append(1)
            elif self.start_working_time <= measurement.time <= self.start_steady_state:
                filtered_I_O.append(0)
                warmup_history.append(measurement)
            else:
                erased_history.append(measurement)
                filtered_I_O.append(-1)

        # Replace the history with the filtered measurements
        self.history = filtered_history
        self.warmup_history = warmup_history
        self.erased_history = erased_history
        self.check_filter = filtered_I_O
        # self.check_filter_plot()

    def warmup_cumulative_attributes(self):
        if self.warmup_history:
            self.warmup_arrivals = self.warmup_history[-1].arrivals
            self.warmup_departures = self.warmup_history[-1].departures
            self.warmup_losses = self.warmup_history[-1].losses
            self.warmup_delays = self.warmup_history[-1].delay
            self.warmup_total_users = sum(measurement.users for measurement in self.warmup_history)
        else:
            self.warmup_arrivals = 0
            self.warmup_departures = 0
            self.warmup_losses = 0
            self.warmup_delays = 0
            self.warmup_total_users = 0

    def cumulative_attributes(self):
        self.arrivals = self.history[-1].arrivals - self.warmup_arrivals
        self.departures = self.history[-1].departures - self.warmup_departures
        self.losses = self.history[-1].losses - self.warmup_losses
        self.users = self.history[-1].users
        self.drones = self.history[-1].drones
        self.charging_drones = self.history[-1].charging_drones
        self.delay = self.history[-1].delay - self.warmup_delays
        self.total_users = sum(measurement.users for measurement in self.history)

    def reset_attributes(self):
        """
        Reset all attributes to their initial or default values.
        """
        # Reset history-related attributes
        self.history = []
        self.warmup_history = []
        self.erased_history = []
        self.check_filter = []

        # Reset cumulative attributes
        self.warmup_arrivals = 0
        self.warmup_departures = 0
        self.warmup_losses = 0
        self.warmup_delays = 0
        self.warmup_total_users = 0

        self.arrivals = 0
        self.departures = 0
        self.losses = 0
        self.users = 0
        self.drones = 0
        self.charging_drones = 0
        self.delay = 0
        self.total_users = 0

    def check_filter_plot(self):
        plt.figure(figsize=(10, 5))
        plt.plot(self.check_filter, marker='o', linestyle='-', color='b')
        plt.xlabel('Index')
        plt.ylabel('Value')
        plt.title('Line Plot of Binary List')
        plt.grid(True)
        # output_filename = "./report_images/culo.png"
        # plt.savefig(output_filename)
        # plt.close()
        plt.show()
