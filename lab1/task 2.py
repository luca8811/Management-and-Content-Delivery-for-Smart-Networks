import random
from queue import PriorityQueue
from queues import MMmB, Client
from measurements import Measure
import csv  # Import CSV module

# Constants
SERVICE = 20.0  # Average service time; service rate is 1/SERVICE
arrival_rates = [5, 10, 15]  # Example rates: mean inter-arrival times
buffer_sizes = [0, 100, 300, 500]  # Example sizes
SIM_TIME = 500000
TYPE1 = 1

# Configuration for scenarios
scenarios = {
    "one_drone_two_antennas": {"n_drones": 1, "antennas_per_drone": 2},
    "two_drones_one_antenna": {"n_drones": 2, "antennas_per_drone": 1}
}

def resolve_MMm():
    return random.choice(list(MMms.keys()))

class Client:
    def __init__(self, type, arrival_time):
        self.type = type
        self.arrival_time = arrival_time
        self.start_service_time = None  # Initialize start_service_time

def arrival(time, FES, queue_id):
    global users
    queue = MMms[queue_id]
    loss = queue.is_queue_full()
    data.arr += 1
    if loss:
        data.los += 1
    else:
        if users > 0:
            data.ut += users * (time - data.oldT)
        data.oldT = time
        client = Client(TYPE1, time)
        queue.insert(client)
        users += 1
        data.transmitted_packets += 1
        data.average_packets += users

        if queue.can_engage_server():
            (s_id, s_service_time) = queue.engage_server()
            service_time = random.expovariate(1.0 / SERVICE)  # Use fixed service time
            client.start_service_time = time  # Set start service time
            FES.put((time + service_time, "departure", queue_id, s_id))

    inter_arrival = random.expovariate(1.0 / ARRIVAL)
    FES.put((time + inter_arrival, "arrival", resolve_MMm(), None))

def departure(time, FES, queue_id, server_id):
    global users
    queue = MMms[queue_id]
    client = queue.consume(server_id)

    data.dep += 1
    service_duration = time - client.arrival_time
    data.delay += service_duration
    if client.start_service_time is not None:
        queue_delay = client.start_service_time - client.arrival_time
        data.queue_delay += queue_delay  # Calculate queue delay correctly
    data.waiting_delay += service_duration  # Waiting delay is the time from queue to departure

    if users > 0:
        data.ut += users * (time - data.oldT)
    data.oldT = time
    users -= 1

    if queue.can_engage_server():
        (s_id, s_service_time) = queue.engage_server()
        service_time = random.expovariate(1.0 / SERVICE)  # Use fixed service time
        new_client = Client(TYPE1, time)  # Create new client for the server
        new_client.start_service_time = time  # Set start service time for new client
        FES.put((time + service_time, "departure", queue_id, s_id))
        data.busy_time += service_duration
    data.buffer_occupancy += users

if __name__ == '__main__':
    random.seed(42)
    # Open a CSV file to write the results
    with open('simulation_results.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the headers
        writer.writerow(['Scenario', 'Buffer Size', 'Arrival Rate', 'No. of Users in Queue', 'No. of Arrivals', 'No. of Departures', 'Arrival Rate', 'Departure Rate', 'Loss Rate', 'Packets Lost', 'Average No. of Users', 'Average Delay', 'Average Queue Delay', 'Average Waiting Delay', 'Average Buffer Occupancy', 'Loss Probability', 'Busy Time'])

        for scenario_key, config in scenarios.items():
            n_drones = config['n_drones']
            antennas_per_drone = config['antennas_per_drone']

            for BUFFER_SIZE in buffer_sizes:
                for ARRIVAL in arrival_rates:
                    # Create drones with the specified number of antennas
                    MMms = {i: MMmB(service_times=[SERVICE] * antennas_per_drone, buffer_size=BUFFER_SIZE) for i in range(n_drones)}
                    data = Measure()
                    time = 0
                    FES = PriorityQueue()
                    FES.put((0, "arrival", resolve_MMm(), None))
                    users = 0

                    while time < SIM_TIME:
                        (time, event_type, queue_id, server_id) = FES.get()
                        if event_type == "arrival":
                            arrival(time, FES, queue_id)
                        elif event_type == "departure":
                            departure(time, FES, queue_id, server_id)

                    average_delay = data.delay / data.dep if data.dep > 0 else 0
                    average_queue_delay = data.queue_delay / data.dep if data.dep > 0 else 0
                    average_waiting_delay = data.waiting_delay / data.dep if data.dep > 0 else 0
                    average_buffer_occupancy = data.buffer_occupancy / data.arr if data.arr > 0 else 0
                    loss_probability = data.los / data.arr if data.arr > 0 else 0
                    average_users = data.ut / time if time > 0 else 0
                    busy_time_ratio = data.busy_time / SIM_TIME

                    # Write results to CSV
                    writer.writerow([scenario_key, BUFFER_SIZE, 1 / ARRIVAL, users, data.arr, data.dep, data.arr / time, data.dep / time, data.los / time, data.los, average_users, average_delay, average_queue_delay, average_waiting_delay, average_buffer_occupancy, loss_probability, busy_time_ratio])
                    print(f"Results for {scenario_key} - Buffer Size {BUFFER_SIZE} and Arrival Rate {1/ARRIVAL:.2f}:")
                    print("No. of users in the queue:", users)
                    print("No. of arrivals =", data.arr, "- No. of departures =", data.dep)
                    print("Arrival rate:", data.arr / time, "- Departure rate:", data.dep / time)
                    print("Loss rate:", data.los / time, "- Packets loss:", data.los)
                    print("Average number of users:", average_users)
                    print("Average delay:", average_delay)
                    print("Average queue delay:", average_queue_delay)
                    print("Average waiting delay:", average_waiting_delay)
                    print("Average buffer occupancy:", average_buffer_occupancy)
                    print("Loss probability:", loss_probability)
                    print("Busy time ratio:", busy_time_ratio)
                    print("---------------------------------------------------")
