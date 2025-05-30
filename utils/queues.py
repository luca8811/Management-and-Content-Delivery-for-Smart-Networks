import random
from enum import Enum


class Packet:
    def __init__(self, arrival_time):
        self.arrival_time = arrival_time
        self.start_service_time = None


class Server:
    def __init__(self, service_time):
        self.idle = True
        self.service_time = service_time
        self.total_time_engaged = 0.0
        self.selection_count = 0

    def engage(self, service_duration):
        self.idle = False
        self.total_time_engaged += service_duration
        self.selection_count += 1

    def release(self):
        self.idle = True


residual_time_max = {
    "INF": 0,
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

    def is_infinite(self):
        return self._max_residual_time == residual_time_max["INF"]


class MMmB:
    def __init__(self, power_supply: str, service_times: list[float], buffer_size=0, infinite_buffer=False, maximum_recharge_cycles="inf", working_slots=[[0, 50000]]):
        self.infinite_buffer = infinite_buffer
        self.buffer_size = buffer_size  # B
        self.battery: Battery = Battery(power_supply)
        self.maximum_recharge_cycles = maximum_recharge_cycles
        self.working_slots = working_slots
        self._queue: list[Packet] = []
        self._servers: dict[int, Server] = {i: Server(service_times[i]) for i in range(len(service_times))}
        self._rr_scheduling: list[int] = list(self._servers.keys())
        self._scheduling_policy = self._get_server_fastest
        self.users = 0

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
        """
        Insert a packet into the queue. If the buffer size is 0, the packet is discarded.
        """
        if self.buffer_size == 0 and not self.infinite_buffer:
            # Buffer is 0, so the packet should be discarded unless a server is free immediately.
            if self.can_engage_server():
                self._queue.append(packet)
            else:
                raise OverflowError("Buffer size is 0, and no server is free. Packet is discarded.")
        else:
            # Regular insertion
            if not self.is_queue_full():
                self._queue.append(packet)
            else:
                raise OverflowError("Buffer is full. Packet is discarded.")

    def queue_size(self):
        return len(self._queue)

    def is_queue_full(self):
        return len(self._queue) == self.buffer_size and not self.infinite_buffer

    def _get_servers_working(self):
        return [server.idle for server in self._servers.values()].count(False)

    def _get_available_servers(self):
        return [k for k, v in self._servers.items() if v.idle]

    def can_engage_server(self):
        """
        Determine if any servers are available to start serving a packet.
        """
        n_servers_w = self._get_servers_working()
        if self.buffer_size == 0:
            # Se non c'è buffer, controlla semplicemente se esiste un server libero
            return n_servers_w < len(self._servers)
        else:
            # Se c'è un buffer, controlla sia la disponibilità del server che lo spazio nel buffer
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
        assert self.can_engage_server()
        server_id = self._scheduling_policy()
        self._servers[server_id].idle = False
        return server_id, self._servers[server_id].service_time

    def consume(self, server_id):
        assert self._get_servers_working() > 0
        if self.queue_size() > 0:
            self._servers[server_id].idle = True
            return self._queue.pop(0)
        else:
            raise IndexError("Attempted to consume from an empty queue")

    def get_last(self):
        return self._queue[-1]

    def is_in_working_slot(self, time):
        for slot in self.working_slots:
            if slot[0] <= time <= slot[1]:
                return True
        return False

    def has_exceeded_max_complete_cycles(self):
        """
        Returns True if the number of charging cycles completed by the battery
        is greater than or equal to the maximum limit of charging cycles.
        """
        if not self.maximum_recharge_cycles == "inf":
            assert isinstance(self.maximum_recharge_cycles, int)
            return self.battery.complete_cycles >= self.maximum_recharge_cycles
        return False
