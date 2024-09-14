import time

import matplotlib.pyplot as plt
import json
from utils.measurements import Measurements
import pandas as pd
from datetime import datetime

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
    t = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    output_filename = f"./report_images/users_over_time_{t}.png"
    plt.savefig(output_filename)
    plt.close()


def plot_users_with_warmup(measurements: Measurements, warmup_times):
    plt.figure()

    # Extract time and users from the measurements
    lot = list(map(lambda m: (m.time, m.users), measurements.history))
    times, users = list(zip(*lot))

    # Plot the users over time
    plt.plot(times, users)

    # Add vertical dashed red lines at each warmup time
    for warmup_time in warmup_times:
        plt.axvline(x=warmup_time, color='r', linestyle='--',
                    label=f'Warmup @ {warmup_time}' if warmup_time == warmup_times[0] else "")

    # Labels and grid
    plt.xlabel('time')
    plt.ylabel('number of users')
    plt.grid()
    plt.title('Users over time with end of warm-up period')

    # Save the figure
    output_filename = "./report_images/average_users_over_time_with warmup.png"
    plt.savefig(output_filename)
    plt.close()


def plot_users_with_steady_state(measurements: Measurements):

    json_filepath = "./report_images/steady_state_working_slots.json"

    plt.figure()

    # Extract time and users from the measurements
    lot = list(map(lambda m: (m.time, m.users), measurements.history))
    times, users = list(zip(*lot))

    # Plot the users over time
    plt.plot(times, users)

    # Load the steady-state working slots from the JSON file
    with open(json_filepath, 'r') as json_file:
        steady_state_slots = json.load(json_file)

    # Add vertical blue lines for each steady-state slot
    for slot in steady_state_slots:
        start, end = slot
        # Plot blue lines for both the start and the end of each steady-state period
        plt.axvline(x=start, color='b', linestyle='--',
                    label=f'Start steady @ {start}' if start == steady_state_slots[0][0] else "")
        plt.axvline(x=end, color='b', linestyle='--',
                    label=f'End steady @ {end}' if end == steady_state_slots[0][0] else "")

    # Labels and grid
    plt.xlabel('time')
    plt.ylabel('number of users')
    plt.grid()
    plt.title('Users over time with steady state periods')

    # Save the figure
    output_filename = "./report_images/average_users_with_steady_state.png"
    plt.savefig(output_filename)
    plt.close()


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


def compare_metrics(data, filtered_measurements):
    """
    Compare overall and steady-state metrics in a tabular format and plot the results.

    Args:
        data: The overall measurements.
        filtered_measurements: The filtered measurements for steady-state data.

    Returns:
        A DataFrame containing the comparison of overall and steady-state metrics.
    """
    # Prepare data for comparison
    comparison_data = {
        'Metric': [
            'Users in Queue', 'Total Arrivals', 'Total Departures', 'Total Losses',
            'Arrival Rate', 'Departure Rate', 'Loss Rate', 'Departures-Losses Ratio',
            'Departures Percentage', 'Average Users', 'Average Delay'
        ],
        'Overall': [
            data.users, data.arrivals, data.departures, data.losses,
            data.arrivals / data.time, data.departures / data.time, data.losses / data.time,
            data.departures / data.losses if data.losses > 0 else "N/A",
            data.departures / data.arrivals * 100 if data.arrivals > 0 else "N/A",
            data.average_users / data.time, data.delay / data.departures if data.departures > 0 else "N/A"
        ],
        'Steady-State': [
            filtered_measurements.users, filtered_measurements.total_arrivals,
            filtered_measurements.total_departures, filtered_measurements.total_losses,
            filtered_measurements.steady_state_arrival_rate, filtered_measurements.steady_state_departure_rate,
            filtered_measurements.steady_state_loss_rate,
            filtered_measurements.total_departures / filtered_measurements.total_losses if filtered_measurements.total_losses > 0 else "N/A",
            filtered_measurements.total_departures / filtered_measurements.total_arrivals * 100 if filtered_measurements.total_arrivals > 0 else "N/A",
            filtered_measurements.average_users, filtered_measurements.average_delay
        ]
    }

    # Create a DataFrame to organize the data
    df_comparison = pd.DataFrame(comparison_data)

    # Plot comparison table using pandas
    fig, ax = plt.subplots(figsize=(10, 5))  # Adjust the size of the figure
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=df_comparison.values, colLabels=df_comparison.columns, cellLoc='center', loc='center')
    output_filename = "./report_images/steady_state_vs_overall_simulation.png"
    plt.savefig(output_filename)
    plt.close()

    return df_comparison
