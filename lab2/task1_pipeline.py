import random
from queue import PriorityQueue
import lab2
import results_visualization
from lab2 import (Event, evt_arrival, evt_departure, evt_recharge, evt_switch_off, calculate_warmup_period,
                  clear_folder, seconds_to_time_string, start_working_intervals, save_steady_state_metrics, FilteredMeasurements)
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

# Initialize a dictionary to store the departure rate results
results_dict = {}

start_working_times = start_working_intervals(variables["SIM_TIME"], variables["WORKING_SCHEDULING"]["V"])


# Function to run the simulation for a given [da decidere] configuration
def simulation_pipeline(slot_counter, start_working_time):
    # Initialize different drone types based on the configuration 'I'
    drone = variables["drone_types"]['A']  # Get drone specifications from configuration

    # Initialize an MMmB object for each drone type with its properties like power,
    # service rate, and buffer size
    MMms[0] = MMmB(
        power_supply=drone['POW'],  # Power supply of the drone
        service_times=[1 / (variables['BASE_SERVICE_RATE'] * drone['SERVICE_RATE'])],
        buffer_size=variables['BASE_BUFFER_SIZE'] * drone['BUFFER_SIZE'],  # Buffer size is multiplied by drone's factor
        maximum_recharge_cycles=variables["RECHARGE_CONSTRAINT"]["I"],  # Max number of recharge cycles for the drone
        working_slots=variables["WORKING_SCHEDULING"]["IV"]  # Time intervals when the drone is operational
    )

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
        steady_state_lists = json.load(json_file)

    # Filter measurements to only include data during steady-state periods
    filtered_measurements = FilteredMeasurements(measurements, steady_state_lists[slot_counter], start_working_time)

    steady_state_metrics = save_steady_state_metrics(filtered_measurements)

    time_key = seconds_to_time_string(start_working_time)

    results_dict[time_key] = steady_state_metrics

    # title = time_key + "-" + f"{seconds_to_time_string(start_working_time+1500)}"

    # Compare overall and steady-state metrics and generate a report for comparison
    # results_visualization.compare_metrics(data, filtered_measurements, title)

    filtered_measurements.reset_attributes()


for slot_counter, start_working_time in enumerate(start_working_times):
    simulation_pipeline(slot_counter, start_working_time)

# Salva il dizionario in un file JSON
output_file_path = "./report_images/result_of_the_simulations_for_comparison.json"
with open(output_file_path, 'w') as json_file:
    json.dump(results_dict, json_file, indent=4)

# Generate various visualizations using the measurements and filtered steady-state data
# Plot number of users over time with warm-up and steady-state periods highlighted
results_visualization.plot_users_with_steady_state(measurements=measurements)
