import random
from queue import PriorityQueue
from utils.queues import MMmB, Packet
from utils.measurements import Measurement
import matplotlib.pyplot as plt

# Constants
SERVICE = 15.0
ARRIVAL = 4
BUFFER_SIZE = 30
m_ANTENNAS = 3
N_DRONES = 1
SERVICE_TIMES = [SERVICE / (i + 1) for i in range(m_ANTENNAS)]
TYPE1 = 1
SIM_TIME = 500000
users = 0

# Scheduling policies to test
policies = ['random', 'round_robin', 'fastest']


# Function to run the simulation for a given scheduling policy
def run_simulation(policy):
    MMms = {i: MMmB(power_supply="INF", service_times=SERVICE_TIMES, buffer_size=BUFFER_SIZE) for i in range(N_DRONES)}

    def resolve_MMm():
        return random.choice(list(MMms.keys()))

    for queue in MMms.values():
        if policy == 'fastest':
            queue._scheduling_policy = queue._get_server_fastest
        elif policy == 'round_robin':
            queue._scheduling_policy = queue._get_server_roundrobin
        else:
            queue._scheduling_policy = queue._get_server_random

    FES = PriorityQueue()
    FES.put((0, "arrival", resolve_MMm(), None))
    time = 0
    data = Measurement()

    while time < SIM_TIME:
        (time, event_type, queue_id, server_id) = FES.get()
        if event_type == "arrival":
            arrival(time, FES, queue_id, data, MMms, resolve_MMm)
        elif event_type == "departure":
            departure(time, FES, queue_id, server_id, data, MMms, resolve_MMm)

    return data, list(MMms.values())[0]._servers.values()


def arrival(time, FES, queue_id, data, MMms, resolve_MMm):
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
        packet = Packet(time)  # Crea un nuovo pacchetto con il tempo di arrivo
        queue.insert(packet)  # Inserisci il pacchetto nella coda
        data.buffer_occupancy += queue.queue_size()

    inter_arrival = random.expovariate(1.0 / ARRIVAL)
    FES.put((time + inter_arrival, "arrival", resolve_MMm(), None))

    # Se il server può essere occupato, inizia il servizio per il pacchetto
    if queue.can_engage_server():
        server_id = queue._scheduling_policy()
        server = queue._servers[server_id]
        service_duration = random.expovariate(1.0 / server.service_time)

        # Recupera il pacchetto dalla coda
        next_packet = queue.get_last()  # Verifica se `get_last()` è il metodo giusto per ottenere il pacchetto
        next_packet.start_service_time = time  # Inizia il tempo di servizio per il pacchetto

        server.engage(service_duration)
        FES.put((time + service_duration, "departure", queue_id, server_id))



def departure(time, FES, queue_id, server_id, data, MMms, resolve_MMm):
    global users
    queue = MMms[queue_id]
    packet = queue.consume(server_id)
    data.departures += 1
    data.average_users += users * (time - data.time)
    data.time = time
    data.delay += (time - packet.arrival_time)

    # Controlla se start_service_time è None
    if packet.start_service_time is not None:
        data.queue_delay += (packet.start_service_time - packet.arrival_time)
        data.waiting_delay += (time - packet.start_service_time)
        service_duration = time - packet.start_service_time
        data.busy_time += service_duration  # Aggiornamento del tempo occupato

    users -= 1

    queue._servers[server_id].release()

    if queue.can_engage_server():
        server_id = queue._scheduling_policy()
        server = queue._servers[server_id]
        service_duration = random.expovariate(1.0 / server.service_time)
        next_packet = queue.get_last()
        next_packet.start_service_time = time
        queue.engage_server()
        FES.put((time + service_duration, "departure", queue_id, server_id))

def print_server_busy_ratios(servers, sim_time):
    for i, server in enumerate(servers):
        busy_time_ratio = server.total_time_engaged / sim_time
        print(f"  Server {i+1} busy time ratio: {busy_time_ratio:.4f}")



def plot_server_loads(servers, title="Server Load Distribution", filename="server_load.png"):
    service_times = [server.total_time_engaged for server in servers]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    colors = ['tab:red']
    ax1.set_xlabel('Server', fontsize=14)
    ax1.set_ylabel('Total Time Engaged', color=colors[0], fontsize=14)
    bars = ax1.bar(range(len(service_times)), service_times, color=colors[0])
    ax1.tick_params(axis='y', labelcolor=colors[0], labelsize=12)
    ax1.set_xticks(range(len(service_times)))
    ax1.set_xticklabels([f"Server {i + 1}" for i in range(len(service_times))], fontsize=12)

    for i, val in enumerate(service_times):
        ax1.text(i, val, f"{val:.2f}", ha='center', va='bottom', fontsize=10)

    ax1.legend([bars], ['Total Time Engaged'], loc='upper left', fontsize=12)

    plt.title(title, fontsize=16)
    plt.tight_layout()
    plt.show()



if __name__ == '__main__':
    random.seed(42)
    for policy in policies:
        print(f"Running simulation with {policy} policy...")
        data, servers = run_simulation(policy)

        print(f"Results for {policy.capitalize()} Scheduling:")
        print(f"  Number of arrivals: {data.arrivals}")
        print(f"  Number of departures: {data.departures}")
        print(f"  Number of losses: {data.losses}")
        print(f"  Average users in system: {data.average_users / SIM_TIME}")
        print(f"  Average delay: {data.delay / data.departures if data.departures > 0 else 0}")
        print(f"  Average queue delay: {data.queue_delay / data.departures if data.departures > 0 else 0}")
        print(f"  Average waiting delay: {data.waiting_delay / data.departures if data.departures > 0 else 0}")
        print(f"  Loss probability: {data.losses / data.arrivals if data.arrivals > 0 else 0}")
        print(f"  Average buffer occupancy: {data.buffer_occupancy / data.arrivals if data.arrivals > 0 else 0}")
        # Stampa il busy time ratio per ogni server
        print_server_busy_ratios(servers, SIM_TIME)
        plot_server_loads(list(servers), f"Load Distribution for {policy.capitalize()} Scheduling")
