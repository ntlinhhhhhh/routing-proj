####################################################
# LSrouter.py
# Name:
# HUID:
#####################################################

from router import Router
from packet import Packet
import json
import heapq


class LSrouter(Router):
    """Link-State Routing Protocol Implementation."""

    def __init__(self, addr, heartbeat_time):
        super().__init__(addr)
        self.heartbeat_time = heartbeat_time
        self.last_time = 0

        self.neighbors = {}  # port -> (neighbor_addr, cost)
        self.forwarding_table = {}  # dst_addr -> port
        self.link_state_db = {addr: {}}  # addr -> {neighbor_addr: cost}
        self.seq_num = 0
        self.received_seq = {}  # addr -> latest seq_num

    def handle_packet(self, port, packet):
        """Process incoming packet."""
        if packet.is_traceroute:
            if packet.dst_addr in self.forwarding_table:
                out_port = self.forwarding_table[packet.dst_addr]
                self.send(out_port, packet)
            return

        # Process routing packet
        content = json.loads(packet.content)
        src = content['src']
        seq = content['seq_num']
        neighbors = content['neighbors']

        # Ignore older or duplicate updates
        if src in self.received_seq and seq <= self.received_seq[src]:
            return

        # Update link-state DB and broadcast
        self.received_seq[src] = seq
        self.link_state_db[src] = neighbors
        self._run_dijkstra()

        for neighbor_port in self.neighbors:
            if neighbor_port != port:
                self.send(neighbor_port, packet)

    def get_neighbor_map(self):
        """Return a dict: neighbor_addr -> cost."""
        result = {}
        # Duyệt qua tất cả các cổng và lấy thông tin, gán (key, value) trong result
        for port, (neighbor, cost) in self.neighbors.items():
            result[neighbor] = cost
        return result
    
    def _broadcast_link_state(self):
        """Send this router's link-state to all neighbors."""
        # Tạo một gói tin dạng ROUTING chứa thông tin trạng thái liên kết của router
        packet = Packet(
            kind=Packet.ROUTING,
            src_addr=self.addr,
            dst_addr=None, # gửi đến tất cả hàng xóm
            content=json.dumps({
                'src': self.addr,
                'seq_num': self.seq_num,
                'neighbors': self.link_state_db[self.addr]
            })
        )
        for port in self.neighbors:
            self.send(port, packet)

    def handle_new_link(self, port, endpoint, cost):
        """Handle new link establishment."""
        #   update local data structures and forwarding table
        #   broadcast the new link state of this router to all neighbors
        self.neighbors[port] = (endpoint, cost) # Thêm liên kết mới vào bảng neighbors
        self.link_state_db[self.addr] = self.get_neighbor_map()
        self.seq_num += 1

        # Gửi bản tin trạng thái liên kết mới đến tất cả các neighbors 
        self._broadcast_link_state()
        self._run_dijkstra()

    def handle_remove_link(self, port):
        """Handle removed link."""
        #   update local data structures and forwarding table
        #   broadcast the new link state of this router to all neighbors
        if port in self.neighbors:
            del self.neighbors[port]
        self.link_state_db[self.addr] = self.get_neighbor_map()
        self.seq_num += 1

        self._broadcast_link_state()
        self._run_dijkstra()

    def handle_time(self, time_ms):
        """Send periodic link-state update (heartbeat)."""
        if time_ms - self.last_time >= self.heartbeat_time:
            self.last_time = time_ms
            self.seq_num += 1
            self.link_state_db[self.addr] = self.get_neighbor_map()
            self._broadcast_link_state()


    def _run_dijkstra(self):
        """Recompute forwarding table using Dijkstra's algorithm."""
        dist = {self.addr: 0}
        prev = {}
        heap = [(0, self.addr)]
        visited = set()

        while heap:
            cost, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)

            for v, weight in self.link_state_db.get(u, {}).items():
                if v not in dist or dist[v] > cost + weight:
                    dist[v] = cost + weight
                    prev[v] = u
                    heapq.heappush(heap, (dist[v], v))

        new_forwarding_table = {}
        for dest in dist:
            if dest == self.addr:
                continue

            # Trace back to find next hop
            next_hop = dest
            while prev.get(next_hop) != self.addr:
                next_hop = prev.get(next_hop)
                if next_hop is None:
                    break

            # Find port that connects to next_hop
            if next_hop:
                for port, (neighbor, _) in self.neighbors.items():
                    if neighbor == next_hop:
                        new_forwarding_table[dest] = port
                        break

        self.forwarding_table = new_forwarding_table

    def __repr__(self):
        """String representation for debugging."""
        return f"LSrouter(addr={self.addr}, neighbors={len(self.neighbors)}, routes={len(self.forwarding_table)})"