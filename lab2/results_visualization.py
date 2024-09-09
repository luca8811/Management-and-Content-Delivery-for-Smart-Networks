import matplotlib.pyplot as plt
import numpy as np
from utils.measurements import Measurements

STARTING_TIME = 0


def plot_users(measurements: Measurements):
    plt.figure()
    lot = list(map(lambda m: (m.time, m.users), measurements.history))
    times, users = list(zip(*lot))
    plt.plot(times, users)
    plt.xlabel('time')
    plt.ylabel('number of users')
    plt.grid()
    plt.title('Users over time')
    plt.show()


def plot_arrivals(measurements: Measurements):
    plt.figure()
    lot = list(map(lambda m: (m.time, m.arrivals), measurements.history))
    times, arrivals = list(zip(*lot))
    plt.plot(times, arrivals)
    plt.xlabel('time (hours)')
    plt.ylabel('number of arrivals')
    plt.grid()
    plt.title('Arrivals over time')
    plt.show()


def plot_departures(measurements: Measurements):
    plt.figure()
    lot = list(map(lambda m: (m.time, m.departures), measurements.history))
    times, departures = list(zip(*lot))
    plt.plot(times, departures)
    plt.xlabel('time (hours)')
    plt.ylabel('number of departures')
    plt.grid()
    plt.title('Departures over time')
    plt.show()


def plot_losses(measurements: Measurements):
    plt.figure()
    lot = list(map(lambda m: (m.time, m.losses), measurements.history))
    times, losses = list(zip(*lot))
    plt.plot(times, losses)
    plt.xlabel('time (hours)')
    plt.ylabel('number of losses')
    plt.grid()
    plt.title('Losses over time')
    plt.show()


def plot_dep_los(measurements: Measurements):
    plt.figure()
    lot = list(map(lambda m: (m.time, m.departures, m.losses), measurements.history))
    times, departures, losses = list(zip(*lot))
    plt.plot(times, departures)
    plt.plot(times, losses)
    plt.legend(["departures", "losses"])
    plt.xlabel('time (hours)')
    plt.ylabel('amount of packets')
    plt.grid()
    plt.title('Departures and losses over time')
    plt.show()


def plot_drones(measurements: Measurements):
    plt.figure()
    lot = list(map(lambda m: (m.time, m.drones, m.charging_drones), measurements.history))
    times, drones, charging_drones = list(zip(*lot))
    plt.plot(times, drones)
    plt.plot(times, charging_drones)
    plt.legend(['Drones', 'Charging drones'])
    plt.xlabel('time (hours)')
    plt.ylabel('drones (units)')
    plt.grid()
    plt.title('Number of drones over time')
    plt.show()


def plot_delay(measurements: Measurements):
    plt.figure()
    lot = list(map(lambda m: (m.time, m.delay), measurements.history))
    times, delay = list(zip(*lot))
    plt.plot(times, delay)
    plt.xlabel('time (hours)')
    plt.ylabel('delay (units)')
    plt.grid()
    plt.title('Delay over time')
    plt.show()


def plot_average_delay_over_departure(measurements: Measurements):
    plt.figure()

    # Estrai i dati per il grafico
    lot = list(map(lambda m: (m.departures, m.average_delay), measurements.history))
    times, delay = list(zip(*lot))

    # Crea il grafico
    plt.plot(times, delay)

    # Imposta la scala logaritmica per l'asse x
    plt.xscale('log')

    # Aggiungi etichette e titolo
    plt.xlabel('departures [log scale]')
    plt.ylabel('average delay (units)')
    plt.grid()
    plt.title('Average delay over departures (log scale)')

    # Mostra il grafico
    plt.show()


def plot_average_delay_over_time(measurements: Measurements):
    plt.figure()

    # Estrai i dati per il grafico
    lot = list(map(lambda m: (m.time/3600, m.average_delay), measurements.history))
    times, delay = list(zip(*lot))

    # Crea il grafico
    plt.plot(times, delay)

    # Aggiungi etichette e titolo
    plt.xlabel('time [hours]')
    plt.ylabel('average delay (units)')
    plt.grid()
    plt.title('Average delay over time (hours)')

    # Mostra il grafico
    plt.show()


def find_warmup_end(measurements: Measurements):
    # Estrai i dati del ritardo medio e del tempo dal dataset
    lot = list(map(lambda m: (m.time/60*60, m.average_delay), measurements.history))
    times, delays = list(zip(*lot))

    # Calcoliamo le differenze tra i ritardi medi successivi
    delay_diff = np.diff(delays)

    # Calcoliamo il valore assoluto della differenza (per misurare le variazioni)
    abs_diff = np.abs(delay_diff)

    # Troviamo il punto in cui le variazioni diventano costantemente piccole
    threshold = 1e-3  # soglia per considerare "piccola" una variazione
    stable_index = np.where(abs_diff < threshold)[0]

    if len(stable_index) > 0:
        # Prendiamo il primo punto in cui le variazioni diventano costantemente piccole
        warmup_end_index = stable_index[0]
        print("warm-up index", warmup_end_index)

        # Troviamo il tempo corrispondente
        warmup_end_time = times[warmup_end_index]

        print(f"Il warm-up period termina a t = {warmup_end_time} ore")

        # Tracciare il punto sul grafico
        plt.figure()
        plt.plot(times, delays, label="Average Delay")
        plt.axvline(x=warmup_end_time, color='red', linestyle='--', label='Fine del Warm-up')
        plt.xlabel('time (hours)')
        plt.ylabel('average delay (units)')
        plt.grid()
        plt.title('Average delay over time')
        plt.legend()
        plt.show()

        return warmup_end_time
    else:
        print("Non è stato possibile trovare un punto in cui il sistema si stabilizza.")
        return None

