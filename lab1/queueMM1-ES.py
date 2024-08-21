import random
from queue import PriorityQueue
from utils.queues import MMmB, Packet
from utils.measurements import Statistics

SERVICE = 20.0  # SERVICE is the average service time; service rate = 1/SERVICE
ARRIVAL = 1.0  # ARRIVAL is the average inter-arrival time; arrival rate = 1/ARRIVAL
BUFFER_SIZE = 100  # Infinite buffer -> 0
SERVICE_TIMES = [SERVICE]
N_DRONES = 2

TYPE1 = 1

SIM_TIME = 500000

arrivals = 0
users = 0

MMm = MMmB(service_times=SERVICE_TIMES, buffer_size=BUFFER_SIZE)


def arrival(time, FES, queue: MMmB):
    global users

    # print("Arrival no. ",data.arr+1," at time ",time," with ",users," users" )

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
        packet = Packet(arrival_time=time)
        # insert the record in the queue
        queue.insert(packet)

    # sample the time until the next event
    inter_arrival = random.expovariate(lambd=1.0 / ARRIVAL)

    # schedule the next arrival
    FES.put((time + inter_arrival, "arrival", None))

    # if the server is idle start the service
    if queue.can_engage_server():
        (s_id, s_service_time) = queue.engage_server()
        # sample the service time
        service_time = random.expovariate(1.0 / s_service_time)
        # service_time = 1 + random.uniform(0, SEVICE_TIME)

        # schedule when the client will finish the service
        FES.put((time + service_time, "departure", s_id))


def departure(time, FES, queue: MMmB, server_id):
    global users

    # print("Departure no. ",data.dep+1," at time ",time," with ",users," users" )

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
        FES.put((time + service_time, "departure", s_id))


if __name__ == '__main__':
    random.seed(42)

    data = Statistics(0, 0, 0, 0, 0, 0)

    # the simulation time
    time = 0

    # the list of events in the form: (time, type)
    FES = PriorityQueue()

    # schedule the first arrival at t=0
    FES.put((0, "arrival", None))

    # simulate until the simulated time reaches a constant
    while time < SIM_TIME:
        (time, event_type, server_id) = FES.get()

        if event_type == "arrival":
            arrival(time, FES, MMm)

        elif event_type == "departure":
            departure(time, FES, MMm, server_id)

    # print output data
    print("MEASUREMENTS \n\nNo. of users in the queue:", users, "\nNo. of arrivals =",
          data.arr, "- No. of departures =", data.dep)

    print("Load: ", SERVICE / ARRIVAL)
    print("\nArrival rate: ", data.arr / time, " - Departure rate: ", data.dep / time)
    print("Loss rate: ", data.los / time, " - Packets loss: ", data.los)

    print("\nAverage number of users: ", data.ut / time)

    print("Average delay: ", data.delay / data.dep)
    print("Actual queue size: ", MMm.queue_size())

    if MMm.queue_size() > 0:
        print("Arrival time of the last element in the queue:", MMm.get_last().arrival_time)
