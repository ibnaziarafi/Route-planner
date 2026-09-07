"""
Core data structures for the multi-driver Pickup-and-Delivery Problem (PDP).

These sit on top of your existing graph + Dijkstra/A* layer. Nothing here
knows about roads or coordinates -- it only knows about a distance matrix
indexed by "location id", which you populate using your existing shortest
path code. That's the key design idea: your graph module and your routing
module never need to touch each other directly.
"""

from dataclasses import dataclass, field
from enum import Enum


class StopType(str, Enum):
    PICKUP = "pickup"
    DROPOFF = "dropoff"


@dataclass(frozen=True)
class Order:
    """One product that needs to move from a pickup node to a dropoff node."""
    order_id: int
    pickup_node: str          # graph node id, e.g. "C"
    dropoff_node: str         # graph node id, e.g. "H"
    demand: int = 1           # "size" of the order -- lets capacity be more than a headcount


@dataclass
class Driver:
    """A delivery person: where they start, and how much they can carry at once."""
    driver_id: int
    start_node: str
    capacity: int = 5         # max simultaneous orders "in the bag"


@dataclass
class Stop:
    """One stop in a driver's route: either picking up or dropping off one order."""
    order_id: int
    node: str
    stop_type: StopType

    def __repr__(self):
        verb = "PICK" if self.stop_type == StopType.PICKUP else "DROP"
        return f"{verb}(order={self.order_id}, node={self.node})"


@dataclass
class Route:
    """The full ordered sequence of stops for a single driver."""
    driver_id: int
    stops: list[Stop] = field(default_factory=list)
    total_distance: float = 0.0

    def as_dict(self):
        return {
            "driver_id": self.driver_id,
            "total_distance": self.total_distance,
            "stops": [
                {"order_id": s.order_id, "node": s.node, "type": s.stop_type.value}
                for s in self.stops
            ],
        }


@dataclass
class Solution:
    """The full assignment: every driver's route, plus bookkeeping."""
    routes: dict[int, Route]
    unassigned_orders: list[int] = field(default_factory=list)

    @property
    def total_distance(self) -> float:
        return sum(r.total_distance for r in self.routes.values())

    def as_dict(self):
        return {
            "total_distance": self.total_distance,
            "unassigned_orders": self.unassigned_orders,
            "routes": [r.as_dict() for r in self.routes.values()],
        }
