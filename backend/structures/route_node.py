from typing import Optional

class RouteNode:
    """
    Node in a Doubly Linked List representing a stop in a route.
    """
    def __init__(self, location: str):
        self.location: str = location
        self.next: Optional["RouteNode"] = None
        self.prev: Optional["RouteNode"] = None

    def __repr__(self) -> str:
        return f"RouteNode({self.location})"
