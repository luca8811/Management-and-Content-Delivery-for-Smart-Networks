import random
from queue import PriorityQueue
from utils.queues import MMmB, Client, BatteryStatus, Battery
from utils.measurements import Statistics, Measurements
from enum import Enum
import matplotlib.pyplot as plt


class Event(Enum):
    ARRIVAL = 1
    DEPARTURE = 2
    SWITCH_OFF = 3
    RECHARGE = 4


SERVICE_RATE = 100
ARRIVAL_RATE = 100
SERVICE = 1 / SERVICE_RATE  # SERVICE is the average service time; service rate = 1/SERVICE
ARRIVAL = 1 / ARRIVAL_RATE  # ARRIVAL is the average inter-arrival time; arrival rate = 1/ARRIVAL
BUFFER_SIZE = 300  # Infinite buffer -> 0
m_ANTENNAS = 2
N_DRONES = 1
SERVICE_TIMES = [SERVICE for i in range(m_ANTENNAS)]
# SERVICE_TIMES = [SERVICE, SERVICE / 2]

TYPE1 = 1

# time unit: seconds
SIM_TIME = 43200  # 12 hours

users = 0
MMms = {i: MMmB(service_times=SERVICE_TIMES, buffer_size=BUFFER_SIZE) for i in range(N_DRONES)}


def resolve_MMm():
    return random.choice(list(MMms.keys()))


# This function schedules the battery consumption of a drone. If 'tot_time' is set to 0, the maximum will be set
def send_drone(time, FES: PriorityQueue, queue_id, desired_time=0):
    queue = MMms[queue_id]
    # checking if battery is full, and managing the case of an eventual solar panel equipped
    if queue.battery.status == BatteryStatus.FULL:
        queue.battery.status = BatteryStatus.IN_USE
        queue.battery.residual = queue.battery.max_residual_time
    if desired_time == 0:
        tot_time = queue.battery.residual
    else:
        tot_time = min(desired_time, queue.battery.residual)
    FES.put((time + tot_time, Event.SWITCH_OFF, queue_id, tot_time))


def schedule_recharge(time, FES: PriorityQueue, queue_id):
    FES.put((time + Battery.RECHARGE_TIME, Event.RECHARGE, queue_id, None))


def evt_switch_off(time, FES: PriorityQueue, queue_id, tot_time):
    queue = MMms[queue_id]
    queue.battery.residual -= tot_time
    if queue.battery.residual == 0:
        queue.battery.status = BatteryStatus.EMPTY
        queue.queue_clear()
        schedule_recharge(time, FES, queue_id)


def evt_recharge(time, FES: PriorityQueue, queue_id):
    queue = MMms[queue_id]
    queue.battery.complete_cycles += 1
    queue.battery.status = BatteryStatus.FULL
    # TODO: send again? for how much time
    send_drone(time, FES, queue_id)


def evt_arrival(time, FES, queue_id):
    global users

    # print("Arrival no. ",data.arr+1," at time ",time," with ",users," users" )

    # drone scheduled to process service
    queue = MMms[queue_id]

    # loss management
    loss = queue.is_queue_full() or queue.battery.status != BatteryStatus.IN_USE
    if loss:
        data.los += 1
    else:
        users += 1
        # create a record for the client
        client = Client(TYPE1, time)
        # insert the record in the queue
        queue.insert(client)

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
    inter_arrival = random.expovariate(lambd=1.0 / ARRIVAL)

    # schedule the next arrival
    FES.put((time + inter_arrival, Event.ARRIVAL, resolve_MMm(), None))

    # if the server is idle start the service
    if queue.can_engage_server():
        (s_id, s_service_time) = queue.engage_server()
        # sample the service time
        service_time = random.expovariate(1.0 / s_service_time)
        # service_time = 1 + random.uniform(0, SERVICE_TIME)

        # schedule when the client will finish the service
        FES.put((time + service_time, Event.DEPARTURE, queue_id, s_id))


def evt_departure(time, FES, queue_id, server_id):
    global users

    # print("Departure no. ",data.dep+1," at time ",time," with ",users," users" )

    # drone scheduled
    queue = MMms[queue_id]

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
            FES.put((time + service_time, Event.DEPARTURE, queue_id, s_id))
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


def plot_users(measurements: Measurements):
    plt.figure()
    times, users_count = measurements.dispatch_users(starting_time)
    plt.plot(times, users_count)
    plt.xlabel('time')
    plt.ylabel('number of users')
    plt.grid()
    plt.title('Users over time')
    plt.show()


def plot_arrivals(measurements: Measurements):
    plt.figure()
    times, arrivals_count = measurements.dispatch_arrivals(starting_time)
    plt.plot(times, arrivals_count)
    plt.xlabel('time (hours)')
    plt.ylabel('number of arrivals')
    plt.grid()
    plt.title('Arrivals over time')
    plt.show()


def plot_departures(measurements: Measurements):
    plt.figure()
    times, departures_count = measurements.dispatch_departures(starting_time)
    plt.plot(times, departures_count)
    plt.xlabel('time (hours)')
    plt.ylabel('number of departures')
    plt.grid()
    plt.title('Departures over time')
    plt.show()


def plot_losses(measurements: Measurements):
    plt.figure()
    times, losses_count = measurements.dispatch_losses(starting_time)
    plt.plot(times, losses_count)
    plt.xlabel('time (hours)')
    plt.ylabel('number of losses')
    plt.grid()
    plt.title('Losses over time')
    plt.show()


def plot_delay(measurements: Measurements):
    plt.figure()
    times, delay_count = measurements.dispatch_delay(starting_time)
    plt.plot(times, delay_count)
    plt.xlabel('time (hours)')
    plt.ylabel('delay (units)')
    plt.grid()
    plt.title('Delay over time')
    plt.show()


if __name__ == '__main__':
    random.seed(42)

    data = Statistics(0, 0, 0, 0, 0, 0)
    measurements = Measurements()

    # the simulation time
    starting_time = 8 * 3600
    time = 0

    # the list of events in the form: (time, type)
    FES = PriorityQueue()

    # schedule the first arrival at t=0
    for queue_id in range(len(MMms)):
        send_drone(time, FES, queue_id)
    FES.put((0, Event.ARRIVAL, resolve_MMm(), None))

    # simulate until the simulated time reaches a constant
    while time < SIM_TIME:
        (time, event_type, queue_id, arg) = FES.get()

        if event_type == Event.ARRIVAL:
            evt_arrival(time, FES, queue_id)
        elif event_type == Event.DEPARTURE:
            evt_departure(time, FES, queue_id, arg)
        elif event_type == Event.SWITCH_OFF:
            evt_switch_off(time, FES, queue_id, arg)
        elif event_type == Event.RECHARGE:
            evt_recharge(time, FES, queue_id)
    plot_users(measurements)
    plot_arrivals(measurements)
    plot_departures(measurements)
    plot_losses(measurements)
    plot_delay(measurements)

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
