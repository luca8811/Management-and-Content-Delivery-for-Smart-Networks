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


def plot_average_delay_over_departure_logarithmic(measurements: Measurements):
    plt.figure()
    lot = list(map(lambda m: (m.departures, m.average_delay), measurements.history))
    departures, delay = list(zip(*lot))
    plt.figure(figsize=(10, 6))
    plt.plot(departures, delay)
    plt.xscale('log')
    plt.xlabel('Departures')
    plt.ylabel('Average Delay (units)')
    plt.grid()
    plt.title('Average Delay Over Departures (logarithmic scale)')
    output_filename = "./report_images/average_delay_over_departure.png"
    plt.savefig(output_filename)
    plt.close()


def plot_average_losses_over_time(measurements: Measurements):
    plt.figure()
    lot = list(map(lambda m: (m.time, m.average_losses), measurements.history))
    time, losses = list(zip(*lot))
    plt.figure(figsize=(10, 6))
    plt.plot(time, losses)
    plt.xscale("log")
    plt.xlabel('Time')
    plt.ylabel('Average Losses (units)')
    plt.grid()
    plt.title('Average Losses Over Time')
    output_filename = "./report_images/average_losses_over_time.png"
    plt.savefig(output_filename)
    plt.close()


def plot_average_delay_over_time_logarithmic(measurements):
    """
    Visualizza il grafico del ritardo medio (average delay) con scala logaritmica sull'asse X
    e con i tick equidistanti, visualizzati come numeri interi.
    """
    lot = list(map(lambda m: (m.average_delay, m.time), measurements.history))
    average_delay, time = list(zip(*lot))
    plt.figure(figsize=(10, 6))
    plt.plot(time, average_delay, label="Average Delay")
    plt.xscale('log')
    plt.title("Average Delay Over Time (log scale)")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Average Delay (units)")
    plt.legend()
    plt.grid(True)
    output_filename = "./report_images/average_delay_over_time_logarithmic_scale.png"
    plt.savefig(output_filename)
    plt.close()


def plot_average_delay_with_warmup(measurements, warmup_end_time):
    """
    Visualizza il grafico del ritardo medio (average delay) con indicazione della fine del warm-up period e con un tick sull'asse X.
    """
    lot = list(map(lambda m: (m.average_delay, m.time), measurements.history))
    average_delay, time = list(zip(*lot))
    plt.figure(figsize=(10, 6))
    plt.plot(time, average_delay, label="Average Delay")
    plt.axvline(x=warmup_end_time, color='r', linestyle='--',
                label=f"End of Warm-up Period\n(t={warmup_end_time:.2f} seconds)")
    plt.xscale('log')
    plt.title("Average Delay Over Time (logarithmic scale)")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Average Delay (units)")
    plt.legend()
    plt.grid(True)
    output_filename = "./report_images/warmup_average_delay_over_time.png"
    plt.savefig(output_filename)
    plt.close()


def plot_average_users_over_time_logarithmic(measurements: Measurements):
    lot = list(map(lambda m: (m.average_users, m.time), measurements.history))
    avg_users, time = list(zip(*lot))
    plt.figure(figsize=(10, 6))
    plt.plot(time, avg_users, label="Average Users")
    plt.title("Average Users Over Time (log scale)")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Average Users (units)")
    plt.legend()
    plt.grid(True)
    output_filename = "./report_images/average_users_over_time_logarithmic_scale.png"
    plt.savefig(output_filename)
    plt.close()
