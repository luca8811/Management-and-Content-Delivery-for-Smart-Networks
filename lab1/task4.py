import random
import simpy
import matplotlib.pyplot as plt

# Constants
SERVICE = 10.0  # Average service time
ARRIVAL = 5.0  # Average inter-arrival time
SIM_TIME = 500000
TYPE1 = 1
BUFFER_SIZE = float('inf')  # Use float('inf') for an unlimited buffer


# Measurement class
class Measure:
    def __init__(self):
        self.arr = 0
        self.dep = 0
        self.los = 0
        self.ut = 0
        self.oldT = 0
        self.delay = 0
        self.transmitted_packets = 0
        self.average_packets = 0
        self.queue_delay = 0
        self.waiting_delay = 0
        self.buffer_occupancy = 0
        self.loss_probability = 0
        self.busy_time = 0
        self.queue_delays = []
        self.waiting_delays = []


# Client class
class Client:
    def __init__(self, Type, ArrivalT):
        self.type = Type
        self.Tarr = ArrivalT
        self.start_service_time = 0


# Arrival process
def arrival_process(env, queue, service_dist, data):
    while True:
        inter_arrival = random.expovariate(1.0 / ARRIVAL)
        yield env.timeout(inter_arrival)
        client = Client(TYPE1, env.now)
        data.arr += 1

        if len(queue) < BUFFER_SIZE:
            queue.append(client)
            data.ut += len(queue) * (env.now - data.oldT)
            data.buffer_occupancy += len(queue)
            data.average_packets += len(queue)
            data.oldT = env.now

            if len(queue) == 1:
                service_time = service_dist()
                env.process(departure_process(env, service_time, queue, data, service_dist))
        else:
            data.los += 1


# Departure process
def departure_process(env, service_time, queue, data, service_dist):
    client = queue[0]
    client.start_service_time = env.now
    data.busy_time += service_time
    yield env.timeout(service_time)
    data.dep += 1
    data.transmitted_packets += 1
    data.delay += env.now - client.Tarr
    data.queue_delay += env.now - client.Tarr
    data.queue_delays.append(env.now - client.Tarr)
    if client.start_service_time > client.Tarr:
        data.waiting_delay += client.start_service_time - client.Tarr
        data.waiting_delays.append(client.start_service_time - client.Tarr)
    data.ut += len(queue) * (env.now - data.oldT)
    data.oldT = env.now
    queue.pop(0)

    if len(queue) > 0:
        service_time = service_dist()
        env.process(departure_process(env, service_time, queue, data, service_dist))


# Service time distributions
def uniform_service_time():
    return random.uniform(5, 15)


def normal_service_time():
    return max(0, random.normalvariate(10, 2))


def constant_service_time():
    return 10


# Run the simulation
def run_simulation(service_dist):
    env = simpy.Environment()
    data = Measure()
    queue = []
    env.process(arrival_process(env, queue, service_dist, data))
    env.run(until=SIM_TIME)
    return data  # Return data


# Main execution
service_distributions = [uniform_service_time, normal_service_time, constant_service_time]
results = {}

for service_dist in service_distributions:
    data = run_simulation(service_dist)
    results[service_dist.__name__] = data
    print(f"Results with {service_dist.__name__}:")
    print(f"  Average number of users: {data.ut / SIM_TIME}")
    print(f"  Average delay: {data.delay / data.dep if data.dep > 0 else 0}")
    print(f"  Busy time: {data.busy_time / SIM_TIME}")
    print(f"  Average queue length: {data.average_packets / SIM_TIME}")
    print(f"  Loss probability: {data.los / data.arr if data.arr > 0 else 0}")
    print(f"  Number of transmitted packets: {data.transmitted_packets}")
    print(f"  Average queuing delay: {data.queue_delay / data.dep if data.dep > 0 else 0}")
    print(f"  Average waiting delay: {data.waiting_delay / data.dep if data.dep > 0 else 0}")
    print(f"  Average buffer occupancy: {data.buffer_occupancy / SIM_TIME}")