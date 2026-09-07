from backend.models.pdp_models import PDPRequest
from backend.pdp.models import Driver, Order, StopType
from backend.pdp.pdp_service import PDPService


def test_ortools_service_preserves_pickup_before_dropoff():
    service = PDPService("small")
    result = service.solve_pdp(
        [Driver(driver_id=1, start_node="A", capacity=2)],
        [Order(order_id=1, pickup_node="B", dropoff_node="F")],
        algorithm="ortools",
        time_limit_seconds=1,
    )

    route = result["routes"][0]
    stops = route["stops"]
    pickup_index = next(index for index, stop in enumerate(stops) if stop["type"] == StopType.PICKUP.value)
    dropoff_index = next(index for index, stop in enumerate(stops) if stop["type"] == StopType.DROPOFF.value)

    assert result["algorithm"] == "ortools"
    assert result["unassigned_orders"] == []
    assert pickup_index < dropoff_index
    assert route["full_path"][0] == "A"


def test_pdp_request_defaults_to_scratch_algorithm():
    request = PDPRequest(
        drivers=[{"driver_id": 1, "start_node": "A"}],
    )

    assert request.algorithm == "scratch"


def test_pyvrp_service_preserves_pickup_before_dropoff():
    service = PDPService("small")
    result = service.solve_pdp(
        [Driver(driver_id=1, start_node="A", capacity=2)],
        [Order(order_id=1, pickup_node="B", dropoff_node="F")],
        algorithm="pyvrp",
        time_limit_seconds=1,
    )

    route = result["routes"][0]
    assert result["algorithm"] == "pyvrp"
    assert result["unassigned_orders"] == []
    assert [stop["type"] for stop in route["stops"]] == [
        StopType.PICKUP.value,
        StopType.DROPOFF.value,
    ]
    assert route["full_path"][0] == "A"