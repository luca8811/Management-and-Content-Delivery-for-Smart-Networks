import random
from queue import PriorityQueue
import lab2
import results_visualization
from lab2 import (Event, evt_arrival, evt_departure, evt_recharge, evt_switch_off, clear_folder, overall_metrics)
from utils.queues import MMmB
import json

# Clear the folder where report images will be stored to ensure fresh output.
clear_folder('./report_images')

# Initialize variables and configurations for the simulation
lab2.init_variables("TASK2")
variables = lab2.variables
MMms = lab2.MMms
measurements = lab2.measurements
data = lab2.data

# Initialize a dictionary to store the departure rate results
results_dict = {}


# Function to run the simulation for a given WORKING_SCHEDULING configuration
def run_simulation(scheduling_key):
    # Initialize different drone types based on the configuration 'I'
    drone = variables["drone_types"]['A']  # Get drone specifications from configuration

    # Initialize an MMmB object for each drone type with its properties like power,
    # service rate, and buffer size
    MMms[0] = MMmB(
        power_supply=drone['POW'],  # Power supply of the drone
        service_times=[1 / (variables['BASE_SERVICE_RATE'] * drone['SERVICE_RATE'])],
        buffer_size=variables['BASE_BUFFER_SIZE'] * drone['BUFFER_SIZE'],  # Buffer size is multiplied by drone's factor
        maximum_recharge_cycles=variables["RECHARGE_CONSTRAINT"]["I"],  # Max number of recharge cycles for the drone
        working_slots=variables["WORKING_SCHEDULING"][scheduling_key]  # Time intervals when the drone is operational
    )

    # Simulation logic (same as before)
    random.seed(42)
    time = 0
    FES = PriorityQueue()
    FES.put((0, Event.ARRIVAL, None, None))

    while time < variables['SIM_TIME']:
        (time, event_type, drone_id, arg) = FES.get()

        if event_type == Event.ARRIVAL:
            evt_arrival(time, FES)
        elif event_type == Event.DEPARTURE:
            evt_departure(time, FES, drone_id, arg)
        elif event_type == Event.SWITCH_OFF:
            evt_switch_off(time, FES, drone_id, arg)
        elif event_type == Event.RECHARGE:
            evt_recharge(time, drone_id)

    # Calculate total working time for the current WORKING_SCHEDULING
    working_time = sum(slot[1] - slot[0] for slot in variables['WORKING_SCHEDULING'][scheduling_key])

    results = overall_metrics(data, working_time)
    results_dict["WORKING SCHEDULE" + " " + scheduling_key] = results

    return measurements, data


# Run the simulation for each WORKING_SCHEDULING configuration
for scheduling_key in variables[f"WORKING_SCHEDULING"]:

    # Run the simulation and get the results
    measurements, data = run_simulation(scheduling_key)

# Salva il dizionario in un file JSON
output_file_path = "./report_images/result_of_the_simulations_for_comparison.json"
with open(output_file_path, 'w') as json_file:
    json.dump(results_dict, json_file, indent=4)

results_visualization.plot_simulation_data(output_file_path)
