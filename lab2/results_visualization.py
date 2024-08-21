import matplotlib.pyplot as plt
from utils.measurements import Measurements

STARTING_TIME = 0


def plot_users(measurements: Measurements):
    plt.figure()
    times, users_count = measurements.dispatch_users(STARTING_TIME)
    plt.plot(times, users_count)
    plt.xlabel('time')
    plt.ylabel('number of users')
    plt.grid()
    plt.title('Users over time')
    plt.show()


def plot_arrivals(measurements: Measurements):
    plt.figure()
    times, arrivals_count = measurements.dispatch_arrivals(STARTING_TIME)
    plt.plot(times, arrivals_count)
    plt.xlabel('time (hours)')
    plt.ylabel('number of arrivals')
    plt.grid()
    plt.title('Arrivals over time')
    plt.show()


def plot_departures(measurements: Measurements):
    plt.figure()
    times, departures_count = measurements.dispatch_departures(STARTING_TIME)
    plt.plot(times, departures_count)
    plt.xlabel('time (hours)')
    plt.ylabel('number of departures')
    plt.grid()
    plt.title('Departures over time')
    plt.show()


def plot_losses(measurements: Measurements):
    plt.figure()
    times, losses_count = measurements.dispatch_losses(STARTING_TIME)
    plt.plot(times, losses_count)
    plt.xlabel('time (hours)')
    plt.ylabel('number of losses')
    plt.grid()
    plt.title('Losses over time')
    plt.show()


def plot_delay(measurements: Measurements):
    plt.figure()
    times, delay_count = measurements.dispatch_delay(STARTING_TIME)
    plt.plot(times, delay_count)
    plt.xlabel('time (hours)')
    plt.ylabel('delay (units)')
    plt.grid()
    plt.title('Delay over time')
    plt.show()
