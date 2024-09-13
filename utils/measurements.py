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


class FilteredMeasurements(Measurements):
    def __init__(self, original_measurements, steady_state_intervals):
        """
        Initialize the FilteredMeasurements class, inheriting from Measurements.
        It filters measurements based on steady-state periods for drone operation.

        Args:
            original_measurements: The original Measurements object containing all data points.
            steady_state_intervals: A list of tuples, where each tuple contains (start_time, end_time)
                                    representing the steady-state periods for drone operation.
        """
        # Initialize the base Measurements class
        super().__init__()

        # Store the original measurements and intervals
        self.original_measurements = original_measurements
        self.steady_state_intervals = steady_state_intervals

        # Filter the measurements
        self.filter_measurements_by_steady_state()

    def filter_measurements_by_steady_state(self):
        """
        Filters the measurements in the history attribute to include only those
        that occur during the drone's steady-state periods.
        When the drone is inactive or not in steady-state, the last valid measurement is used.
        Specific attributes (arrivals, drones, losses) remain unfiltered.
        """
        filtered_history = []
        last_valid_measurement = None

        # Attributes that should not be filtered because independent of warm-up period.
        non_filtered_attributes = ['time', 'arrivals', 'departures', 'losses', 'transmitted_packets', 'busy_time']

        # Loop through all the measurements and filter based on the steady-state intervals and drone activity
        for measurement in self.original_measurements.history:
            if any(start <= measurement.time <= end for start, end in
                   self.steady_state_intervals) and measurement.drones > 0:
                # If in steady-state and the drone is active, use the current measurement
                filtered_history.append(measurement)
                last_valid_measurement = measurement  # Update the last valid measurement
            else:
                # If not in steady-state or the drone is inactive, repeat the last valid measurement
                if last_valid_measurement:
                    # Create a copy of the last valid measurement but update the time
                    new_measurement = self.copy_measurement(last_valid_measurement, new_time=measurement.time)

                    # Ensure that certain attributes remain the same as in the original measurement
                    for attr in non_filtered_attributes:
                        setattr(new_measurement, attr, getattr(measurement, attr))

                    # Add the copied measurement with updated attributes
                    filtered_history.append(new_measurement)

        # Replace the history with the filtered measurements
        self.history = filtered_history

    @staticmethod
    def copy_measurement(measurement, new_time):
        """
        Creates a copy of a measurement, updating its time to new_time.

        Args:
            measurement: The measurement to copy.
            new_time: The new time for the copied measurement.

        Returns:
            A new Measurement object with updated time.
        """
        new_measurement = Measurement()
        # Copy all attributes from the existing measurement
        new_measurement.__dict__.update(measurement.__dict__)
        # Update the time to the new time
        new_measurement.time = new_time
        return new_measurement
