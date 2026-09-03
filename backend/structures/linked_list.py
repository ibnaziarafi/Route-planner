from typing import Optional
from backend.structures.route_node import RouteNode

class RouteLinkedList:
    """
    Custom Doubly Linked List for storing and manipulating ordered route locations.
    """
    def __init__(self):
        self.head: Optional[RouteNode] = None
        self.tail: Optional[RouteNode] = None
        self.size: int = 0

    def append(self, location: str) -> None:
        """Appends a new location node to the end of the linked list."""
        new_node = RouteNode(location)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node
        self.size += 1

    def insert(self, index: int, location: str) -> None:
        """Inserts a new location node at the specified index."""
        if index <= 0:
            # Prepend
            new_node = RouteNode(location)
            if self.head is None:
                self.head = new_node
                self.tail = new_node
            else:
                new_node.next = self.head
                self.head.prev = new_node
                self.head = new_node
            self.size += 1
            return

        if index >= self.size:
            # Append
            self.append(location)
            return

        # Insert at internal index
        curr = self.head
        for _ in range(index):
            curr = curr.next

        new_node = RouteNode(location)
        new_node.prev = curr.prev
        new_node.next = curr

        if curr.prev:
            curr.prev.next = new_node
        curr.prev = new_node

        self.size += 1

    def remove(self, index: int) -> str:
        """Removes the node at the specified 0-based index and returns its location."""
        if index < 0 or index >= self.size or self.head is None:
            raise IndexError("Index out of bounds")

        curr = self.head
        for _ in range(index):
            curr = curr.next

        # Node to remove is curr
        if curr.prev:
            curr.prev.next = curr.next
        else:
            self.head = curr.next

        if curr.next:
            curr.next.prev = curr.prev
        else:
            self.tail = curr.prev

        self.size -= 1
        return curr.location

    def get_all(self) -> list[str]:
        """Traverses the linked list from head to tail and returns a list of location names."""
        locations = []
        curr = self.head
        while curr:
            locations.append(curr.location)
            curr = curr.next
        return locations

    def clear(self) -> None:
        """Clears all nodes from the linked list."""
        self.head = None
        self.tail = None
        self.size = 0

    def extend_segment(self, node_list: list[str]) -> None:
        """
        Appends a list of nodes representing a segment.
        If self already has nodes and node_list[0] == self.tail.location,
        skips the first node to avoid duplicate segment endpoints.
        """
        if not node_list:
            return

        start_idx = 0
        if self.tail is not None and node_list[0] == self.tail.location:
            start_idx = 1

        for loc in node_list[start_idx:]:
            self.append(loc)
