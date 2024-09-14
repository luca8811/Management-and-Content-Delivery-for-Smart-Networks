import random
from queue import PriorityQueue
import lab2
import results_visualization
from lab2 import (Event, evt_arrival, evt_departure, evt_recharge, evt_switch_off, clear_folder)
from utils.queues import MMmB

# Clear the folder where report images will be stored to ensure fresh output.
clear_folder('./report_images')

# Initialize variables and configurations for the simulation
lab2.init_variables("TASK2")
variables = lab2.variables
MMms = lab2.MMms
measurements = lab2.measurements
data = lab2.data


# Function to run the simulation for a given WORKING_SCHEDULING configuration
def run_simulation(scheduling_key):
    # Initialize drone configurations based on the selected WORKING_SCHEDULING value
    drone_types = variables['drone_types']
    for i, drone_type in enumerate((variables['configurations']['I'])):
        drone = drone_types[drone_type]
        MMms[i] = MMmB(
            power_supply=drone['POW'],
            service_times=[1 / (variables['BASE_SERVICE_RATE'] * drone['SERVICE_RATE']) for m in
                           range(drone['m_ANTENNAS'])],
            buffer_size=variables['BASE_BUFFER_SIZE'] * drone['BUFFER_SIZE'],
            maximum_recharge_cycles=variables["RECHARGE_CONSTRAINT"]["I"],
            working_slots=variables[f"WORKING_SCHEDULING"][scheduling_key]  # Use the specified WORKING_SCHEDULING
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

    print(f"\nResults for WORKING_SCHEDULING '{scheduling_key}':")

    # Visualize and print the results for each WORKING_SCHEDULING configuration
    results_visualization.plot_users(measurements)

    # Print output data for comparison
    print("\nMEASUREMENTS \n\nNo. of users in the queue:", data.users, "\nNo. of arrivals =",
          data.arrivals, "- No. of departures =", data.departures)

    print("\nArrival rate: ", data.arrivals / variables['SIM_TIME'], " - Departure rate: ",
          data.departures / variables['SIM_TIME'])
    print("Loss rate: ", data.losses / variables['SIM_TIME'], " - Packets loss: ", data.losses)
    print("Departures-losses ratio: ", data.departures / data.losses if data.losses > 0 else "N/A")
    print("Departures percentage: {:.1f}%".format(data.departures / data.arrivals * 100 if data.arrivals > 0 else 0))

    print("\nAverage number of users: ", data.average_users / variables['SIM_TIME'])
    print("Average delay: ", data.delay / data.departures if data.departures > 0 else "N/A")
    print("\n**** **** ****")

    return measurements, data


# Run the simulation for each WORKING_SCHEDULING configuration
for scheduling_key in variables[f"WORKING_SCHEDULING"]:

    # Run the simulation and get the results
    measurements, data = run_simulation(scheduling_key)
