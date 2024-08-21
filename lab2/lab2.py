import json
import random
from queue import PriorityQueue
from utils.queues import MMmB, Client, BatteryStatus, Battery
from utils.measurements import Statistics, Measurements
from enum import Enum
import arrivals_profile
import results_visualization

# LEGEND:
#   - FES: Finite Event Schedule

task = "TASK1"
with open('variables.json') as f:
    variables = json.load(f)[task]


class Event(Enum):
    ARRIVAL = 1
    DEPARTURE = 2
    SWITCH_OFF = 3
    RECHARGE = 4


users = 0
MMms = {}
for i, drone in enumerate(variables['drones']):
    # TODO: service times, no list
    MMms[i] = MMmB(type=drone['TYPE'],
                   service_times=[1 / drone['SERVICE_RATE'] for m in range(drone['m_ANTENNAS'])],
                   buffer_size=variables['BUFFER_SIZE'])


def resolve_MMm():
    return random.choice(list(MMms.keys()))


# This function schedules the battery consumption of a drone. If 'tot_time' is set to 0, the maximum will be set
def send_drone(time, FES: PriorityQueue, drone_id, desired_time=0):
    queue = MMms[drone_id]
    # checking if battery is full, and managing the case of an eventual solar panel equipped
    if queue.battery.status == BatteryStatus.FULL:
        queue.battery.status = BatteryStatus.IN_USE
        queue.battery.init_battery(8 * 3600 <= time <= 16 * 3600)
    if desired_time == 0:
        tot_time = queue.battery.residual
    else:
        tot_time = min(desired_time, queue.battery.residual)
    FES.put((time + tot_time, Event.SWITCH_OFF, drone_id, tot_time))


def schedule_recharge(time, FES: PriorityQueue, drone_id):
    FES.put((time + Battery.RECHARGE_TIME, Event.RECHARGE, drone_id, None))


def evt_switch_off(time, FES: PriorityQueue, drone_id, tot_time):
    queue = MMms[drone_id]
    queue.battery.residual -= tot_time
    if queue.battery.residual == 0:
        queue.battery.status = BatteryStatus.EMPTY
        queue.queue_clear()
        schedule_recharge(time, FES, drone_id)


def evt_recharge(time, FES: PriorityQueue, drone_id):
    queue = MMms[drone_id]
    queue.battery.complete_cycles += 1
    queue.battery.status = BatteryStatus.FULL
    # TODO: send again? for how much time
    send_drone(time, FES, drone_id)


def evt_arrival(time, FES, drone_id):
    global users

    # print("Arrival no. ",data.arr+1," at time ",time," with ",users," users" )

    # drone scheduled to process service
    drone = MMms[drone_id]

    # loss management - boolean result
    loss = drone.is_queue_full() or drone.battery.status != BatteryStatus.IN_USE
    if loss:
        data.los += 1
    else:
        users += 1
        # create a record for the client
        client = Client(drone.type, time)
        # insert the record in the queue
        drone.insert(client)

    # cumulate statistics
    data.arr += 1
    data.ut += users * (time - data.oldT)  # average users per time unit
    data.oldT = time
    # measurements
    measurements.add_record(time=time,
                            users=users,
                            arrivals=data.arr,
                            departures=data.dep,
                            losses=data.los,
                            delay=data.delay)

    # sample the time until the next event
    # inter_arrival = random.expovariate(lambd=1.0 / ARRIVAL)
    inter_arrival = random.expovariate(
        lambd=variables['ARRIVAL_RATE'] * arrivals_profile.arrivals_profile[int(time / 3600)])

    # schedule the next arrival
    FES.put((time + inter_arrival, Event.ARRIVAL, resolve_MMm(), None))

    # if the server is idle start the service
    if drone.can_engage_server():
        (s_id, s_service_time) = drone.engage_server()
        # sample the service time
        service_time = random.expovariate(1.0 / s_service_time)
        # service_time = 1 + random.uniform(0, SERVICE_TIME)

        # schedule when the client will finish the service
        FES.put((time + service_time, Event.DEPARTURE, drone_id, s_id))


def evt_departure(time, FES, drone_id, server_id):
    global users

    # print("Departure no. ",data.dep+1," at time ",time," with ",users," users" )

    # drone scheduled
    queue = MMms[drone_id]

    # losses management
    loss = queue.battery.status != BatteryStatus.IN_USE
    if loss:
        data.los += 1
    else:
        data.dep += 1
        # get the first element from the queue
        client = queue.consume(server_id)

        # do whatever we need to do when clients go away

        data.delay += (time - client.arrival_time)
        users -= 1

        # see whether there are more clients to in the line
        if queue.can_engage_server():
            (s_id, s_service_time) = queue.engage_server()
            # sample the service time
            service_time = random.expovariate(1.0 / s_service_time)

            # schedule when the client will finish the service
            FES.put((time + service_time, Event.DEPARTURE, drone_id, s_id))
    # cumulate statistics
    data.ut += users * (time - data.oldT)
    data.oldT = time
    # measurements
    measurements.add_record(time=time,
                            users=users,
                            arrivals=data.arr,
                            departures=data.dep,
                            losses=data.los,
                            delay=data.delay)


if __name__ == '__main__':
    random.seed(42)

    data = Statistics(0, 0, 0, 0, 0, 0)
    measurements = Measurements()

    # the simulation time
    time = 0

    # the list of events in the form: (time, evt_type, drone_id, ???)
    FES = PriorityQueue()

    # just to initialize the drones parameters
    for drone_id in range(len(MMms)):
        send_drone(time, FES, drone_id)
    # schedule the first arrival at t=0. resolve_MMm is used to assign
    # a drone which will process the first arrival
    FES.put((0, Event.ARRIVAL, resolve_MMm(), None))

    # simulate until the simulated time reaches a constant
    while time < variables['SIM_TIME']:
        (time, event_type, drone_id, arg) = FES.get()

        if event_type == Event.ARRIVAL:
            evt_arrival(time, FES, drone_id)
        elif event_type == Event.DEPARTURE:
            evt_departure(time, FES, drone_id, arg)
        elif event_type == Event.SWITCH_OFF:
            evt_switch_off(time, FES, drone_id, arg)
        elif event_type == Event.RECHARGE:
            evt_recharge(time, FES, drone_id)
    results_visualization.STARTING_TIME = variables['STARTING_TIME']
    results_visualization.plot_users(measurements)
    results_visualization.plot_arrivals(measurements)
    results_visualization.plot_departures(measurements)
    results_visualization.plot_losses(measurements)
    results_visualization.plot_delay(measurements)

    # print output data
    print("MEASUREMENTS \n\nNo. of users in the queue:", users, "\nNo. of arrivals =",
          data.arr, "- No. of departures =", data.dep)

    print("\nArrival rate: ", data.arr / time, " - Departure rate: ", data.dep / time)
    print("Loss rate: ", data.los / time, " - Packets loss: ", data.los)

    print("\nAverage number of users: ", data.ut / time)

    print("Average delay: ", data.delay / data.dep)
    # print("Actual queue size: ", MMm.queue_size())

    # if MMm.queue_size() > 0:
    #     print("Arrival time of the last element in the queue:", MMm.get_last().arrival_time)
