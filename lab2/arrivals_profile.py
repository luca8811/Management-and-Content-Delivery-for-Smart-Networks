import numpy as np
from scipy.interpolate import PchipInterpolator  # Per spline monotona
import matplotlib.pyplot as plt

use_custom_profile = True

# Definition of interpolation nodes
t_nodes = np.array([0, 5, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 23, 24])
A_nodes = np.array([1, 1, 2, 3, 5, 5, 3, 2, 3, 5, 5, 2, 1, 1]) / 5

# Monotonic spline interpolation (PCHIP)
pchip_interp = PchipInterpolator(t_nodes, A_nodes)

# Interpolation on a finer time scale
t_fine = np.linspace(0, 24, 300)
arrivals_profile = pchip_interp(t_fine)

# Clipping values to be within [0, 1]
arrivals_profile = np.clip(arrivals_profile, 0, 1)

# Plot with improved aesthetics
if __name__ == "__main__":
    plt.figure(figsize=(10, 5))
    plt.plot(t_fine, arrivals_profile, '-', label='Monotonic spline fit', color='orange', linewidth=2)
    plt.plot(t_nodes, A_nodes, 'o', label='Interpolation nodes', color='blue', markersize=8)
    plt.xlabel('Time (hours)', fontsize=12)
    plt.ylabel('Arrival Rate', fontsize=12)
    plt.title('Arrival Rates Profile', fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(linestyle='--', linewidth=.4)

    # Set yticks to match the unique values in A_nodes
    unique_A_nodes = np.unique(A_nodes)  # Remove duplicates for clean Y ticks
    plt.yticks(unique_A_nodes)  # Set Y ticks to A_nodes values

    plt.xticks(np.arange(0, 25, step=1))  # Display every 1 hours
    plt.tight_layout()  # Better spacing

    # Save the figure
    output_filename = "./report_images/arrivals_rate_per_hour.png"
    plt.savefig(output_filename)
    plt.close()
