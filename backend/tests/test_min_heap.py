import pytest
from backend.structures.min_heap import MinHeap


def test_min_heap_initial_state():
    heap = MinHeap()
    assert heap.is_empty() is True
    assert heap.size() == 0


def test_min_heap_push_peek_size():
    heap = MinHeap()
    heap.push(5, "B")
    assert heap.is_empty() is False
    assert heap.size() == 1
    assert heap.peek() == (5, "B")

    heap.push(2, "D")
    assert heap.size() == 2
    assert heap.peek() == (2, "D")

    heap.push(8, "F")
    assert heap.size() == 3
    assert heap.peek() == (2, "D")


def test_min_heap_pop_order():
    heap = MinHeap()
    items = [(5, "B"), (2, "D"), (8, "F"), (1, "A"), (4, "C")]
    for priority, val in items:
        heap.push(priority, val)

    popped = []
    while not heap.is_empty():
        popped.append(heap.pop())

    expected = [(1, "A"), (2, "D"), (4, "C"), (5, "B"), (8, "F")]
    assert popped == expected


def test_min_heap_duplicate_priorities():
    heap = MinHeap()
    heap.push(3, "Node1")
    heap.push(3, "Node2")
    heap.push(1, "Node0")

    assert heap.pop() == (1, "Node0")
    p1 = heap.pop()
    p2 = heap.pop()
    assert p1[0] == 3
    assert p2[0] == 3
    assert heap.is_empty() is True


def test_min_heap_empty_errors():
    heap = MinHeap()
    with pytest.raises(IndexError, match="pop from an empty heap"):
        heap.pop()

    with pytest.raises(IndexError, match="peek from an empty heap"):
        heap.peek()
