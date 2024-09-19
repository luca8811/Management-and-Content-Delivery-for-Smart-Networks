import matplotlib.pyplot as plt
import json
from utils.measurements import Measurements
import pandas as pd
import re

SIM_START = 0


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
                    label=f'End of Warm-up Transient')

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
    plt.subplots(figsize=(14, 8))
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
    plt.title('Users over Time with Steady State')

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


def compare_metrics(data, filtered_measurements, title=None):
    """
    Compare overall and steady-state metrics in a tabular format and plot the results.

    Args:
        data: Original measurements.
        filtered_measurements: The filtered measurements for steady-state data.
        title: Optional custom title for the plot. If None, no additional title is added.

    Returns:
        A DataFrame containing the comparison of overall and steady-state metrics.
    """

    def round_if_number(value):
        """Helper function to round a number to 3 decimal places, or return 'N/A'."""
        if isinstance(value, (int, float)):
            return round(value, 3)
        return value

    # Prepare data for comparison
    comparison_data = {
        'Metric': [
            'Working Time', 'Total Arrivals', 'Total Departures', 'Total Losses',
            'Arrival Rate', 'Departure Rate', 'Loss Rate', 'Departures-Losses Ratio',
            'Departures Percentage', 'Average Users', 'Average Delay'
        ],
        "Warm-up transient": [
            round_if_number(filtered_measurements.warmup_interval),
            round_if_number(filtered_measurements.warmup_arrivals),
            round_if_number(filtered_measurements.warmup_departures),
            round_if_number(filtered_measurements.warmup_losses),

            round_if_number(filtered_measurements.warmup_arrivals / filtered_measurements.warmup_interval),
            round_if_number(filtered_measurements.warmup_departures / filtered_measurements.warmup_interval),
            round_if_number(filtered_measurements.warmup_losses / filtered_measurements.warmup_interval),

            round_if_number(
                filtered_measurements.warmup_departures / filtered_measurements.warmup_losses) if filtered_measurements.warmup_losses > 0 else "N/A",
            round_if_number(
                filtered_measurements.warmup_departures / filtered_measurements.warmup_arrivals * 100) if filtered_measurements.warmup_arrivals > 0 else "N/A",

            round_if_number(filtered_measurements.warmup_total_users / filtered_measurements.warmup_interval),
            round_if_number(
                filtered_measurements.warmup_delays / filtered_measurements.warmup_departures) if filtered_measurements.warmup_departures > 0 else "N/A"
        ],
        'Steady-State': [
            round_if_number(filtered_measurements.steady_state_interval),
            round_if_number(filtered_measurements.arrivals),
            round_if_number(filtered_measurements.departures),
            round_if_number(filtered_measurements.losses),

            round_if_number(filtered_measurements.arrivals / filtered_measurements.steady_state_interval),
            round_if_number(filtered_measurements.departures / filtered_measurements.steady_state_interval),
            round_if_number(filtered_measurements.losses / filtered_measurements.steady_state_interval),

            round_if_number(
                filtered_measurements.departures / filtered_measurements.losses) if filtered_measurements.losses > 0 else "N/A",
            round_if_number(
                filtered_measurements.departures / filtered_measurements.arrivals * 100) if filtered_measurements.arrivals > 0 else "N/A",

            round_if_number(filtered_measurements.total_users / filtered_measurements.steady_state_interval),
            round_if_number(
                filtered_measurements.delay / filtered_measurements.departures) if filtered_measurements.departures > 0 else "N/A"
        ],
        'Overall': [
            round_if_number(data.working_interval),
            round_if_number(data.arrivals),
            round_if_number(data.departures),
            round_if_number(data.losses),

            round_if_number(data.arrivals / data.working_interval),
            round_if_number(data.departures / data.working_interval),
            round_if_number(data.losses / data.working_interval),

            round_if_number(data.departures / data.losses) if data.losses > 0 else "N/A",
            round_if_number(data.departures / data.arrivals * 100) if data.arrivals > 0 else "N/A",

            round_if_number(data.total_users / data.working_interval),
            round_if_number(data.delay / data.departures) if data.departures > 0 else "N/A"
        ],
    }

    # Create a DataFrame to organize the data
    df_comparison = pd.DataFrame(comparison_data)

    # Plot comparison table using pandas
    fig, ax = plt.subplots(figsize=(10, 5))  # Adjust the size of the figure
    ax.axis('tight')
    ax.axis('off')

    # Create the table
    table = ax.table(cellText=df_comparison.values, colLabels=df_comparison.columns, cellLoc='center', loc='center')

    # Format table: Adjust column width, font size, and borders
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)  # Scale the table to fit better in the plot

    # Set cell properties (add borders and change background color for headers)
    for (i, j), cell in table.get_celld().items():
        if i == 0:  # Header row
            cell.set_fontsize(11)
            cell.set_text_props(weight='bold')
            cell.set_edgecolor('black')
            cell.set_facecolor('#d9d9d9')  # Lighter grey background for the header
        else:
            cell.set_edgecolor('black')

    # Add title if provided
    base_title = "Comparison of Metrics: Warm-up, Steady-State, and Overall"
    if title:
        plt.title(f"{base_title}\n{title}", fontsize=14, fontweight='bold', pad=10)
    else:
        plt.title(base_title, fontsize=14, fontweight='bold', pad=10)

    # Clean up the title for file naming (replace invalid characters like ':' with '_')
    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title or 'default')

    # Save the plot
    output_filename = f"./report_images/steady_state_vs_overall_simulation_{safe_title}.png"
    plt.savefig(output_filename, bbox_inches='tight')
    plt.close()

    return df_comparison


# Function to load the json file and generate the required plots
def plot_simulation_data(file_path):
    # Load the JSON data
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Prepare data for plotting
    schedules = list(data.keys())

    # Extracting relevant values
    arrival_rates = [data[schedule]["Arrival Rate"] for schedule in schedules]
    departure_rates = [data[schedule]["Departure Rate"] for schedule in schedules]
    loss_rates = [data[schedule]["Loss Rate"] for schedule in schedules]
    departure_percentages = [data[schedule]["Departures Percentage"] for schedule in schedules]
    average_users = [data[schedule]["Average Users"] for schedule in schedules]
    average_delays = [data[schedule]["Average Delay"] for schedule in schedules]

    # Define a color palette with shades of blue and reduced bar width
    colors = ['#A9D6E5', '#89C2D9', '#61A5C2', '#468FAF']
    bar_width = 0.5

    # Create subplots with shades of blue and reduced bar width
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))

    # Subplot 1: Arrival Rate, Departure Rate, and Loss Rate
    axes[0, 0].bar(schedules, arrival_rates, label='Arrival Rate', color=colors[0], alpha=0.85, width=bar_width)
    axes[0, 0].bar(schedules, loss_rates, label='Loss Rate', color=colors[1], alpha=0.85, width=bar_width)
    axes[0, 0].bar(schedules, departure_rates, label='Departure Rate', color=colors[3], alpha=0.85, width=bar_width)
    axes[0, 0].set_title('Arrival Rate, Departure Rate, and Loss Rate')
    axes[0, 0].legend()

    # Subplot 2: Departure Percentage
    axes[0, 1].bar(schedules, departure_percentages, color=colors[1], width=bar_width)
    axes[0, 1].set_title('Departure Percentage')

    # Subplot 3: Average Users
    axes[1, 0].bar(schedules, average_users, color=colors[2], width=bar_width)
    axes[1, 0].set_title('Average Users')

    # Subplot 4: Average Delays
    axes[1, 1].bar(schedules, average_delays, color=colors[3], width=bar_width)
    axes[1, 1].set_title('Average Delays')

    # Adjust layout
    plt.tight_layout()

    # Save the plot
    output_filename = f"./report_images/plot_result_simulation.png"
    plt.savefig(output_filename, bbox_inches='tight')
    plt.close()
