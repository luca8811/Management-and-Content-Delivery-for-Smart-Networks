import random
from queue import PriorityQueue
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from utils.queues import MMmB, Packet
from utils.measurements import Measurement

# Parametri di simulazione
SERVICE = 15.0  # Tempo di servizio fisso
BUFFER_SIZE = 0  # Nessun buffer come da Task 1
SERVICE_TIMES = [SERVICE]
SIM_TIME = 500000  # Tempo totale di simulazione
ARRIVAL_RATES = [0.1, 0.5, 0.9, 1.1, 1.5]  # Tassi di arrivo da testare

def arrival(time, FES, queue: MMmB, arrival_rate, data: Measurement):
    global users
    loss = False
    data.arrivals += 1
    data.average_users += users * (time - data.time)  # Tempo ponderato
    data.time = time
    try:
        if queue.buffer_size > 0:
            queue.insert(Packet(time))
            users += 1
        else:
            # Tenta di processare il pacchetto direttamente se il buffer è 0
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
            service_time = random.expovariate(1.0 / SERVICE)
            FES.put((time + service_time, "departure", s_id))  # Evento di partenza

    inter_arrival = random.expovariate(arrival_rate)
    FES.put((time + inter_arrival, "arrival", None))

def departure(time, FES, queue: MMmB, server_id, data: Measurement):
    global users
    if queue.queue_size() > 0:
        client = queue.consume(server_id)
        client.start_service_time = time
        data.departures += 1
        data.transmitted_packets += 1
        data.delay += (time - client.arrival_time)

        if client.start_service_time > client.arrival_time:  # Il pacchetto ha aspettato in coda
            data.waiting_delay += client.start_service_time - client.arrival_time
            data.waiting_delays.append(client.start_service_time - client.arrival_time)
        data.average_users += users * (time - data.time)
        data.time = time
        users -= 1  # Decrementa il numero di utenti
        if queue.can_engage_server():
            s_id, _ = queue.engage_server()
            service_time = random.expovariate(1.0 / SERVICE)
            FES.put((time + service_time, "departure", s_id))
            data.busy_time += service_time

        # Calcolo dell'occupazione del buffer
        if BUFFER_SIZE > 0:
            data.buffer_occupancy = users / BUFFER_SIZE
        else:
            data.buffer_occupancy = 0  # Se il buffer è 0, l'occupazione è 0
    else:
        queue._servers[server_id].release()  # Libera il server se non ci sono pacchetti in coda

if __name__ == '__main__':
    random.seed(42)
    results = []
    delays = []
    loss_rates = []
    average_users_list = []

    for ARRIVAL in ARRIVAL_RATES:
        data = Measurement()
        FES = PriorityQueue()
        FES.put((0, "arrival", None))
        MMm = MMmB(power_supply="INF", service_times=SERVICE_TIMES, buffer_size=BUFFER_SIZE)
        users = 0
        time = 0
        while not FES.empty() and time < SIM_TIME:
            time, event_type, server_id = FES.get()
            if event_type == "arrival":
                arrival(time, FES, MMm, ARRIVAL, data)
            elif event_type == "departure":
                departure(time, FES, MMm, server_id, data)
        average_delay = data.delay / data.departures if data.departures > 0 else 0
        results.append({
            'Arrival Rate': ARRIVAL,
            'Arrivals': data.arrivals,
            'Departures': data.departures,
            'Avg Users': data.average_users / time if time > 0 else 0,
            'Avg Delay': average_delay,
            'Loss Rate': data.loss_probability if data.arrivals > 0 else 0,
            'Avg Waiting Delay': data.waiting_delay / data.departures if data.departures > 0 else 0,
            'Avg Buffer Occupancy': data.buffer_occupancy,
            'Busy Time': data.busy_time
        })
        delays.append(average_delay)
        loss_rates.append(data.loss_probability if data.arrivals > 0 else 0)
        average_users_list.append(data.average_users / time if time > 0 else 0)

    # Imposta le opzioni di visualizzazione di pandas per mostrare tutte le colonne
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    # Creazione di un DataFrame per visualizzare i risultati in modo tabellare
    df_results = pd.DataFrame(results)
    print(df_results)

    # Plot of Average Delay vs Arrival Rate
    plt.figure(figsize=(10, 6))
    plt.plot(ARRIVAL_RATES, delays, marker='o', linestyle='-')
    plt.title('Average Delay vs Arrival Rate')
    plt.xlabel('Arrival Rate')
    plt.ylabel('Average Delay')
    plt.grid(True)
    plt.show()

    # Plot of Loss Probability vs Arrival Rate
    plt.figure(figsize=(10, 6))
    plt.plot(ARRIVAL_RATES, loss_rates, marker='s', color='r', linestyle='--')
    plt.title('Loss Probability vs Arrival Rate')
    plt.xlabel('Arrival Rate')
    plt.ylabel('Loss Probability')
    plt.grid(True)
    plt.show()

    # Plot of Average Number of Users vs Arrival Rate
    plt.figure(figsize=(10, 6))
    plt.plot(ARRIVAL_RATES, average_users_list, marker='^', color='g', linestyle='-.')
    plt.title('Average Number of Users vs Arrival Rate')
    plt.xlabel('Arrival Rate')
    plt.ylabel('Average Number of Users')
    plt.grid(True)
    plt.show()

