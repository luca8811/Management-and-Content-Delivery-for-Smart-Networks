import random
from queue import PriorityQueue
from scipy.stats import t
import math
from queues import MMmB, Client

# Measure class to track metrics
class Measure:
    def __init__(self):
        self.arr = 0  # Number of arrivals
        self.dep = 0  # Number of departures
        self.los = 0  # Number of lost packets
        self.ut = 0  # Time-weighted number of users in the system
        self.oldT = 0  # Previous event time
        self.delay = 0  # Total delay
        self.transmitted_packets = 0  # Number of transmitted packets
        self.average_packets = 0  # Sum of packets in the system for calculating average
        self.queue_delay = 0  # Total queue delay
        self.waiting_delay = 0  # Total waiting delay
        self.buffer_occupancy = 0  # Average buffer occupancy
        self.loss_probability = 0  # Loss probability
        self.busy_time = 0  # Total busy time of the server
        self.queue_delays = []  # List of individual queue delays for distribution
        self.waiting_delays = []  # List of individual waiting delays for distribution
        self.time_series = []  # Time series data for further analysis

# Fixed service time
SERVICE = 20.0  # Constant service time for simplicity
# Initialize variables for simulation
BUFFER_SIZE = 300
SERVICE_TIMES = [SERVICE]  # One service unit, fixed service time
SIM_TIME = 500000  # Simulation time in some units
ARRIVAL_RATES = [0.5, 0.75, 1, 1.5, 2]  # Lower arrival rates to be tested
CONFIDENCE_LEVEL = 0.95  # Desired confidence level

def compute_t_confidence_interval(sample, confidence_level):
    """
    Compute the t-distribution based confidence interval for a sample using scipy.stats.
    """
    sample_size = len(sample)
    if sample_size < 2:
        raise ValueError("Sample size must be greater than one for confidence interval calculation.")

    sample_mean = sum(sample) / sample_size
    sample_std_dev = math.sqrt(sum((x - sample_mean) ** 2 for x in sample) / (sample_size - 1))
    standard_error = sample_std_dev / math.sqrt(sample_size)

    # Degrees of freedom
    degrees_of_freedom = sample_size - 1

    # Calculate the t-distribution based confidence interval
    confidence_interval = t.interval(confidence_level, degrees_of_freedom, sample_mean, standard_error)

    return confidence_interval

def arrival(time, FES, queue: MMmB, arrival_rate, data):
    global users
    loss = queue.is_queue_full()
    data.arr += 1
    data.ut += users * (time - data.oldT)
    data.oldT = time
    if loss:
        data.los += 1
        data.loss_probability = data.los / data.arr
    else:
        users += 1
        client = Client(1, time)
        queue.insert(client)
    inter_arrival = random.expovariate(1.0 / arrival_rate)
    FES.put((time + inter_arrival, "arrival", None))
    if queue.can_engage_server():
        s_id, _ = queue.engage_server()
        service_time = SERVICE  # Use the fixed service time
        FES.put((time + service_time, "departure", s_id))

def departure(time, FES, queue: MMmB, server_id, data):
    global users
    client = queue.consume(server_id)
    client.start_service_time = time
    data.dep += 1
    data.transmitted_packets += 1
    data.delay += (time - client.arrival_time)
    data.queue_delay += (time - client.arrival_time)
    data.queue_delays.append(time - client.arrival_time)
    if client.start_service_time > client.arrival_time:
        data.waiting_delay += client.start_service_time - client.arrival_time
        data.waiting_delays.append(client.start_service_time - client.arrival_time)
    data.ut += users * (time - data.oldT)
    data.oldT = time
    users -= 1
    if queue.can_engage_server():
        s_id, _ = queue.engage_server()
        service_time = SERVICE  # Use the fixed service time
        FES.put((time + service_time, "departure", s_id))
        data.busy_time += service_time
    data.buffer_occupancy = users / BUFFER_SIZE

if __name__ == '__main__':
    random.seed(42)
    results = []
    delays = []
    for ARRIVAL in ARRIVAL_RATES:
        data = Measure()
        FES = PriorityQueue()
        FES.put((0, "arrival", None))
        MMm = MMmB(service_times=SERVICE_TIMES, buffer_size=BUFFER_SIZE)
        users = 0
        time = 0
        while not FES.empty() and time < SIM_TIME:
            time, event_type, server_id = FES.get()
            if event_type == "arrival":
                arrival(time, FES, MMm, ARRIVAL, data)
            elif event_type == "departure":
                departure(time, FES, MMm, server_id, data)
        average_delay = data.delay / data.dep if data.dep > 0 else 0
        results.append(f"Arrival Rate {ARRIVAL}: Users in queue: {users}, Arrivals: {data.arr}, Departures: {data.dep}, Avg Users: {data.ut / time if time > 0 else 'No time passed'}, Avg Delay: {average_delay}, Loss Rate: {data.loss_probability if data.arr > 0 else 'No arrivals'}, Avg Waiting Delay: {data.waiting_delay / data.dep if data.dep > 0 else 0}, Avg Buffer Occupancy: {data.buffer_occupancy}, Busy Time: {data.busy_time}")
        delays.append(average_delay)
    ci_lower, ci_upper = compute_t_confidence_interval(delays, CONFIDENCE_LEVEL)
    results.append(f"Confidence Interval for Average Delays at {CONFIDENCE_LEVEL*100}% Confidence Level: ({ci_lower}, {ci_upper})")
    for result in results:
        print(result)
