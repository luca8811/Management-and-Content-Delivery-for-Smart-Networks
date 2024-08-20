import random
from queue import PriorityQueue
from queues import MMmB, Client
from measurements import Measure
import matplotlib.pyplot as plt

# Constants
SERVICE = 20.0
ARRIVAL = 3
BUFFER_SIZE = 100
m_ANTENNAS = 3
N_DRONES = 1
SERVICE_TIMES = [SERVICE / (i + 1) for i in range(m_ANTENNAS)]  # Varied service times
TYPE1 = 1
SIM_TIME = 500000
users = 0

# Scheduling policies to test
policies = ['random', 'round_robin', 'fastest']


# Function to run the simulation for a given scheduling policy
def run_simulation(policy):
    MMms = {i: MMmB(service_times=SERVICE_TIMES, buffer_size=BUFFER_SIZE) for i in range(N_DRONES)}

    def resolve_MMm():
        return random.choice(list(MMms.keys()))

    for queue in MMms.values():
        queue._scheduling_policy = queue._get_server_fastest if policy == 'fastest' else \
            (queue._get_server_roundrobin if policy == 'round_robin' else \
                 queue._get_server_random)

    FES = PriorityQueue()
    FES.put((0, "arrival", resolve_MMm(), None))
    time = 0
    data = Measure()

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
    data.arr += 1
    data.ut += users * (time - data.oldT)
    data.oldT = time
    if loss:
        data.los += 1  # Increment loss count if the queue is full
    else:
        users += 1
        client = Client(TYPE1, time)
        queue.insert(client)
        data.buffer_occupancy += queue.queue_size()

    inter_arrival = random.expovariate(1.0 / ARRIVAL)
    FES.put((time + inter_arrival, "arrival", resolve_MMm(), None))

    if queue.can_engage_server():
        server_id = queue._scheduling_policy()
        server = queue._servers[server_id]
        service_duration = random.expovariate(1.0 / server.service_time)
        client.start_service_time = time  # Record start service time
        queue.engage_server()
        server.engage(service_duration)  # Update server attributes when engaged
        FES.put((time + service_duration, "departure", queue_id, server_id))


def departure(time, FES, queue_id, server_id, data, MMms, resolve_MMm):
    global users
    queue = MMms[queue_id]
    client = queue.consume(server_id)
    data.dep += 1
    data.ut += users * (time - data.oldT)
    data.oldT = time
    data.delay += (time - client.arrival_time)
    if client.start_service_time:
        data.queue_delay += (client.start_service_time - client.arrival_time)
        data.waiting_delay += (time - client.start_service_time)
    users -= 1

    if queue.can_engage_server():
        server_id = queue._scheduling_policy()
        server = queue._servers[server_id]
        service_duration = random.expovariate(1.0 / server.service_time)
        next_client = queue.get_last()
        next_client.start_service_time = time
        queue.engage_server()
        FES.put((time + service_duration, "departure", queue_id, server_id))

    data.busy_time += (time - data.oldT)


def plot_server_loads(servers, title="Server Load Distribution"):
    # Gather data
    service_times = [server.total_time_engaged for server in servers]
    selections = [server.selection_count for server in servers]

    # Create figure and plot space
    fig, ax1 = plt.subplots(figsize=(10, 6))  # Larger figure size for better visibility

    # Plotting service times
    colors = ['tab:red', 'tab:blue']  # Distinct colors for each dataset
    ax1.set_xlabel('Server', fontsize=14)
    ax1.set_ylabel('Total Time Engaged', color=colors[0], fontsize=14)
    bars = ax1.bar(range(len(service_times)), service_times, color=colors[0])
    ax1.tick_params(axis='y', labelcolor=colors[0], labelsize=12)
    ax1.set_xticks(range(len(service_times)))
    ax1.set_xticklabels([f"Server {i + 1}" for i in range(len(service_times))], fontsize=12)

    # Adding text labels to the bars
    for i, val in enumerate(service_times):
        ax1.text(i, val, f"{val:.2f}", ha='center', va='bottom', fontsize=10)

    # Create a twin axis to plot selection count
    ax2 = ax1.twinx()
    ax2.set_ylabel('Selection Count', color=colors[1], fontsize=14)
    line, = ax2.plot(range(len(selections)), selections, color=colors[1], marker='o', label='Selection Count')
    ax2.tick_params(axis='y', labelcolor=colors[1], labelsize=12)

    # Adding a legend to the plot
    ax1.legend([bars, line], ['Total Time Engaged', 'Selection Count'], loc='upper left', fontsize=12)

    # Title and layout adjustments
    plt.title(title, fontsize=16)
    plt.tight_layout()  # Adjust layout to not cut off labels

    plt.show()


# Main simulation and analysis
if __name__ == '__main__':
    random.seed(42)
    for policy in policies:
        print(f"Running simulation with {policy} policy...")
        data, servers = run_simulation(policy)

        # Print the results
        print(f"Results for {policy.capitalize()} Scheduling:")
        print(f"  Number of arrivals: {data.arr}")
        print(f"  Number of departures: {data.dep}")
        print(f"  Number of losses: {data.los}")
        print(f"  Average users in system: {data.ut / SIM_TIME}")
        print(f"  Average delay: {data.delay / data.dep if data.dep > 0 else 0}")
        print(f"  Average queue delay: {data.queue_delay / data.dep if data.dep > 0 else 0}")
        print(f"  Average waiting delay: {data.waiting_delay / data.dep if data.dep > 0 else 0}")
        print(f"  Loss probability: {data.los / data.arr if data.arr > 0 else 0}")
        print(f"  Average buffer occupancy: {data.buffer_occupancy / data.arr if data.arr > 0 else 0}")
        print(f"  Busy time ratio: {data.busy_time / SIM_TIME}")

        # Plot the results
        plot_server_loads(list(servers), f"Load Distribution for {policy.capitalize()} Scheduling")
