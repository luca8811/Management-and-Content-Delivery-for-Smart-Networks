import random
from queue import PriorityQueue
from utils.queues import MMmB, Packet
from utils.measurements import Measurement
import matplotlib.pyplot as plt

# Constants
BUFFER_SIZE = 100
SERVICE = 10.0
ARRIVAL = 10
N_ANTENNAS = 1  # m = 1
N_DRONES = 1  # N = 1
SIM_TIME = 500000
users = 0

# Different service time distributions to test
distributions = {
    'exponential': lambda: random.expovariate(1.0 / SERVICE),
    'uniform': lambda: random.uniform(SERVICE / 2, SERVICE * 1.5),
    'normal': lambda: max(0.0, random.gauss(SERVICE, SERVICE * 0.25))  # Avoid negative service times
}

def run_simulation(service_time_dist):
    MMms = {i: MMmB(power_supply="INF", service_times=[SERVICE], buffer_size=BUFFER_SIZE) for i in range(N_DRONES)}

    def resolve_MMm():
        return random.choice(list(MMms.keys()))

    for queue in MMms.values():
        queue._scheduling_policy = queue._get_server_fastest

    FES = PriorityQueue()
    FES.put((0, "arrival", resolve_MMm(), None))
    time = 0
    data = Measurement()

    while time < SIM_TIME:
        (time, event_type, queue_id, server_id) = FES.get()
        if event_type == "arrival":
            arrival(time, FES, queue_id, data, MMms, resolve_MMm, service_time_dist)
        elif event_type == "departure":
            departure(time, FES, queue_id, server_id, data, MMms, resolve_MMm, service_time_dist)

    # Final calculations
    if data.time > 0:  # Avoid division by zero
        data.average_users /= data.time
        data.buffer_occupancy /= data.time
        data.busy_time /= data.time

    return data

def arrival(time, FES, queue_id, data, MMms, resolve_MMm, service_time_dist):
    global users
    queue = MMms[queue_id]
    loss = queue.is_queue_full()
    data.arrivals += 1
    data.average_users += users * (time - data.time)
    data.time = time

    if loss:
        data.losses += 1
    else:
        users += 1
        packet = Packet(time)
        queue.insert(packet)
        data.buffer_occupancy += queue.queue_size() * (time - data.time)

        if queue.can_engage_server():
            server_id = queue._scheduling_policy()
            server = queue._servers[server_id]
            service_duration = service_time_dist()
            packet.start_service_time = time
            queue.engage_server()
            server.engage(service_duration)
            FES.put((time + service_duration, "departure", queue_id, server_id))

    # Schedule next arrival
    inter_arrival = random.expovariate(1.0 / ARRIVAL)
    FES.put((time + inter_arrival, "arrival", resolve_MMm(), None))

def departure(time, FES, queue_id, server_id, data, MMms, resolve_MMm, service_time_dist):
    global users
    queue = MMms[queue_id]
    packet = queue.consume(server_id)
    data.departures += 1
    data.average_users += users * (time - data.time)
    data.time = time
    if packet and packet.start_service_time is not None:
        service_duration = time - packet.start_service_time
        data.delay += (time - packet.arrival_time)
        data.queue_delay += (packet.start_service_time - packet.arrival_time)
        data.waiting_delay += service_duration
        data.busy_time += service_duration
    users -= 1

    queue._servers[server_id].release()

    if queue.can_engage_server():
        server_id = queue._scheduling_policy()
        server = queue._servers[server_id]
        service_duration = service_time_dist()
        next_packet = queue.get_last()
        next_packet.start_service_time = time
        queue.engage_server()
        FES.put((time + service_duration, "departure", queue_id, server_id))

def plot_results(data, title):
    print(f"Results for {title} Distribution:")
    print(f"  Number of arrivals: {data.arrivals}")
    print(f"  Number of departures: {data.departures}")
    print(f"  Number of losses: {data.losses}")
    print(f"  Average users in system: {data.average_users}")
    print(f"  Average delay: {data.delay / data.departures if data.departures > 0 else 0}")
    print(f"  Average queue delay: {data.queue_delay / data.departures if data.departures > 0 else 0}")
    print(f"  Average waiting delay: {data.waiting_delay / data.departures if data.departures > 0 else 0}")
    print(f"  Loss probability: {data.losses / data.arrivals if data.arrivals > 0 else 0}")
    print(f"  Average buffer occupancy: {data.buffer_occupancy / data.time if data.time > 0 else 0}")
    print(f"  Busy time ratio: {data.busy_time}")

def plot_comparisons(results):
    # Estrarre i risultati per ogni distribuzione
    labels = list(results.keys())
    avg_delay = [results[dist]['avg_delay'] for dist in labels]
    loss_prob = [results[dist]['loss_prob'] for dist in labels]
    buffer_occupancy = [results[dist]['avg_buffer_occupancy'] for dist in labels]

    x = range(len(labels))

    # Grafico per ritardo medio
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.bar(x, avg_delay, color='blue', alpha=0.6)
    plt.xticks(x, labels)
    plt.title('Average Delay by Distribution')
    plt.xlabel('Service Time Distribution')
    plt.ylabel('Average Delay')

    # Grafico per la probabilità di perdita
    plt.subplot(1, 2, 2)
    plt.bar(x, loss_prob, color='red', alpha=0.6)
    plt.xticks(x, labels)
    plt.title('Loss Probability by Distribution')
    plt.xlabel('Service Time Distribution')
    plt.ylabel('Loss Probability')

    plt.tight_layout()
    plt.show()

# Main simulation and analysis
if __name__ == '__main__':
    random.seed(42)
    results = {}

    for dist_name, dist_func in distributions.items():
        print(f"Running simulation with {dist_name} distribution...")
        data = run_simulation(dist_func)

        # Memorizza i risultati in un dizionario
        results[dist_name] = {
            'arrivals': data.arrivals,
            'departures': data.departures,
            'losses': data.losses,
            'avg_delay': data.delay / data.departures if data.departures > 0 else 0,
            'loss_prob': data.losses / data.arrivals if data.arrivals > 0 else 0,
            'avg_buffer_occupancy': data.buffer_occupancy / data.time if data.time > 0 else 0
        }

        # Stampa i risultati per ogni distribuzione
        plot_results(data, dist_name.capitalize())

    # Visualizza un confronto tra le distribuzioni
    plot_comparisons(results)
