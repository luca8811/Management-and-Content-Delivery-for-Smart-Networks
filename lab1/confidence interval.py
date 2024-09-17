import math
from scipy.stats import t
import matplotlib.pyplot as plt
import numpy as np


def compute_variance(sample):
    sample_size = len(sample)
    sample_mean = sum(sample) / sample_size
    variance = sum((x - sample_mean) ** 2 for x in sample) / (sample_size - 1)
    return variance


def compute_confidence_interval(sample, confidence_level):
    sample_size = len(sample)
    if sample_size < 2:
        raise ValueError("Il campione deve avere almeno due elementi per calcolare l'intervallo di confidenza.")

    sample_mean = sum(sample) / sample_size
    sample_variance = compute_variance(sample)
    sample_std_dev = math.sqrt(sample_variance)

    standard_error = sample_std_dev / math.sqrt(sample_size)
    degrees_of_freedom = sample_size - 1

    t_value = t.ppf((1 + confidence_level) / 2, degrees_of_freedom)
    margin_of_error = t_value * standard_error

    return sample_mean, sample_mean - margin_of_error, sample_mean + margin_of_error


# Dati delle simulazioni per ciascun tasso di arrivo
sample_data = {
    0.1: [14.9737, 15.2640, 15.0828, 14.8079, 14.9794, 15.1632, 14.8053, 15.0729],
    0.5: [14.9739, 14.9349, 15.1308, 14.9920, 14.6847, 15.0223, 14.9837, 15.1082],
    0.9: [14.8490, 14.8987, 14.7074, 14.7832, 14.9852, 14.8890, 14.9818, 15.0973],
    1.1: [15.0463, 14.8234, 14.9054, 15.1332, 15.0678, 14.8127, 14.7803, 15.0084],
    1.5: [14.9691, 14.8547, 14.9707, 15.1116, 15.1202, 14.9904, 15.0124, 14.9962]
}

confidence_level = 0.95

arrival_rates = []
means = []
ci_lower = []
ci_upper = []

# Calcola le medie e gli intervalli di confidenza per ogni tasso di arrivo
for arrival_rate, sample_data_arrival in sorted(sample_data.items()):
    mean, lower, upper = compute_confidence_interval(sample_data_arrival, confidence_level)
    arrival_rates.append(arrival_rate)
    means.append(mean)
    ci_lower.append(lower)
    ci_upper.append(upper)

    print(f"Tasso di Arrivo {arrival_rate}:")
    print(f"  Media: {mean}")
    print(f"  Intervallo di confidenza al {confidence_level * 100}%: ({lower}, {upper})\n")

# Converti le liste in array numpy
arrival_rates = np.array(arrival_rates)
means = np.array(means)
ci_lower = np.array(ci_lower)
ci_upper = np.array(ci_upper)

# Crea il grafico senza scale factor
plt.figure(figsize=(10, 6))
plt.plot(arrival_rates, means, 'b-', label="Mean Average Delay")
plt.fill_between(arrival_rates, ci_lower, ci_upper, color='blue', alpha=0.2, label="Confidence Interval 95%")

plt.title('Average Delay con Intervalli di Confidenza al 95%')
plt.xlabel('Tasso di Arrivo')
plt.ylabel('Average Delay')
plt.grid(True)
plt.legend(loc="best")
plt.show()
