import random
from queue import PriorityQueue
import math
import matplotlib.pyplot as plt
from utils.queues import MMmB, Packet
from utils.measurements import Measurement

# Simulation Parameters
SERVICE = 1.0  # Average service time (reasonable time units)
BUFFER_SIZE = 10  # Buffer size (number of packets)
SERVICE_TIMES = [SERVICE]
SIM_TIME = 50000  # Total simulation time (reduced for faster execution)
ARRIVAL_RATE = 0.9  # Single arrival rate to test


# Function to generate service time based on the chosen distribution
def generate_service_time(distribution="exponential", service_mean=SERVICE):
    if distribution == "exponential":
        return random.expovariate(1.0 / service_mean)  # Exponential distribution
    elif distribution == "uniform":
        return random.uniform(service_mean * 0.5, service_mean * 1.5)  # Uniform distribution
    elif distribution == "normal":
        return max(0.0, random.gauss(service_mean, service_mean * 0.2))  # Normal (Gaussian) distribution
    elif distribution == "gamma":
        shape = 2.0  # Shape parameter (k)
        scale = service_mean / shape  # Mean = shape * scale
        return random.gammavariate(shape, scale)  # Gamma distribution
    else:
        raise ValueError(f"Distribution '{distribution}' is not supported.")


# Function to handle arrival events
def arrival(time, FES, queue: MMmB, arrival_rate, data: Measurement, distribution="exponential"):
    global users
    loss = False
    data.arrivals += 1
    data.average_users += users * (time - data.time)  # Weighted time
    data.time = time
    try:
        if queue.buffer_size > 0:
            queue.insert(Packet(time))
            users += 1
        else:
            # Attempt to process the packet directly if buffer is 0
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
            service_time = generate_service_time(distribution)  # Generate service time with chosen distribution
            FES.put((time + service_time, "departure", s_id))  # Departure event

    inter_arrival = random.expovariate(arrival_rate)
    FES.put((time + inter_arrival, "arrival", None))


# Function to handle departure events
def departure(time, FES, queue: MMmB, server_id, data: Measurement, distribution="exponential"):
    global users
    if queue.queue_size() > 0:
        client = queue.consume(server_id)
        client.start_service_time = time
        data.departures += 1
        data.transmitted_packets += 1
        data.delay += (time - client.arrival_time)

        if client.start_service_time > client.arrival_time:  # Packet waited in queue
            data.waiting_delay += client.start_service_time - client.arrival_time
            data.waiting_delays.append(client.start_service_time - client.arrival_time)
        data.average_users += users * (time - data.time)
        data.time = time
        users -= 1  # Decrement the number of users
        if queue.can_engage_server():
            s_id, _ = queue.engage_server()
            service_time = generate_service_time(distribution)  # Generate service time with chosen distribution
            FES.put((time + service_time, "departure", s_id))
            data.busy_time += service_time

        # Calculate buffer occupancy
        if BUFFER_SIZE > 0:
            data.buffer_occupancy = users / BUFFER_SIZE
        else:
            data.buffer_occupancy = 0  # If buffer is 0, occupancy is 0
    else:
        queue._servers[server_id].release()  # Release the server if there are no packets in queue


if __name__ == '__main__':
    service_distributions = ["exponential", "uniform", "normal", "gamma"]  # Different service distributions to test
    ARRIVAL = ARRIVAL_RATE

    # Lists to store the results for each distribution
    avg_users = []
    avg_delay = []
    loss_probability = []
    busy_time_ratio = []

    for service_distribution in service_distributions:
        random.seed(42)
        data = Measurement()
        FES = PriorityQueue()
        FES.put((0, "arrival", None))
        MMm = MMmB(power_supply="INF", service_times=SERVICE_TIMES, buffer_size=BUFFER_SIZE)
        users = 0
        time = 0
        while not FES.empty() and time < SIM_TIME:
            time, event_type, server_id = FES.get()
            if event_type == "arrival":
                arrival(time, FES, MMm, ARRIVAL, data, distribution=service_distribution)
            elif event_type == "departure":
                departure(time, FES, MMm, server_id, data, distribution=service_distribution)

        average_delay = data.delay / data.departures if data.departures > 0 else 0
        busy_time_ratio_val = data.busy_time / SIM_TIME  # Busy time ratio calculation

        # Store results
        avg_users.append(data.average_users / time if time > 0 else 0)
        avg_delay.append(average_delay)
        loss_probability.append(data.loss_probability if data.arrivals > 0 else 0)
        busy_time_ratio.append(busy_time_ratio_val)

        # Print the results for each distribution
        print(f"\nResults for Service Time Distribution = {service_distribution}:")
        print(f" - Arrival Rate: {ARRIVAL}")
        print(f" - Users in Queue: {users}")
        print(f" - Arrivals: {data.arrivals}")
        print(f" - Departures: {data.departures}")
        print(f" - Avg Users: {data.average_users / time if time > 0 else 0:.2f}")
        print(f" - Avg Delay: {average_delay:.2f}")
        print(f" - Loss Probability: {data.loss_probability if data.arrivals > 0 else 0:.4f}")
        print(f" - Avg Waiting Delay: {data.waiting_delay / data.departures if data.departures > 0 else 0:.2f}")
        print(f" - Avg Buffer Occupancy: {data.buffer_occupancy:.2f}")
        print(f" - Busy Time Ratio: {busy_time_ratio_val:.4f}")

    # Plot Average Users
    plt.figure()
    plt.bar(service_distributions, avg_users, color='skyblue')
    plt.title('Average Users in System')
    plt.ylabel('Avg Users')
    plt.show()

    # Plot Average Delay
    plt.figure()
    plt.bar(service_distributions, avg_delay, color='lightgreen')
    plt.title('Average Delay in System')
    plt.ylabel('Avg Delay')
    plt.show()

    # Plot Loss Probability
    plt.figure()
    plt.bar(service_distributions, loss_probability, color='salmon')
    plt.title('Loss Probability')
    plt.ylabel('Loss Probability')
    plt.show()

    # Plot Busy Time Ratio
    plt.figure()
    plt.bar(service_distributions, busy_time_ratio, color='darkblue')
    plt.title('Busy Time Ratio')
    plt.ylabel('Busy Time Ratio')
    plt.show()
