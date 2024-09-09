import random
from queue import PriorityQueue
import numpy as np
import lab2
import results_visualization
from lab2 import Event, evt_arrival, evt_departure, evt_recharge, evt_switch_off
from utils.queues import MMmB

lab2.init_variables("TASK1")
variables = lab2.variables
MMms = lab2.MMms
measurements = lab2.measurements
data = lab2.data

drone_types = variables['drone_types']
for i, drone_type in enumerate(variables['configurations']['I']):
    drone = drone_types[drone_type]
    MMms[i] = MMmB(power_supply=drone['POW'],
                   service_times=[1 / (variables['BASE_SERVICE_RATE'] * drone['SERVICE_RATE'])
                                  for m in range(drone['m_ANTENNAS'])],
                   buffer_size=variables['BASE_BUFFER_SIZE'] * drone['BUFFER_SIZE'])

def find_end_of_warmup_period(measurements):
    # Estrai i dati per il grafico
    lot = list(map(lambda m: (m.departures, m.average_delay, m.time), measurements.history))
    departures, average_delay, time = list(zip(*lot))

    return


def calculate_warmup_period(measurements, window_size, threshold):
    """
    Calcola il warm-up period utilizzando una media mobile su una metrica (ad esempio, numero di utenti o ritardo medio).

    Parametri:
        - data: Lista o array contenente la metrica di interesse (ad esempio, numero di utenti nel tempo).
        - window_size: Dimensione della finestra per la media mobile.
        - threshold: Soglia di variazione relativa per determinare quando il sistema è stabile.

    Restituisce:
        - Il tempo (indice) in cui il warm-up period termina.
    """
    # Estrai i dati per il grafico
    lot = list(map(lambda m: (m.departures, m.average_delay, m.time), measurements.history))
    departures, average_delay, time = list(zip(*lot))

    # Calcola la media mobile sui dati
    moving_avg = np.convolve(average_delay, np.ones(window_size) / window_size, mode='valid')

    # Analizza la variazione relativa tra medie mobili successive
    for i in range(1, len(moving_avg)):
        variation = abs((moving_avg[i] - moving_avg[i - 1]) / moving_avg[i - 1])

        # Se la variazione è minore della soglia, consideriamo che il sistema è stabile
        if variation < threshold:
            warmup_period = i + window_size - 1  # Adjust to match the original data indexing
            return warmup_period

    # Se nessuna variazione soddisfa la soglia, restituisci il tempo massimo (fine dei dati)
    return len(average_delay) - 1


if __name__ == '__main__':
    random.seed(42)

    # the simulation time
    time = 0

    # the list of events in the form: (time, evt_type, drone_id*, additional_parameters*)
    # * -> if needed
    FES = PriorityQueue()

    # schedule the first arrival at t=0, in order to make the simulation start.
    FES.put((0, Event.ARRIVAL, None, None))

    # simulate until the simulated time reaches a constant
    while time < variables['SIM_TIME']:
        (time, event_type, drone_id, arg) = FES.get()

        if event_type == Event.ARRIVAL:
            evt_arrival(time, FES)
        elif event_type == Event.DEPARTURE:
            evt_departure(time, FES, drone_id, arg)
        elif event_type == Event.SWITCH_OFF:
            evt_switch_off(time, FES, drone_id, arg)
        elif event_type == Event.RECHARGE:
            evt_recharge(time, drone_id)

    a = calculate_warmup_period(measurements, 5, 0.05)
    print(a)
    results_visualization.STARTING_TIME = variables['STARTING_TIME']
    # results_visualization.plot_users(measurements)
    # results_visualization.plot_arrivals(measurements)
    results_visualization.plot_departures(measurements)
    # results_visualization.plot_losses(measurements)
    # results_visualization.plot_dep_los(measurements)
    # results_visualization.plot_drones(measurements)
    # results_visualization.plot_delay(measurements)
    results_visualization.plot_average_delay_over_departure(measurements)
    results_visualization.plot_average_delay_over_time(measurements)
    # warmup_end_time = results_visualization.find_warmup_end(measurements)

    # print output data
    print("MEASUREMENTS \n\nNo. of users in the queue:", data.users, "\nNo. of arrivals =",
          data.arrivals, "- No. of departures =", data.departures)

    print("\nArrival rate: ", data.arrivals / time, " - Departure rate: ", data.departures / time)
    print("Loss rate: ", data.losses / time, " - Packets loss: ", data.losses)
    print("Departures-losses ratio: ", data.departures / data.losses)
    print("Departures percentage: {:.1f}%".format(data.departures / data.arrivals * 100))

    print("\nAverage number of users: ", data.average_users / time)
    print("Average delay: ", data.delay / data.departures)
