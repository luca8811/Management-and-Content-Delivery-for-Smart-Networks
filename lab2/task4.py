import random
from queue import PriorityQueue

import lab2
import results_visualization
from lab2 import Event, evt_arrival, evt_departure, evt_recharge, evt_switch_off
from utils.measurements import Measurement, Measurements
from utils.queues import MMmB

lab2.init_variables('TASK4')
variables = lab2.variables
drone_types = variables['drone_types']

# Control plane for simulation configuration and results visualization
run_specific_simulations = True
specific_simulations = {
    'drones_configuration': ['I', 'II', 'III'],
    'working_slots': ['II']
}
want_print_results = True
want_plot_results = False


def run_simulation(working_slots, drones_configuration, seed=0):
    lab2.init_simulation_environment()
    MMms = lab2.MMms
    data = lab2.data
    measurements = lab2.measurements
    for i, drone_type in enumerate(drones_configuration):
        drone = drone_types[drone_type]
        MMms[i] = MMmB(power_supply=drone['POW'],
                       service_times=[1 / (variables['BASE_SERVICE_RATE'] * drone['SERVICE_RATE'])
                                      for m in range(drone['m_ANTENNAS'])],
                       buffer_size=variables['BASE_BUFFER_SIZE'] * drone['BUFFER_SIZE'],
                       working_slots=working_slots)
    random.seed(seed)
    # the simulation time
    time = variables['SIM_START']
    # the list of events in the form: (time, evt_type, drone_id*, additional_parameters*)
    # * -> if needed
    FES = PriorityQueue()
    # schedule the first arrival at t=0, in order to make the simulation start.
    FES.put((variables['SIM_START'], Event.ARRIVAL, None, None))
    # simulate until the simulated time reaches a constant
    while time < variables['SIM_START'] + variables['SIM_TIME']:
        (time, event_type, drone_id, arg) = FES.get()
        if event_type == Event.ARRIVAL:
            evt_arrival(time, FES)
        elif event_type == Event.DEPARTURE:
            evt_departure(time, FES, drone_id, arg)
        elif event_type == Event.SWITCH_OFF:
            evt_switch_off(time, FES, drone_id, arg)
        elif event_type == Event.RECHARGE:
            evt_recharge(time, drone_id)
    return data, measurements


def print_results(data: Measurement):
    print('No. of users in the queue:', data.users)
    print('No. of arrivals =', data.arrivals, '- No. of departures =', data.departures)
    print('Measured arrival rate: ', data.arrivals / sim_time, ' - Measured departure rate: ',
          data.departures / sim_time)
    print('Loss rate: ', data.losses / sim_time, ' - Packets lost: ', data.losses)
    print('Departures-losses ratio: ', data.departures / data.losses)
    print('Departures percentage: {:.1f}%'.format(data.departures / data.arrivals * 100))
    print('Average number of users: ', data.average_users / sim_time)
    print('Average delay: ', data.delay / data.departures)
    # print('Complete discharging/charging cycles: ', data.)


def plot_results(measurements: Measurements):
    results_visualization.plot_users(measurements)
    # results_visualization.plot_arrivals(measurements)
    # results_visualization.plot_departures(measurements)
    # results_visualization.plot_losses(measurements)
    # results_visualization.plot_dep_los(measurements)
    results_visualization.plot_drones(measurements)
    # results_visualization.plot_delay(measurements)


if __name__ == '__main__':
    sim_start = variables['SIM_START']
    sim_time = variables['SIM_TIME']
    sim_stop = sim_start + sim_time
    results_visualization.SIM_START = sim_start

    if not run_specific_simulations:
        drones_configurations = variables['configurations'].keys()
        working_slots = variables['WORKING_SCHEDULING'].keys()
    else:
        drones_configurations = specific_simulations['drones_configuration']
        working_slots = specific_simulations['working_slots']
    for drones_configuration in drones_configurations:
        for working_scheduling in working_slots:
            print('\nRunning simulation with drones configuration ', drones_configuration)
            data, measurements = run_simulation(working_slots=variables['WORKING_SCHEDULING'][working_scheduling],
                                                drones_configuration=variables['configurations'][drones_configuration])
            if want_print_results:
                print_results(data)
            if want_plot_results:
                plot_results(measurements)
