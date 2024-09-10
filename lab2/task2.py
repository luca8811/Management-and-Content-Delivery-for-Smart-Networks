import random
from queue import PriorityQueue
import lab2
import results_visualization
from lab2 import Event, evt_arrival, evt_departure, evt_recharge, evt_switch_off
from utils.queues import MMmB

lab2.init_variables("TASK2")
variables = lab2.variables
MMms = lab2.MMms
measurements = lab2.measurements
data = lab2.data

drone_types = variables['drone_types']
for i, drone_type in enumerate(variables['configurations']['I']):
    drone = drone_types[drone_type]
    MMms[i] = MMmB(power_supply=drone['POW'],
                   service_times=[1 / (variables['BASE_SERVICE_RATE'] * drone['SERVICE_RATE'])
                                  for m in range(drone['m_ANTENNAS'])],
                   buffer_size=variables['BASE_BUFFER_SIZE'] * drone['BUFFER_SIZE'])


if __name__ == '__main__':
    random.seed(42)

    # the simulation time
    time = 0

    # the list of events in the form: (time, evt_type, drone_id*, additional_parameters*)
    # * -> if needed
    FES = PriorityQueue()

    # schedule the first arrival at t=0, in order to make the simulation start.
    FES.put((0, Event.ARRIVAL, None, None))

    # simulate until the simulated time reaches a constant
    while time < variables['SIM_TIME']:
        (time, event_type, drone_id, arg) = FES.get()

        if event_type == Event.ARRIVAL:
            evt_arrival(time, FES)
        elif event_type == Event.DEPARTURE:
            evt_departure(time, FES, drone_id, arg)
        elif event_type == Event.SWITCH_OFF:
            evt_switch_off(time, FES, drone_id, arg)
        elif event_type == Event.RECHARGE:
            evt_recharge(time, drone_id)

    results_visualization.STARTING_TIME = variables['STARTING_TIME']
    results_visualization.plot_users(measurements)
    results_visualization.plot_arrivals(measurements)
    results_visualization.plot_departures(measurements)
    results_visualization.plot_losses(measurements)
    results_visualization.plot_dep_los(measurements)
    results_visualization.plot_drones(measurements)
    results_visualization.plot_delay(measurements)
    results_visualization.plot_average_delay_over_time_logarithmic(measurements)

    # print output data
    print("MEASUREMENTS \n\nNo. of users in the queue:", data.users, "\nNo. of arrivals =",
          data.arrivals, "- No. of departures =", data.departures)

    print("\nArrival rate: ", data.arrivals / time, " - Departure rate: ", data.departures / time)
    print("Loss rate: ", data.losses / time, " - Packets loss: ", data.losses)
    print("Departures-losses ratio: ", data.departures / data.losses)
    print("Departures percentage: {:.1f}%".format(data.departures / data.arrivals * 100))

    print("\nAverage number of users: ", data.average_users / time)
    print("Average delay: ", data.delay / data.departures)
