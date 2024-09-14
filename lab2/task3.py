import random
from queue import PriorityQueue
import lab2
import results_visualization
from lab2 import (Event, evt_arrival, evt_departure, evt_recharge, evt_switch_off, clear_folder)
from utils.queues import MMmB
import json  # Import JSON for saving results

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
def run_simulation(scheduling_key, battery_strategy, configurations):
    # Initialize drone configurations based on the selected WORKING_SCHEDULING value
    drone_types = variables['drone_types']
    for i, drone_type in enumerate(variables['configurations'][configurations]):
        drone = drone_types[drone_type]
        MMms[i] = MMmB(
            power_supply=drone['POW'],
            service_times=[1 / (variables['BASE_SERVICE_RATE'] * drone['SERVICE_RATE']) for m in
                           range(drone['m_ANTENNAS'])],
            buffer_size=variables['BASE_BUFFER_SIZE'] * drone['BUFFER_SIZE'],
            maximum_recharge_cycles=variables["RECHARGE_CONSTRAINT"][battery_strategy],
            working_slots=variables["WORKING_SCHEDULING"][scheduling_key]
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

    # Calculate departure rate using the working time
    departure_rate = data.departures / working_time

    # Add results to the dictionary
    key = f"WORKING_SCHEDULING_{scheduling_key}_RECHARGE_CONSTRAINT_{battery_strategy}"
    results_dict[key] = {
        "departure_rate": departure_rate,
        "arrivals": data.arrivals,
        "departures": data.departures,
        "losses": data.losses
    }

    # Return the data
    return measurements, data


# Run simulations for each combination of WORKING_SCHEDULING and RECHARGE_CONSTRAINT
for scheduling_key in variables["WORKING_SCHEDULING"]:
    for battery_strategy in variables['RECHARGE_CONSTRAINT']:
        for configurations in variables['configurations']:
            measurements, data = run_simulation(scheduling_key, battery_strategy, configurations)

# Save the results to a JSON file
with open("simulation_results_task3.json", "w") as json_file:
    json.dump(results_dict, json_file, indent=4)

print("Results saved to simulation_results.json")
