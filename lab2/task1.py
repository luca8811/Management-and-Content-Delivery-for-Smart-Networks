import random
from queue import PriorityQueue
import lab2
import results_visualization
from lab2 import (Event, evt_arrival, evt_departure, evt_recharge, evt_switch_off, calculate_warmup_period, clear_folder,
                  FilteredMeasurements)
from utils.queues import MMmB
import json

# Clear the folder where report images will be stored to ensure fresh output.
clear_folder('./report_images')

# Initialize variables and configurations for the simulation
lab2.init_variables("TASK1")  # This loads the variables.json file, which contains various configurations.
variables = lab2.variables  # All configurations and settings are now stored in the `variables` object.
MMms = lab2.MMms  # List of MMmB objects representing different drone types
measurements = lab2.measurements  # To store measurement data (arrivals, departures, losses, etc.)
data = lab2.data  # Overall data to store aggregated measurements over the simulation time

# Initialize different drone types based on the configuration 'I'
drone_types = variables['drone_types']
for i, drone_type in enumerate(variables['configurations']['I']):
    drone = drone_types[drone_type]  # Get drone specifications from configuration
    # Initialize an MMmB object for each drone type with its properties like power, service rate, and buffer size
    MMms[i] = MMmB(
        power_supply=drone['POW'],  # Power supply of the drone
        service_times=[1 / (variables['BASE_SERVICE_RATE'] * drone['SERVICE_RATE']) for m in range(drone['m_ANTENNAS'])],
        buffer_size=variables['BASE_BUFFER_SIZE'] * drone['BUFFER_SIZE'],  # Buffer size is multiplied by drone's factor
        maximum_recharge_cycles=variables["RECHARGE_CONSTRAINT"]["I"],  # Max number of recharge cycles for the drone
        working_slots=variables["WORKING_SCHEDULING"]["IV"]  # Time intervals when the drone is operational
    )

# Main simulation logic
if __name__ == '__main__':
    random.seed(42)  # Set a seed for reproducibility of random events in the simulation

    # Initialize simulation time
    time = 0

    # Priority queue for Future Event Scheduling (FES) to handle events like ARRIVAL, DEPARTURE, etc.
    FES = PriorityQueue()

    # Schedule the first event, an arrival at time 0, to start the simulation
    FES.put((0, Event.ARRIVAL, None, None))

    # Simulation loop continues until the total simulation time is reached
    while time < variables['SIM_TIME']:
        # Fetch the next event from the queue (sorted by event time)
        (time, event_type, drone_id, arg) = FES.get()

        # Handle different types of events
        if event_type == Event.ARRIVAL:
            evt_arrival(time, FES)  # Handle packet arrival event
        elif event_type == Event.DEPARTURE:
            evt_departure(time, FES, drone_id, arg)  # Handle packet departure event
        elif event_type == Event.SWITCH_OFF:
            evt_switch_off(time, FES, drone_id, arg)  # Handle drone switch off event
        elif event_type == Event.RECHARGE:
            evt_recharge(time, drone_id)  # Handle drone recharge event

    # Set the start time for visualizations based on the configured start time
    results_visualization.STARTING_TIME = variables['STARTING_TIME']

    # Calculate the warm-up period to remove transient behavior and focus on steady-state behavior
    warmup_period = calculate_warmup_period(
        buffer_size=variables['BASE_BUFFER_SIZE'] * drone['BUFFER_SIZE'],  # Calculate using buffer size
        measurements=measurements  # Use the recorded measurements to estimate when steady state is reached
    )

    # Load the steady-state time intervals from the generated JSON file
    steady_state_json_filepath = "./report_images/steady_state_working_slots.json"
    with open(steady_state_json_filepath) as json_file:
        steady_state_intervals = json.load(json_file)

    # Filter measurements to only include data during steady-state periods
    filtered_measurements = FilteredMeasurements(measurements, steady_state_intervals)

    # Generate various visualizations using the measurements and filtered steady-state data
    # Plot number of users over time with warm-up and steady-state periods highlighted
    results_visualization.plot_users_with_warmup(measurements=measurements, warmup_times=warmup_period)
    results_visualization.plot_users_with_steady_state(measurements=measurements)

    # Compare overall and steady-state metrics and generate a report for comparison
    results_visualization.compare_metrics(data, filtered_measurements)
