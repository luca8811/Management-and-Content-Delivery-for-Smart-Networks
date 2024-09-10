import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

use_custom_profile = True

# Definition of interpolation nodes
t_nodes = np.array([0, 5, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 23, 24])
A_nodes = np.array([1, 1, 2, 3, 5, 5, 3, 2, 3, 5, 5, 2, 1, 1]) / 5
# A_nodes = np.array([3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]) / 5

# Creation of linear interpolation function
linear_interp = interp1d(t_nodes, A_nodes, kind='linear')

# Interpolation on all the hours in a day
t = np.linspace(0, 24, 25)
if use_custom_profile:
    arrivals_profile = linear_interp(t)
else:
    arrivals_profile = np.ones(shape=(25,))

if __name__ == "__main__":
    plt.figure(figsize=(10, 5))
    plt.plot(t_nodes, A_nodes, 'o', label='Interpolation nodes')
    plt.plot(t, arrivals_profile, '-', label='Complete profile')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Arrival rates profile')
    plt.legend()
    plt.grid(True)
    plt.show()
