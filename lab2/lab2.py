import json
import os
import random
import shutil
from enum import Enum
from queue import PriorityQueue

import arrivals_profile
from utils.measurements import Measurement, Measurements
from utils.queues import BatteryStatus, Battery, Packet

# LEGEND:
#   - FES: Finite Event Schedule

variables = {}
MMms = {}
data = Measurement()
measurements = Measurements()


def init_simulation_environment():
    global data, measurements
    data = Measurement()
    measurements = Measurements()


def init_variables(task):
    """
    Initializes the environment of the running case, loading the configuration
    file "variables.json". These variables are largely used inside the program,
    so it is useful to make them change depending on the threatened task
    """
    global variables
    with open('variables.json') as f:
        variables = json.load(f)[task]


class Event(Enum):
    ARRIVAL = 1
    DEPARTURE = 2
    SWITCH_OFF = 3
    RECHARGE = 4


def is_drone_available(time, drone: MMms):
    return (drone.is_in_working_slot(time)
            and not drone.has_exceeded_max_complete_cycles()
            and drone.battery.status == BatteryStatus.IN_USE
            and not drone.is_queue_full())


def is_drone_ready(time, drone: MMms):
    return (drone.battery.status in [BatteryStatus.PAUSED, BatteryStatus.FULL]
            and drone.is_in_working_slot(time)
            and not drone.has_exceeded_max_complete_cycles())


def assign_packet_to_drone(time):
    # """
    # When a packet arrives, we want it to be assigned to a running drone.
    # It returns the id of the fastest (highest capacity) drone, if any
    # available (running and with space inside its queue).
    # """
    #
    # def is_available(drone: tuple[int, MMms]):
    #     return drone[1].battery.status == BatteryStatus.IN_USE and not drone[1].is_queue_full()
    #
    # drones = list(filter(is_available, MMms.items()))
    # if len(drones) > 0:
    #     drones = sorted(drones, key=lambda drone: drone[1].get_capacity(), reverse=True)
    #     return drones[0][0]
    # return None
    requested_drone_id = random.choice(list(MMms.keys()))
    drone = MMms[requested_drone_id]
    if is_drone_available(time, drone):
        return requested_drone_id
    else:
        return None


def send_drone(time, FES: PriorityQueue, drone_id, desired_time=0):
    """
    Activates a drone, and schedules its battery consumption.
    If 'tot_time' is set to 0, the maximum will be set
    """
    drone = MMms[drone_id]
    # checking if battery is full, and managing the case of an eventual solar panel equipped
    if drone.battery.status == BatteryStatus.FULL:
        drone.switch_on(solar_panel=8 * 3600 <= time <= 16 * 3600)
    if desired_time == 0:
        tot_time = drone.battery.residual
    else:
        tot_time = min(desired_time, drone.battery.residual)
    if not drone.battery.is_infinite():
        FES.put((time + tot_time, Event.SWITCH_OFF, drone_id, tot_time))
    data.drones += 1
    measurements.add_measurement(measurement=data)


def request_drone(time):
    """
    Used after a loss, to "call" another drone to manage the load.
    It returns the id of the fastest (average service time of its servers)
    drone, if any available (battery not empty).
    """
    drones = list(filter(lambda drone: is_drone_ready(time, drone[1]), MMms.items()))
    if len(drones) > 0:
        drones = sorted(drones, key=lambda drone: drone[1].get_capacity(), reverse=True)
        i_max = len(drones) - 1
        req = int(i_max * arrivals_profile.arrivals_profile[int(time / 3600)])
        return drones[req][0]
    return None


def schedule_recharge(time, FES: PriorityQueue, drone_id):
    """
    Used to schedule the fully charged battery of a drone, after it has
    been emptied.
    """
    FES.put((time + Battery.RECHARGE_TIME, Event.RECHARGE, drone_id, None))
    data.charging_drones += 1
    measurements.add_measurement(measurement=data)
    req_drone = request_drone(time)
    if req_drone is not None:
        send_drone(time, FES, req_drone)


def evt_switch_off(time, FES: PriorityQueue, drone_id, tot_time):
    """
    Called when a drone has to be switched off. All its queue is lost, even
    if there's still energy in its battery.
    """
    drone = MMms[drone_id]
    drone.battery_consume(usage_time=tot_time)
    if drone.battery.residual == 0:
        data.users -= drone.queue_size()
        drone.switch_off(empty_battery=True)
        schedule_recharge(time, FES, drone_id)
    else:
        drone.switch_off(empty_battery=False)
    data.drones -= 1
    measurements.add_measurement(measurement=data)


def evt_recharge(time, drone_id):
    """
    Called when the battery of a drone has been fully charged.
    """
    drone = MMms[drone_id]
    drone.battery_recharge()
    data.charging_drones -= 1
    measurements.add_measurement(measurement=data)


def evt_arrival(time, FES: PriorityQueue):
    """
    Called when there's an arrival packet.
    """
    # loss management - boolean result
    drone_id = assign_packet_to_drone(time)
    loss = drone_id is None
    if loss:
        req_drone_id = request_drone(time)
        if req_drone_id is not None:
            send_drone(time, FES, req_drone_id)
        data.losses += 1
    else:
        data.users += 1
        # create a record for the client
        client = Packet(arrival_time=time)
        # insert the record in the queue
        drone = MMms[drone_id]
        drone.insert(packet=client)

        # if the server is idle start the service
        if drone.can_engage_server():
            (s_id, s_service_time) = drone.engage_server()
            # sample the service time
            service_time = random.expovariate(1.0 / s_service_time)

            # schedule when the client will finish the service
            FES.put((time + service_time, Event.DEPARTURE, drone_id, s_id))

    # sample the time until the next event
    current_arrival_percentage = arrivals_profile.arrivals_profile[int(time / 3600)]
    inter_arrival = random.expovariate(lambd=variables['ARRIVAL_RATE'] * current_arrival_percentage)

    # schedule the next arrival
    FES.put((time + inter_arrival, Event.ARRIVAL, None, None))

    # cumulate statistics
    data.arrivals += 1
    data.total_users += data.users
    data.average_users += data.users * (time - data.time)  # average users per time unit
    data.time = time
    # measurements
    measurements.add_measurement(measurement=data)


def evt_departure(time, FES, drone_id, server_id):
    """
    Called when a packet has been processed by a server of a drone.
    """
    # drone scheduled
    drone = MMms[drone_id]

    # losses management
    loss = drone.battery.status != BatteryStatus.IN_USE
    if loss:
        data.losses += 1
        data.average_losses = data.losses / data.arrivals
    else:
        data.users -= 1
        data.departures += 1
        # get the first element from the queue
        client = drone.consume(server_id)

        # do whatever we need to do when clients go away

        data.delay += (time - client.arrival_time)

        # see whether there are more clients to in the line
        if drone.can_engage_server():
            (s_id, s_service_time) = drone.engage_server()
            # sample the service time
            service_time = random.expovariate(1.0 / s_service_time)

            # schedule when the client will finish the service
            FES.put((time + service_time, Event.DEPARTURE, drone_id, s_id))

    # cumulate statistics
    data.total_users += data.users
    data.average_users += data.users * (time - data.time)
    data.time = time
    data.average_delay = data.delay / data.departures
    # measurements
    measurements.add_measurement(measurement=data)


def clear_folder(folder_path):
    # Loop through all the files and directories inside the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Delete the file
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Delete the directory and its contents
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')


def calculate_warmup_period(buffer_size, measurements: Measurements, gap_threshold=100):
    """
    Calculates the warmup period for each working slot, where users != 0,
    and saves a JSON file containing the working slots in steady state.

    :param buffer_size: The buffer size to determine when the system reaches steady-state.
    :param measurements: The measurements object containing user counts over time.
    :param gap_threshold: The maximum allowed gap (in time units) to merge consecutive working slots.
    :return: List of transition points from transient to steady-state for each slot.
    """
    # Extract the times and the number of users from the measurement history
    lot = list(map(lambda m: (m.time, m.users), measurements.history))
    times, users = list(zip(*lot))

    # List to store the transition points from transient to steady-state for each time slot
    warmup_times = []

    # Detect working slots where users != 0
    time_slots = []
    steady_state_slots = []  # To store the steady state working slots
    in_slot = False
    start_time = None
    last_nonzero_time = None

    for time, user_count in zip(times, users):
        if user_count != 0:
            if not in_slot:
                # Start a new slot if we weren't already in one
                start_time = time
                in_slot = True
            last_nonzero_time = time
        elif in_slot and (time - last_nonzero_time > gap_threshold):
            # End the current slot if users have been zero for longer than the gap threshold
            end_time = last_nonzero_time
            time_slots.append([start_time, end_time])
            in_slot = False

    # If the last time slot is still open, close it at the last non-zero user time
    if in_slot:
        time_slots.append([start_time, last_nonzero_time])

    # For each time slot, find when the number of users reaches the buffer size
    for slot in time_slots:
        start_time, end_time = slot
        transient_period = None
        max_users = 0
        max_users_time = start_time  # Keep track of the time when max users occur in the slot

        # Loop through the measurements within the time slot
        for time, user_count in zip(times, users):
            if start_time <= time <= end_time:
                # Track the time when the maximum users occurred
                if user_count > max_users:
                    max_users = user_count
                    max_users_time = time

                # If users reach the buffer size, mark this time as the transient period end
                if user_count >= buffer_size:
                    transient_period = time
                    break  # Once buffer size is reached, we exit the loop

        # If we found a transient period, we assume the rest of the time is steady-state
        if transient_period:
            warmup_times.append(transient_period)
            # Add the steady state working slot (from warmup time to end of time slot)
            steady_state_slots.append([transient_period, end_time])
        else:
            # If buffer size is not reached, use the time when the maximum users occurred
            warmup_times.append(max_users_time)
            steady_state_slots.append([max_users_time, end_time])

    # Save the steady-state slots to a JSON file
    steady_state_json_path = "./report_images/steady_state_working_slots.json"
    with open(steady_state_json_path, 'w') as json_file:
        json.dump(steady_state_slots, json_file, indent=4)

    # Return the list of all warmup times (transition points from transient to steady-state)
    return warmup_times


def check_json_file_exists(json_filepath="./report_images/steady_state_working_slots.json"):
    """
    Checks whether the specified JSON file exists.

    :param json_filepath: Path to the JSON file to check.
    :return: True if the file exists, False otherwise.
    """
    return os.path.exists(json_filepath)


def start_working_intervals(simulation_time, working_schedule_lists):
    start_slot = working_schedule_lists[0][0]
    end_slot = working_schedule_lists[0][1]
    start_times = []
    working_interval = 25 * 60
    charging_interval = 60 * 60
    working_cycle = working_interval + charging_interval
    working_slots = int(simulation_time / working_cycle)
    for i in range(working_slots + 1):
        initial_time = working_cycle * i
        if start_slot <= initial_time <= end_slot:
            start_times.append(initial_time)
    # Saves the dictionary in a JSON file
    output_file_path = "./report_images/start_working_intervals.json"
    with open(output_file_path, 'w') as json_file:
        json.dump(start_times, json_file, indent=4)
    return start_times


def save_steady_state_metrics(filtered_measurements):
    """
    Compare overall and steady-state metrics in a dictionary format.

    Args:
        filtered_measurements: The filtered measurements for steady-state data.

    Returns:
        dict: A dictionary containing the steady-state metrics.
    """

    def round_if_number(value):
        """Helper function to round a number to 3 decimal places, or return 'N/A'."""
        if isinstance(value, (int, float)):
            return round(value, 3)
        return value

    # Prepare the steady-state metrics in dictionary format
    steady_state_metrics = {
        'Working Time': round_if_number(filtered_measurements.steady_state_interval),
        'Total Arrivals': round_if_number(filtered_measurements.arrivals),
        'Total Departures': round_if_number(filtered_measurements.departures),
        'Total Losses': round_if_number(filtered_measurements.losses),
        'Arrival Rate': round_if_number(filtered_measurements.arrivals / filtered_measurements.steady_state_interval),
        'Departure Rate': round_if_number(
            filtered_measurements.departures / filtered_measurements.steady_state_interval),
        'Loss Rate': round_if_number(filtered_measurements.losses / filtered_measurements.steady_state_interval),
        'Departures-Losses Ratio': round_if_number(
            filtered_measurements.departures / filtered_measurements.losses
        ) if filtered_measurements.losses > 0 else "N/A",
        'Departures Percentage': round_if_number(
            filtered_measurements.departures / filtered_measurements.arrivals * 100
        ) if filtered_measurements.arrivals > 0 else "N/A",
        'Average Users': round_if_number(
            filtered_measurements.total_users / filtered_measurements.steady_state_interval),
        'Average Delay': round_if_number(
            filtered_measurements.delay / filtered_measurements.departures
        ) if filtered_measurements.departures > 0 else "N/A"
    }

    return steady_state_metrics


def seconds_to_time_string(seconds):
    """
    Converts a given number of seconds from midnight into a time string in the format HH:MM:SS.

    Args:
        seconds (int): The number of seconds since midnight.

    Returns:
        str: The time string in the format HH:MM:SS.
    """
    hours = seconds // 3600  # Calculate the hours
    minutes = (seconds % 3600) // 60  # Calculate minutes
    seconds = seconds % 60  # Calculates seconds remaining

    # Returns the formatted string in the format HH:MM:SS
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def overall_metrics(data, working_time, working_cycles):
    """
    Compare overall and steady-state metrics in a dictionary format.

    Args:
        data: The filtered measurements for steady-state data.

    Returns:
        dict: A dictionary containing the steady-state metrics.
    """

    def round_if_number(value):
        """Helper function to round a number to 3 decimal places, or return 'N/A'."""
        if isinstance(value, (int, float)):
            return round(value, 3)
        return value

    # Prepare the steady-state metrics in dictionary format
    overall_metrics = {
        'Working Time': round_if_number(working_time),
        'Working Cycles': working_cycles,
        'Total Arrivals': round_if_number(data.arrivals),
        'Total Departures': round_if_number(data.departures),
        'Total Losses': round_if_number(data.losses),
        'Arrival Rate': round_if_number(data.arrivals / working_time),
        'Departure Rate': round_if_number(data.departures / working_time),
        'Loss Rate': round_if_number(data.losses / working_time),
        'Departures-Losses Ratio': round_if_number(
            data.departures / data.losses
        ) if data.losses > 0 else "N/A",
        'Departures Percentage': round_if_number(
            data.departures / data.arrivals * 100
        ) if data.arrivals > 0 else "N/A",
        'Average Users': round_if_number(data.total_users / working_time),
        'Average Delay': round_if_number(
            data.delay / data.departures
        ) if data.departures > 0 else "N/A"
    }

    return overall_metrics


def define_working_and_charging_interval(power_supply):

    if power_supply == "BAT":
        working_interval = 25 * 60  # seconds
        charging_interval = 60 * 60  # seconds

    elif power_supply == "W45":
        working_interval = 35 * 60  # seconds
        charging_interval = 60 * 60  # seconds

    elif power_supply == "W65":
        working_interval = 40 * 60  # seconds
        charging_interval = 60 * 60  # seconds

    elif power_supply == "W75":
        working_interval = 45 * 60  # seconds
        charging_interval = 60 * 60  # seconds

    return working_interval, charging_interval


def calculate_working_cycles_per_interval(working_schedule_list, power_supply):

    working_period = working_schedule_list[1] - working_schedule_list[0]
    working_interval, charging_interval = define_working_and_charging_interval(power_supply)

    working_cycle = working_interval + charging_interval
    working_slots = int(working_period / working_cycle)

    res = working_period - working_cycle * working_slots

    if res > 0:
        if int(res / working_interval) > 0:
            working_slots += 1

    return working_slots


def calculate_working_cycles(max_recharges, pow_supply, working_schedule_lists):

    working_slots = 0
    for slot in working_schedule_lists:
        working_slots += calculate_working_cycles_per_interval(slot, pow_supply)

    if isinstance(max_recharges, int):
        if working_slots > max_recharges:
            working_slots = max_recharges

    return working_slots


def working_time_by_schedule_and_recharges(max_recharges, working_schedule_lists, pow_supply):
    working_slots = calculate_working_cycles(max_recharges, pow_supply,working_schedule_lists)
    working_interval, _ = define_working_and_charging_interval(pow_supply)
    return working_slots*working_interval


def sort_and_filter_by_departure_percentage(result_dict):
    """
    Takes a dictionary with simulation results and returns a new dictionary
    sorted by Departure Percentage in descending order, keeping only the Departure Percentage.

    :param result_dict: Dictionary containing simulation results.
    :return: A new dictionary sorted by Departure Percentage in descending order, with only the Departure Percentage as values.
    """
    # Create a sorted list of tuples (key, departure_percentage) based on "Departures Percentage" value
    sorted_tuples = sorted(
        result_dict.items(),
        key=lambda item: item[1]["Departures Percentage"],
        reverse=True
    )

    # Create a new dictionary that keeps only the "Departures Percentage" value
    sorted_filtered_dict = {key: value["Departures Percentage"] for key, value in sorted_tuples}

    return sorted_filtered_dict
