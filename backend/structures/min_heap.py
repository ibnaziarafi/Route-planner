from typing import Any


class MinHeap:
    """
    A custom minimum binary heap implementation.
    Stores elements as (priority, value) tuples where smaller priority
    values are popped first. Uses a Python list as the underlying array.
    """

    def __init__(self) -> None:
        self.heap: list[tuple[float, Any]] = []

    def push(self, priority: float, value: Any) -> None:
        """
        Inserts a new (priority, value) pair into the heap and restores heap order.
        """
        # 1. Append the new item at the end of the heap
        self.heap.append((priority, value))
        # 2. Bubble up the new item to its correct position
        self._bubble_up(len(self.heap) - 1)

    def pop(self) -> tuple[float, Any]:
        """
        Removes and returns the (priority, value) tuple with the minimum priority.
        Raises IndexError if the heap is empty.
        """
        if self.is_empty():
            raise IndexError("pop from an empty heap")

        # Swap root element with the last element
        min_item = self.heap[0]
        last_item = self.heap.pop()

        # If there are elements remaining, move last item to root and bubble down
        if not self.is_empty():
            self.heap[0] = last_item
            self._bubble_down(0)

        return min_item

    def peek(self) -> tuple[float, Any]:
        """
        Returns the minimum (priority, value) tuple without removing it.
        Raises IndexError if the heap is empty.
        """
        if self.is_empty():
            raise IndexError("peek from an empty heap")
        return self.heap[0]

    def is_empty(self) -> bool:
        """
        Checks whether the heap contains no elements.
        """
        return len(self.heap) == 0

    def size(self) -> int:
        """
        Returns the number of elements in the heap.
        """
        return len(self.heap)

    # --- Private Helper Methods for Binary Heap Traversal ---

    def _parent(self, index: int) -> int:
        """Calculates index of parent node."""
        return (index - 1) // 2

    def _left_child(self, index: int) -> int:
        """Calculates index of left child node."""
        return 2 * index + 1

    def _right_child(self, index: int) -> int:
        """Calculates index of right child node."""
        return 2 * index + 2

    def _swap(self, i: int, j: int) -> None:
        """Swaps elements at indices i and j."""
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def _bubble_up(self, index: int) -> None:
        """
        Moves the item at `index` upward until heap property is satisfied.
        """
        while index > 0:
            parent_idx = self._parent(index)
            # Compare priorities (index 0 of the tuple)
            if self.heap[index][0] < self.heap[parent_idx][0]:
                self._swap(index, parent_idx)
                index = parent_idx
            else:
                break

    def _bubble_down(self, index: int) -> None:
        """
        Moves the item at `index` downward until heap property is satisfied.
        """
        heap_length = len(self.heap)

        while True:
            left_idx = self._left_child(index)
            right_idx = self._right_child(index)
            smallest = index

            # Check if left child exists and has smaller priority
            if left_idx < heap_length and self.heap[left_idx][0] < self.heap[smallest][0]:
                smallest = left_idx

            # Check if right child exists and has smaller priority
            if right_idx < heap_length and self.heap[right_idx][0] < self.heap[smallest][0]:
                smallest = right_idx

            # If the current node is smaller than both children, heap property is valid
            if smallest == index:
                break

            self._swap(index, smallest)
            index = smallest
