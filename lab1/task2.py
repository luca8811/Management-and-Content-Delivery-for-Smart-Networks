import random
from queue import PriorityQueue
from utils.queues import MMmB, Packet
from utils.measurements import Measurement
import csv
import logging
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.WARNING)

# Costanti
SERVICE = 20.0  # Tempo medio di servizio fisso
arrival_rates = [5, 10, 15, 20]  # Tassi di arrivo
buffer_sizes = [float('inf'), 100, 300, 500]  # Buffer infinito e buffer di dimensioni finite
SIM_TIME = 500000

# Configurazione degli scenari
scenarios = {
    "one_drone_two_antennas": {"n_drones": 1, "antennas_per_drone": 2},
    "two_drones_one_antenna": {"n_drones": 2, "antennas_per_drone": 1}
}

# Dizionari per raccogliere i dati da visualizzare nei grafici
results_data = {
    'scenario': [],
    'buffer_size': [],
    'arrival_rate': [],
    'average_delay': [],
    'loss_rate': [],
    'buffer_occupancy': [],
    'busy_time_ratio': []
}

# Funzione per risolvere quale MMm usare (scelta casuale tra i server)
def resolve_MMm():
    return random.choice(list(MMms.keys()))

# Evento di arrivo
def arrival(time, FES, queue_id, data, ARRIVAL):
    global users
    queue = MMms[queue_id]
    loss = queue.is_queue_full()
    data.arrivals += 1

    if loss:
        data.losses += 1
    else:
        if users > 0:
            data.average_users += users * (time - data.time)
        data.time = time
        packet = Packet(time)
        queue.insert(packet)
        users += 1
        data.transmitted_packets += 1
        data.average_packets += users

        if queue.can_engage_server():
            (s_id, s_service_time) = queue.engage_server()
            service_time = random.expovariate(1.0 / SERVICE)
            FES.put((time + service_time, "departure", queue_id, s_id))
            data.busy_time += service_time

    inter_arrival = random.expovariate(1.0 / ARRIVAL)
    FES.put((time + inter_arrival, "arrival", resolve_MMm(), None))

# Evento di partenza
def departure(time, FES, queue_id, server_id, data):
    global users
    queue = MMms[queue_id]
    if queue.queue_size() > 0:
        packet = queue.consume(server_id)
        data.departures += 1
        service_duration = time - packet.arrival_time
        data.delay += service_duration

        if packet.start_service_time is not None:
            queue_delay = packet.start_service_time - packet.arrival_time
            data.queue_delay += queue_delay

        data.waiting_delay += service_duration

        if users > 0:
            data.average_users += users * (time - data.time)
        data.time = time
        users -= 1

        if queue.can_engage_server():
            (s_id, s_service_time) = queue.engage_server()
            service_time = random.expovariate(1.0 / SERVICE)
            FES.put((time + service_time, "departure", queue_id, s_id))
            data.busy_time += service_time

    data.buffer_occupancy += users

if __name__ == '__main__':
    random.seed(42)

    # Apri il file CSV per scrivere i risultati
    with open('simulation_results.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        # Scrivi l'intestazione del file CSV
        writer.writerow(['Scenario', 'Buffer Size', 'Arrival Rate', 'Users', 'Arrivals', 'Departures', 'Loss Rate',
                         'Packets Lost', 'Average Users', 'Average Delay', 'Average Queue Delay', 'Average Waiting Delay',
                         'Average Buffer Occupancy', 'Loss Probability', 'Busy Time Ratio'])

        for scenario_key, config in scenarios.items():
            n_drones = config['n_drones']
            antennas_per_drone = config['antennas_per_drone']

            for BUFFER_SIZE in buffer_sizes:
                for ARRIVAL in arrival_rates:
                    # Crea droni con il numero specificato di antenne
                    MMms = {i: MMmB(power_supply="INF", service_times=[SERVICE] * antennas_per_drone, buffer_size=BUFFER_SIZE) for i in range(n_drones)}
                    data = Measurement()
                    time = 0
                    FES = PriorityQueue()
                    FES.put((0, "arrival", resolve_MMm(), None))
                    users = 0

                    while time < SIM_TIME:
                        (time, event_type, queue_id, server_id) = FES.get()
                        if event_type == "arrival":
                            arrival(time, FES, queue_id, data, ARRIVAL)
                        elif event_type == "departure":
                            departure(time, FES, queue_id, server_id, data)

                    # Calcola le metriche di prestazione
                    average_delay = data.delay / data.departures if data.departures > 0 else 0
                    average_queue_delay = data.queue_delay / data.departures if data.departures > 0 else 0
                    average_waiting_delay = data.waiting_delay / data.departures if data.departures > 0 else 0
                    average_buffer_occupancy = data.buffer_occupancy / data.arrivals if data.arrivals > 0 else 0
                    loss_probability = data.losses / data.arrivals if data.arrivals > 0 else 0
                    average_users = data.average_users / time if time > 0 else 0
                    busy_time_ratio = data.busy_time / SIM_TIME

                    # Scrivi i risultati nel file CSV
                    writer.writerow(
                        [scenario_key, BUFFER_SIZE, ARRIVAL, users, data.arrivals, data.departures, data.losses / time,
                         data.losses, average_users, average_delay, average_queue_delay, average_waiting_delay,
                         average_buffer_occupancy, loss_probability, busy_time_ratio])

                    # Stampa i risultati per monitorare la simulazione
                    print(f"Results for {scenario_key} - Buffer Size {BUFFER_SIZE} and Arrival Rate {ARRIVAL}:")
                    print("No. of users in the queue:", users)
                    print("No. of arrivals =", data.arrivals, "- No. of departures =", data.departures)
                    print("Loss rate:", data.losses / time, "- Packets lost:", data.losses)
                    print("Average number of users:", average_users)
                    print("Average delay:", average_delay)
                    print("Average queue delay:", average_queue_delay)
                    print("Average waiting delay:", average_waiting_delay)
                    print("Average buffer occupancy:", average_buffer_occupancy)
                    print("Loss probability:", loss_probability)
                    print("Busy time ratio:", busy_time_ratio)
                    print("---------------------------------------------------")

                    # Memorizza i dati per i grafici
                    results_data['scenario'].append(scenario_key)
                    results_data['buffer_size'].append(BUFFER_SIZE)
                    results_data['arrival_rate'].append(ARRIVAL)
                    results_data['average_delay'].append(average_delay)
                    results_data['loss_rate'].append(data.losses / time if time > 0 else 0)
                    results_data['buffer_occupancy'].append(average_buffer_occupancy)
                    results_data['busy_time_ratio'].append(busy_time_ratio)

    # Genera i grafici
    plt.figure(figsize=(10, 8))

    # Grafico 1: Ritardo medio vs Tasso di arrivo (con scala logaritmica)
    plt.subplot(2, 2, 1)
    for buffer_size in buffer_sizes:
        for scenario in scenarios:
            x = [results_data['arrival_rate'][i] for i in range(len(results_data['scenario']))
                 if results_data['scenario'][i] == scenario and results_data['buffer_size'][i] == buffer_size]
            y = [results_data['average_delay'][i] for i in range(len(results_data['scenario']))
                 if results_data['scenario'][i] == scenario and results_data['buffer_size'][i] == buffer_size]
            plt.plot(x, y, marker='o', label=f'{scenario}, Buffer={buffer_size}')
    plt.yscale('log')  # Aggiunta della scala logaritmica
    plt.title('Average Delay vs Arrival Rate')
    plt.xlabel('Arrival Rate')
    plt.ylabel('Average Delay (log scale)')
    plt.legend(loc='upper right')
    plt.grid(True)

    # Grafico 2: Tasso di perdita vs Tasso di arrivo (normale)
    plt.subplot(2, 2, 2)
    for buffer_size in buffer_sizes:
        for scenario in scenarios:
            x = [results_data['arrival_rate'][i] for i in range(len(results_data['scenario']))
                 if results_data['scenario'][i] == scenario and results_data['buffer_size'][i] == buffer_size]
            y = [results_data['loss_rate'][i] for i in range(len(results_data['scenario']))
                 if results_data['scenario'][i] == scenario and results_data['buffer_size'][i] == buffer_size]
            plt.plot(x, y, marker='o', label=f'{scenario}, Buffer={buffer_size}')
    plt.title('Loss Rate vs Arrival Rate')
    plt.xlabel('Arrival Rate')
    plt.ylabel('Loss Rate')
    plt.legend(loc='upper right')
    plt.grid(True)

    # Grafico 3: Occupazione del buffer vs Tasso di arrivo (con scala logaritmica)
    plt.subplot(2, 2, 3)
    for buffer_size in buffer_sizes:
        for scenario in scenarios:
            x = [results_data['arrival_rate'][i] for i in range(len(results_data['scenario']))
                 if results_data['scenario'][i] == scenario and results_data['buffer_size'][i] == buffer_size]
            y = [results_data['buffer_occupancy'][i] for i in range(len(results_data['scenario']))
                 if results_data['scenario'][i] == scenario and results_data['buffer_size'][i] == buffer_size]
            plt.plot(x, y, marker='o', label=f'{scenario}, Buffer={buffer_size}')
    plt.yscale('log')  # Aggiunta della scala logaritmica
    plt.title('Buffer Occupancy vs Arrival Rate')
    plt.xlabel('Arrival Rate')
    plt.ylabel('Buffer Occupancy (log scale)')
    plt.legend(loc='upper right')
    plt.grid(True)

    # Grafico 4: Busy Time Ratio vs Tasso di arrivo (normale)
    plt.subplot(2, 2, 4)
    for buffer_size in buffer_sizes:
        for scenario in scenarios:
            x = [results_data['arrival_rate'][i] for i in range(len(results_data['scenario']))
                 if results_data['scenario'][i] == scenario and results_data['buffer_size'][i] == buffer_size]
            y = [results_data['busy_time_ratio'][i] for i in range(len(results_data['scenario']))
                 if results_data['scenario'][i] == scenario and results_data['buffer_size'][i] == buffer_size]
            plt.plot(x, y, marker='o', label=f'{scenario}, Buffer={buffer_size}')
    plt.title('Busy Time Ratio vs Arrival Rate')
    plt.xlabel('Arrival Rate')
    plt.ylabel('Busy Time Ratio')
    plt.legend(loc='upper right')
    plt.grid(True)

    # Mostra i grafici
    plt.tight_layout()
    plt.show()
