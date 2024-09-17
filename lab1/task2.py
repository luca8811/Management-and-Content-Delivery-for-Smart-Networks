import random
from queue import PriorityQueue
from utils.queues import MMmB, Packet
from utils.measurements import Measurement
import csv
import logging
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.WARNING)

# Costanti
SERVICE = 2.0  # Tempo medio di servizio fisso
arrival_rates = [0.5, 0.8, 1.0, 1.2]  # Tassi di arrivo
buffer_sizes = [float('inf'), 10, 20, 50]  # Buffer infinito e buffer di dimensioni finite
SIM_TIME = 100000

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

# Evento di arrivo
def arrival(time, FES, queue_id, data, ARRIVAL, n_drones):
    queue = MMms[queue_id]
    measurement = data[queue_id]
    packet = Packet(time)
    measurement.arrivals += 1

    if queue.is_queue_full():
        measurement.losses += 1
    else:
        queue.users += 1  # Incrementa gli utenti poiché un nuovo pacchetto è arrivato
        if queue.can_engage_server():
            (s_id, s_service_time) = queue.engage_server()
            queue.server_packets[s_id] = packet  # Assegna il pacchetto al server
            packet.start_service_time = time  # Imposta il tempo di inizio servizio
            service_time = random.expovariate(1.0 / SERVICE)
            FES.put((time + service_time, "departure", queue_id, s_id))
            measurement.busy_time += service_time
        else:
            queue.insert(packet)

    # Pianifica il prossimo arrivo
    inter_arrival = random.expovariate(ARRIVAL / n_drones)
    FES.put((time + inter_arrival, "arrival", queue_id, None))


# Evento di partenza
def departure(time, FES, queue_id, server_id, data):
    queue = MMms[queue_id]
    measurement = data[queue_id]
    packet = queue.server_packets.pop(server_id)  # Recupera il pacchetto associato al server
    measurement.departures += 1

    total_delay = time - packet.arrival_time  # Ritardo totale nel sistema
    measurement.delay += total_delay

    if packet.start_service_time is not None:
        queue_delay = packet.start_service_time - packet.arrival_time  # Tempo in coda
        service_time = time - packet.start_service_time  # Tempo di servizio
        measurement.queue_delay += queue_delay
        measurement.waiting_delay += service_time  # Aggiorna il tempo di servizio
    else:
        # Questo non dovrebbe accadere, ma lo gestiamo comunque
        measurement.waiting_delay += 0

    # Aggiorna il numero medio di utenti
    if queue.users > 0:
        measurement.average_users += queue.users * (time - measurement.time)
    measurement.time = time
    queue.users -= 1  # Decrementa gli utenti poiché un pacchetto ha lasciato il sistema

    # Controlla se ci sono pacchetti in attesa nella coda
    if len(queue._queue) > 0:
        next_packet = queue._queue.pop(0)  # Estrae il prossimo pacchetto dalla coda
        queue.server_packets[server_id] = next_packet  # Assegna il pacchetto al server
        next_packet.start_service_time = time  # Imposta il tempo di inizio servizio
        next_service_time = random.expovariate(1.0 / SERVICE)
        FES.put((time + next_service_time, "departure", queue_id, server_id))
        measurement.busy_time += next_service_time
        # Non decrementare queue.users qui, il pacchetto è ancora nel sistema
    else:
        # Non ci sono pacchetti in attesa, il server diventa idle
        queue._servers[server_id].idle = True

    measurement.buffer_occupancy += queue.users



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
            total_servers = n_drones * antennas_per_drone

            for BUFFER_SIZE in buffer_sizes:
                for ARRIVAL in arrival_rates:
                    # Crea droni con il numero specificato di antenne
                    MMms = {i: MMmB(power_supply="INF", service_times=[SERVICE] * antennas_per_drone, buffer_size=BUFFER_SIZE) for i in range(n_drones)}
                    # Inizializza data per ogni coda
                    data = {queue_id: Measurement() for queue_id in MMms.keys()}
                    # Inizializza users e server_packets per ogni coda
                    for queue in MMms.values():
                        queue.users = 0
                        queue.server_packets = {}  # Aggiungi questa linea
                    time = 0
                    FES = PriorityQueue()
                    # Inizializza un arrivo per ciascuna coda
                    for queue_id in MMms.keys():
                        FES.put((0, "arrival", queue_id, None))

                    while time < SIM_TIME:
                        (time, event_type, queue_id, server_id) = FES.get()
                        if event_type == "arrival":
                            arrival(time, FES, queue_id, data, ARRIVAL, n_drones)
                        elif event_type == "departure":
                            departure(time, FES, queue_id, server_id, data)

                    # Calcola le metriche di prestazione sommando sui droni
                    total_arrivals = sum([data[queue_id].arrivals for queue_id in data.keys()])
                    total_departures = sum([data[queue_id].departures for queue_id in data.keys()])
                    total_losses = sum([data[queue_id].losses for queue_id in data.keys()])
                    total_delay = sum([data[queue_id].delay for queue_id in data.keys()])
                    total_queue_delay = sum([data[queue_id].queue_delay for queue_id in data.keys()])
                    total_waiting_delay = sum([data[queue_id].waiting_delay for queue_id in data.keys()])
                    total_buffer_occupancy = sum([data[queue_id].buffer_occupancy for queue_id in data.keys()])
                    total_busy_time = sum([data[queue_id].busy_time for queue_id in data.keys()])
                    total_average_users = sum([data[queue_id].average_users for queue_id in data.keys()]) / SIM_TIME

                    average_delay = total_delay / total_departures if total_departures > 0 else 0
                    average_queue_delay = total_queue_delay / total_departures if total_departures > 0 else 0
                    average_waiting_delay = total_waiting_delay / total_departures if total_departures > 0 else 0
                    average_buffer_occupancy = total_buffer_occupancy / total_arrivals if total_arrivals > 0 else 0
                    loss_probability = total_losses / total_arrivals if total_arrivals > 0 else 0
                    busy_time_ratio = total_busy_time / (SIM_TIME * total_servers)

                    # Scrivi i risultati nel file CSV
                    writer.writerow(
                        [scenario_key, BUFFER_SIZE, ARRIVAL, "-", total_arrivals, total_departures, total_losses / time if time > 0 else 0,
                         total_losses, total_average_users, average_delay, average_queue_delay, average_waiting_delay,
                         average_buffer_occupancy, loss_probability, busy_time_ratio])

                    # Stampa i risultati per monitorare la simulazione
                    print(f"Results for {scenario_key} - Buffer Size {BUFFER_SIZE} and Arrival Rate {ARRIVAL}:")
                    print("No. of users in the queue per drone:", [MMms[q_id].users for q_id in MMms.keys()])
                    print("No. of arrivals =", total_arrivals, "- No. of departures =", total_departures)
                    print("Loss rate:", total_losses / time if time > 0 else 0, "- Packets lost:", total_losses)
                    print("Average number of users:", total_average_users)
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
                    results_data['loss_rate'].append(total_losses / time if time > 0 else 0)
                    results_data['buffer_occupancy'].append(average_buffer_occupancy)
                    results_data['busy_time_ratio'].append(busy_time_ratio)





