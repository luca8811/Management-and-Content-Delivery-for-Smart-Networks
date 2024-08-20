import random
from queue import PriorityQueue
from queues import MMmB, Client
from measurements import Measure

SERVICE = 20.0  # SERVICE is the average service time; service rate = 1/SERVICE
ARRIVAL = 3.0  # ARRIVAL is the average inter-arrival time; arrival rate = 1/ARRIVAL
BUFFER_SIZE = 300  # Infinite buffer -> 0
m_ANTENNAS = 2
N_DRONES = 1
SERVICE_TIMES = [SERVICE for i in range(m_ANTENNAS)]
# SERVICE_TIMES = [SERVICE, SERVICE / 2]

TYPE1 = 1

SIM_TIME = 500000

arrivals = 0
users = 0

MMms = {i: MMmB(service_times=SERVICE_TIMES, buffer_size=BUFFER_SIZE) for i in range(N_DRONES)}


def resolve_MMm():
    return random.choice(list(MMms.keys()))


def arrival(time, FES, queue_id):
    global users

    # print("Arrival no. ",data.arr+1," at time ",time," with ",users," users" )

    queue = MMms[queue_id]
    # loss detection
    loss = queue.is_queue_full()

    # cumulate statistics
    data.arr += 1
    data.ut += users * (time - data.oldT)  # average users per time unit
    data.oldT = time
    if loss:
        data.los += 1
    else:
        users += 1
        # create a record for the client
        client = Client(TYPE1, time)
        # insert the record in the queue
        queue.insert(client)

    # sample the time until the next event
    inter_arrival = random.expovariate(lambd=1.0 / ARRIVAL)

    # schedule the next arrival
    FES.put((time + inter_arrival, "arrival", resolve_MMm(), None))

    # if the server is idle start the service
    if queue.can_engage_server():
        (s_id, s_service_time) = queue.engage_server()
        # sample the service time
        service_time = random.expovariate(1.0 / s_service_time)
        # service_time = 1 + random.uniform(0, SEVICE_TIME)

        # schedule when the client will finish the service
        FES.put((time + service_time, "departure", queue_id, s_id))


def departure(time, FES, queue_id, server_id):
    global users

    # print("Departure no. ",data.dep+1," at time ",time," with ",users," users" )

    queue = MMms[queue_id]
    # get the first element from the queue
    client = queue.consume(server_id)

    # cumulate statistics
    data.dep += 1
    data.ut += users * (time - data.oldT)
    data.oldT = time

    # do whatever we need to do when clients go away

    data.delay += (time - client.arrival_time)
    users -= 1

    # see whether there are more clients to in the line
    if queue.can_engage_server():
        (s_id, s_service_time) = queue.engage_server()
        # sample the service time
        service_time = random.expovariate(1.0 / s_service_time)

        # schedule when the client will finish the service
        FES.put((time + service_time, "departure", queue_id, s_id))


if __name__ == '__main__':
    random.seed(42)

    data = Measure(0, 0, 0, 0, 0, 0)

    # the simulation time
    time = 0

    # the list of events in the form: (time, type)
    FES = PriorityQueue()

    # schedule the first arrival at t=0
    FES.put((0, "arrival", resolve_MMm(), None))

    # simulate until the simulated time reaches a constant
    while time < SIM_TIME:
        (time, event_type, queue_id, server_id) = FES.get()

        if event_type == "arrival":
            arrival(time, FES, queue_id)

        elif event_type == "departure":
            departure(time, FES, queue_id, server_id)

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