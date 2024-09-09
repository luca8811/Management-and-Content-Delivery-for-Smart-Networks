import json
import random
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


def assign_packet_to_drone():
    """
    When a packet arrives, we want it to be assigned to a running drone.
    It returns the id of the fastest (highest capacity) drone, if any
    available (running and with space inside its queue).
    """

    def is_available(drone: tuple[int, MMms]):
        return drone[1].battery.status == BatteryStatus.IN_USE and not drone[1].is_queue_full()

    drones = list(filter(is_available, MMms.items()))
    if len(drones) > 0:
        drones = sorted(drones, key=lambda drone: drone[1].get_capacity(), reverse=True)
        return drones[0][0]
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

    def is_available(drone: tuple[int, MMms]):
        return drone[1].battery.status in [BatteryStatus.PAUSED, BatteryStatus.FULL]

    drones = list(filter(is_available, MMms.items()))
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
    drone_id = assign_packet_to_drone()
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
    else:
        data.departures += 1
        # get the first element from the queue
        client = drone.consume(server_id)

        # do whatever we need to do when clients go away

        data.delay += (time - client.arrival_time)
        data.users -= 1

        # see whether there are more clients to in the line
        if drone.can_engage_server():
            (s_id, s_service_time) = drone.engage_server()
            # sample the service time
            service_time = random.expovariate(1.0 / s_service_time)

            # schedule when the client will finish the service
            FES.put((time + service_time, Event.DEPARTURE, drone_id, s_id))

    # cumulate statistics
    data.average_users += data.users * (time - data.time)
    data.time = time
    data.average_delay = data.delay / data.departures
    # measurements
    measurements.add_measurement(measurement=data)
