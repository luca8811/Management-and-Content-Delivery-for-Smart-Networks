import random
from queue import PriorityQueue
from scipy.stats import t
import math
import matplotlib.pyplot as plt
from utils.queues import MMmB, Packet
from utils.measurements import Measurement

# Fixed service time
SERVICE = 20.0  # Constant service time for simplicity
# Initialize variables for simulation
BUFFER_SIZE = 0  # No buffer scenario as per Task 1
SERVICE_TIMES = [SERVICE]  # One service unit, fixed service time
SIM_TIME = 500000  # Simulation time in some units
ARRIVAL_RATES = [0.5, 1, 5, 10]  # Arrival rates to be tested
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


def arrival(time, FES, queue: MMmB, arrival_rate, data: Measurement):
    global users
    loss = False
    data.arrivals += 1
    data.average_users += users * (time - data.time) #weighted time
    data.time = time
    try:
        if queue.buffer_size > 0:
            queue.insert(Packet(time))
            users += 1
        else:
            # Directly attempt to process the packet if buffer size is 0
            if queue.can_engage_server():
                queue.insert(Packet(time))
                users += 1
            else:
                loss = True
    except OverflowError:
        loss = True

    if loss:
        data.losses += 1
        data.loss_probability = data.losses / data.arrivals
    else:
        if queue.can_engage_server():
            s_id, _ = queue.engage_server()
            service_time = SERVICE
            FES.put((time + service_time, "departure", s_id)) #set departure event

    inter_arrival = random.expovariate(1.0 / arrival_rate)
    FES.put((time + inter_arrival, "arrival", None))


def departure(time, FES, queue: MMmB, server_id, data: Measurement):
    global users
    if queue.queue_size() > 0:
        client = queue.consume(server_id)
        client.start_service_time = time
        data.departures += 1
        data.transmitted_packets += 1
        data.delay += (time - client.arrival_time)

        if client.start_service_time > client.arrival_time: #packet has waited in the line
            data.waiting_delay += client.start_service_time - client.arrival_time
            data.waiting_delays.append(client.start_service_time - client.arrival_time)
        data.average_users += users * (time - data.time)
        data.time = time
        users -= 1 #descresing the users
        if queue.can_engage_server():
            s_id, _ = queue.engage_server()
            service_time = SERVICE
            FES.put((time + service_time, "departure", s_id))
            data.busy_time += service_time

        # Handle buffer occupancy calculation
        if BUFFER_SIZE > 0:
            data.buffer_occupancy = users / BUFFER_SIZE
        else:
            data.buffer_occupancy = 0  # If buffer size is 0, set occupancy to 0
    else:
        queue._servers[server_id].release()  # Release the server if no packets are left in the queue (become avaiable)


if __name__ == '__main__':
    random.seed(42)
    results = []
    delays = []
    loss_rates = []
    average_users_list = []

    for ARRIVAL in ARRIVAL_RATES:
        data = Measurement()  # Usa la classe Measurement
        FES = PriorityQueue()
        FES.put((0, "arrival", None))
        MMm = MMmB(power_supply="INF", service_times=SERVICE_TIMES, buffer_size=BUFFER_SIZE)  # Modifica qui
        users = 0
        time = 0
        while not FES.empty() and time < SIM_TIME:
            time, event_type, server_id = FES.get()
            if event_type == "arrival":
                arrival(time, FES, MMm, ARRIVAL, data)
            elif event_type == "departure":
                departure(time, FES, MMm, server_id, data)
        average_delay = data.delay / data.departures if data.departures > 0 else 0
        results.append(
            f"Arrival Rate {ARRIVAL}: Users in queue: {users}, Arrivals: {data.arrivals}, Departures: {data.departures}, Avg Users: {data.average_users / time if time > 0 else 'No time passed'}, Avg Delay: {average_delay}, Loss Rate: {data.loss_probability if data.arrivals > 0 else 'No arrivals'}, Avg Waiting Delay: {data.waiting_delay / data.departures if data.departures > 0 else 0}, Avg Buffer Occupancy: {data.buffer_occupancy}, Busy Time: {data.busy_time}")
        delays.append(average_delay)
        loss_rates.append(data.loss_probability if data.arrivals > 0 else 0)
        average_users_list.append(data.average_users / time if time > 0 else 0)

    ci_lower, ci_upper = compute_t_confidence_interval(delays, CONFIDENCE_LEVEL)
    results.append(
        f"Confidence Interval for Average Delays at {CONFIDENCE_LEVEL * 100}% Confidence Level: ({ci_lower}, {ci_upper})")

    for result in results:
        print(result)

    # Grafici

    # Grafico 1: Tasso di perdita vs Tasso di arrivo
    plt.figure()
    plt.plot(ARRIVAL_RATES, loss_rates, marker='o', linestyle='-', color='r')
    plt.title('Loss Rate vs Arrival Rate')
    plt.xlabel('Arrival Rate (packets per time unit)')
    plt.ylabel('Loss Rate')
    plt.grid(True)
    plt.show()

    # Grafico 2: Ritardo medio vs Tasso di arrivo
    plt.figure()
    plt.plot(ARRIVAL_RATES, delays, marker='o', linestyle='-', color='b')
    plt.title('Average Delay vs Arrival Rate')
    plt.xlabel('Arrival Rate (packets per time unit)')
    plt.ylabel('Average Delay (time units)')
    plt.grid(True)
    plt.show()

    # Grafico 3: Numero medio di utenti nel sistema vs Tasso di arrivo
    plt.figure()
    plt.plot(ARRIVAL_RATES, average_users_list, marker='o', linestyle='-', color='g')
    plt.title('Average Users in System vs Arrival Rate')
    plt.xlabel('Arrival Rate (packets per time unit)')
    plt.ylabel('Average Users')
    plt.grid(True)
    plt.show()

    # Grafico 4: Intervallo di confidenza per il Ritardo medio
    plt.figure()
    plt.errorbar(ARRIVAL_RATES, delays, yerr=[ci_upper - delays[0]] * len(ARRIVAL_RATES), fmt='o', color='purple')
    plt.title('Confidence Interval for Average Delay')
    plt.xlabel('Arrival Rate (packets per time unit)')
    plt.ylabel('Average Delay (with 95% CI)')
    plt.grid(True)
    plt.show()
