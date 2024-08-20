import pandas as pd

# Load the data from CSV file
data = pd.read_csv('/Users/lucabernardi/PycharmProjects/Management/lab1/simulation_results.csv')

import seaborn as sns
import matplotlib.pyplot as plt

# Define the metrics to plot
import seaborn as sns
import matplotlib.pyplot as plt

# Set the aesthetic style of the plots
sns.set(style="whitegrid")

# Define the metrics to plot
metrics = [
    'No. of Users in Queue', 'No. of Arrivals', 'No. of Departures',
    'Arrival Rate', 'Departure Rate', 'Loss Rate', 'Packets Lost',
    'Average No. of Users', 'Average Delay'
]

# Create a plot for each metric
for metric in metrics:
    plt.figure(figsize=(10, 6))  # Create a new figure for each plot
    sns.lineplot(data=data, x='Arrival Rate', y=metric, hue='Buffer Size', style='Buffer Size', markers=True, dashes=False)
    plt.title(f'{metric} vs. Arrival Rate for Different Buffer Sizes')
    plt.xlabel('Arrival Rate')
    plt.ylabel(metric)
    plt.legend(title='Buffer Size')
    plt.show()
