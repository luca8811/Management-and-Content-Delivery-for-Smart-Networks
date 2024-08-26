import random
from enum import Enum


class Packet:
    def __init__(self, arrival_time):
        self.arrival_time = arrival_time


class Server:
    def __init__(self, service_time):
        self.idle = True  # whether the server is idle or not
        self.service_time = service_time  # service period specific for this server


residual_time_max = {
    "BAT": 25 * 60,
    "W45": 35 * 60,
    "W65": 40 * 60,
    "W75": 45 * 60
}


class BatteryStatus(Enum):
    EMPTY = 1
    FULL = 2
    IN_USE = 3
    PAUSED = 4


class Battery:
    RECHARGE_TIME = 3600
    MAX_CYCLES = 3

    def __init__(self, power_supply: str):
        self._max_residual_time: int = residual_time_max[power_supply]
        self.residual: int = 0
        self.status: BatteryStatus = BatteryStatus.FULL
        self.complete_cycles: int = 0

    def init_battery(self, solar_panel=False):
        if solar_panel:
            self.residual = self._max_residual_time
        else:
            self.residual = residual_time_max["BAT"]


class MMmB:
    def __init__(self, power_supply: str, service_times: list[float], buffer_size=0):
        self.buffer_size = buffer_size  # B
        self.battery: Battery = Battery(power_supply)
        self._queue: list[Packet] = []
        self._servers: dict[int, Server] = {i: Server(service_times[i]) for i in range(len(service_times))}
        self._rr_scheduling: list[int] = list(self._servers.keys())
        self._scheduling_policy = self._get_server_fastest

    def battery_recharge(self):
        self.battery.status = BatteryStatus.FULL
        self.battery.complete_cycles += 1

    def battery_consume(self, usage_time):
        self.battery.residual -= usage_time

    def switch_on(self, solar_panel=False):
        self.battery.status = BatteryStatus.IN_USE
        self.battery.init_battery(solar_panel=solar_panel)

    def switch_off(self, empty_battery=True):
        for server in self._servers.values():
            server.idle = True
        self._queue.clear()
        self.battery.status = BatteryStatus.EMPTY if empty_battery else BatteryStatus.PAUSED

    def insert(self, packet: Packet):
        assert not self.is_queue_full()
        self._queue.append(packet)

    def queue_size(self):
        return len(self._queue)

    def is_queue_full(self):
        return self.queue_size() == self.buffer_size and self.buffer_size > 0

    def _get_servers_working(self):
        return [server.idle for server in self._servers.values()].count(False)

    def _get_available_servers(self):
        return [k for k, v in self._servers.items() if v.idle]

    def can_engage_server(self):
        n_servers_w = self._get_servers_working()
        return n_servers_w < len(self._servers) and n_servers_w < self.queue_size()

    def _get_server_random(self):
        return random.choice(self._get_available_servers())

    def _get_server_fastest(self):
        return min(self._get_available_servers(), key=lambda k: self._servers[k].service_time)

    def _get_server_roundrobin(self):
        s_id = self._rr_scheduling.pop(0)
        while not self._servers[s_id].idle:
            self._rr_scheduling.append(s_id)
            s_id = self._rr_scheduling.pop(0)
        self._rr_scheduling.append(s_id)
        return s_id

    def get_capacity(self):
        return sum(map(lambda server: server.service_time, self._servers.values()))

    def engage_server(self):
        assert self._get_servers_working() < len(self._servers)
        server_id = self._scheduling_policy()
        self._servers[server_id].idle = False
        return server_id, self._servers[server_id].service_time

    def consume(self, server_id):
        assert self._get_servers_working() > 0
        self._servers[server_id].idle = True
        return self._queue.pop(0)

    def get_last(self):
        return self._queue[-1]
