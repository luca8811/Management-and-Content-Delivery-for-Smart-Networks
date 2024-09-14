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

        # Filter the measurements based on steady state and activity
        self.filter_measurements_by_steady_state()

        # Compute cumulative metrics over the steady-state period
        self.compute_cumulative_metrics()

    def filter_measurements_by_steady_state(self):
        """
        Filters the measurements in the history attribute to include only those
        that occur during the drone's steady-state periods.
        When the drone is inactive or not in steady-state, the last valid measurement is used.
        System-wide metrics (arrivals, drones, losses, etc.) remain unfiltered.
        """
        filtered_history = []
        last_valid_measurement = None

        # System-wide attributes that should not be filtered (remain the same regardless of the drone's state)
        non_filtered_attributes = ['arrivals', 'departures', 'losses', 'transmitted_packets', 'busy_time',
                                   'drones', 'charging_drones']

        # Loop through all the measurements and filter based on the steady-state intervals and drone activity
        for measurement in self.original_measurements.history:
            # If the measurement is within a steady-state period and the drone is active
            if any(start <= measurement.time <= end for start, end in self.steady_state_intervals) and measurement.drones > 0:
                # Append the current measurement since the drone is active in steady state
                filtered_history.append(measurement)
                last_valid_measurement = measurement  # Update the last valid measurement for future use
            else:
                # If the drone is inactive or not in steady state, use the last valid measurement
                if last_valid_measurement:
                    # Create a copy of the last valid measurement but retain the original time
                    new_measurement = self.copy_measurement(last_valid_measurement)

                    # Ensure that system-wide attributes remain the same as the original measurement
                    for attr in non_filtered_attributes:
                        setattr(new_measurement, attr, getattr(measurement, attr))

                    # Keep the original time from the current measurement
                    new_measurement.time = measurement.time

                    # Add the copied measurement with updated attributes
                    filtered_history.append(new_measurement)

        # Replace the history with the filtered measurements
        self.history = filtered_history

    @staticmethod
    def copy_measurement(measurement):
        """
        Creates a copy of a measurement, without modifying the time.

        Args:
            measurement: The measurement to copy.

        Returns:
            A new Measurement object with the same attributes (except time, which is handled separately).
        """
        new_measurement = Measurement()
        # Copy all attributes from the existing measurement
        new_measurement.__dict__.update(measurement.__dict__)
        return new_measurement

    def compute_cumulative_metrics(self):
        # todo: non so come gestite losses, departures e delay. Il resto è ok.
        """
        Compute cumulative metrics such as total arrivals, departures, users, losses, and delays
        during the steady-state period. These are stored as attributes for easy access.
        """
        # Initialize attributes to store cumulative metrics
        self.total_users = 0
        self.total_arrivals = 0
        self.total_departures = 0
        self.total_losses = 0
        self.total_delay = 0
        self.steady_state_time = 0
        self.users = 0

        # Loop through the filtered measurements and accumulate metrics
        previous_time = None

        for i, measurement in enumerate(self.history):
            # Only accumulate time for actual steady-state periods
            if previous_time is not None:
                time_diff = measurement.time - previous_time
                self.steady_state_time += time_diff

            # Set cumulative metrics as the final values for the last measurement
            if i == len(self.history) - 1:
                self.users = measurement.users  # Take the last measurement for users
                self.total_arrivals = measurement.arrivals  # Take the last cumulative value for arrivals
                self.total_departures = measurement.departures  # Last cumulative value for departures
                self.total_losses = measurement.losses  # Last cumulative value for losses
                self.total_delay += measurement.delay

            self.total_users += measurement.users
            # self.total_arrivals += measurement.arrivals
            # self.total_departures += measurement.departures
            # self.total_losses += measurement.losses
            # self.total_delay += measurement.delay

            # Update the previous time
            previous_time = measurement.time

        # Calculate average values or rates based on the steady-state data
        if self.steady_state_time > 0:
            self.steady_state_arrival_rate = self.total_arrivals / self.steady_state_time
            self.steady_state_departure_rate = self.total_departures / self.steady_state_time
            self.steady_state_loss_rate = self.total_losses / self.steady_state_time
        else:
            self.steady_state_arrival_rate = 0
            self.steady_state_departure_rate = 0
            self.steady_state_loss_rate = 0

        self.average_users = self.total_users / len(self.history) if len(self.history) > 0 else 0
        self.average_delay = self.total_delay / self.total_departures if self.total_departures > 0 else 0
