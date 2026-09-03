import pytest
from backend.structures.linked_list import RouteLinkedList

def test_linked_list_append():
    ll = RouteLinkedList()
    ll.append("A")
    ll.append("B")
    ll.append("C")
    assert ll.get_all() == ["A", "B", "C"]
    assert ll.size == 3

def test_linked_list_insert():
    ll = RouteLinkedList()
    ll.append("A")
    ll.append("D")
    ll.append("C")
    # Insert 'E' between 'D' and 'C' (index 2)
    ll.insert(2, "E")
    assert ll.get_all() == ["A", "D", "E", "C"]
    assert ll.size == 4

def test_linked_list_insert_boundaries():
    ll = RouteLinkedList()
    ll.insert(0, "B")
    ll.insert(0, "A")  # Prepend
    ll.insert(10, "C") # Append out of bounds
    assert ll.get_all() == ["A", "B", "C"]

def test_linked_list_remove():
    ll = RouteLinkedList()
    ll.append("A")
    ll.append("B")
    ll.append("C")
    
    removed = ll.remove(1)
    assert removed == "B"
    assert ll.get_all() == ["A", "C"]
    assert ll.size == 2

    # Remove head
    removed_head = ll.remove(0)
    assert removed_head == "A"
    assert ll.get_all() == ["C"]

    # Remove remaining tail
    removed_tail = ll.remove(0)
    assert removed_tail == "C"
    assert ll.get_all() == []
    assert ll.size == 0

def test_linked_list_remove_out_of_bounds():
    ll = RouteLinkedList()
    ll.append("A")
    with pytest.raises(IndexError):
        ll.remove(5)

def test_linked_list_clear():
    ll = RouteLinkedList()
    ll.append("A")
    ll.append("B")
    ll.clear()
    assert ll.get_all() == []
    assert ll.size == 0
    assert ll.head is None
    assert ll.tail is None

def test_linked_list_extend_segment():
    ll = RouteLinkedList()
    ll.extend_segment(["A", "D"])
    ll.extend_segment(["D", "E", "C"])
    ll.extend_segment(["C", "F"])
    assert ll.get_all() == ["A", "D", "E", "C", "F"]
