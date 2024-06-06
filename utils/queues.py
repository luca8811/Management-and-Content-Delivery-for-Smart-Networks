import random
from enum import Enum


class Client:
    def __init__(self, type, arrival_time):
        self.type = type
        self.arrival_time = arrival_time


class Server:
    def __init__(self, service_time):
        self.idle = True  # whether the server is idle or not
        self.service_time = service_time  # service period specific for this server


class ResidualTimeMax:
    BASE = 25 * 60
    W45 = 35 * 60
    W65 = 40 * 60
    W75 = 45 * 60


class BatteryStatus(Enum):
    EMPTY = 1
    FULL = 2
    IN_USE = 3


class Battery:
    RECHARGE_TIME = 3600
    MAX_CYCLES = 3

    def __init__(self):
        self.max_residual_time: int = ResidualTimeMax.BASE
        self.residual: int = 0
        self.status: BatteryStatus = BatteryStatus.FULL
        self.complete_cycles: int = 0


class MMmB:
    def __init__(self, service_times: list[float], buffer_size=0):
        self.buffer_size = buffer_size  # B
        self.battery: Battery = Battery()
        self._queue: list[Client] = []
        self._servers: dict[int, Server] = {i: Server(service_times[i]) for i in range(len(service_times))}
        self._rr_scheduling: list[int] = list(self._servers.keys())
        self._scheduling_policy = self._get_server_fastest

    def queue_clear(self):
        self._queue.clear()

    def insert(self, event: Client):
        assert not self.is_queue_full()
        self._queue.append(event)

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
