from fastapi.testclient import TestClient
from backend.main import app

client=TestClient(app)

def _payload(mode="save", methods=None):
    return {"dataset":"synthetic","graph_type":"small","mode":mode,
        "methods":methods or ["scratch"],"time_limit_seconds":1,
        "drivers":[{"driver_id":1,"start_node":"A","capacity":2}],
        "orders":[{"order_id":1,"pickup_node":"B","dropoff_node":"F","demand":1}]}

def test_compare_returns_canonical_feasible_result_and_time_count_failure():
    save=client.post("/api/benchmarks/compare",json=_payload()).json()
    row=save["results"][0]
    assert len(save["request_id"])==64 and row["status"]=="feasible"
    assert row["validation"]["valid"] and row["objective_value"]==row["metrics"]["economic_cost"]
    assert row["timings"]["validation_ms"] >= 0
    time_payload=_payload("time")
    time_payload["drivers"].append({"driver_id":2,"start_node":"C","capacity":2})
    time_result=client.post("/api/benchmarks/compare",json=time_payload).json()["results"][0]
    assert time_result["status"]=="infeasible"
    assert time_result["objective_value"] is None

def test_compare_rejects_duplicate_ids_and_unknown_nodes():
    payload=_payload()
    payload["drivers"].append({"driver_id":1,"start_node":"C","capacity":2})
    assert client.post("/api/benchmarks/compare",json=payload).status_code==422
    payload=_payload(); payload["orders"][0]["pickup_node"]="missing"
    assert client.post("/api/benchmarks/compare",json=payload).status_code==422

def test_path_comparison_checks_astar_against_independent_reference():
    result=client.get("/api/benchmarks/paths?graph_type=medium&repeats=1").json()
    assert {r["method"] for r in result["results"]}=={"scan","heap","astar"}
    assert all(r["valid"] for r in result["results"])
    assert all(r["median_ms"] >= 0 and r["examined_arcs"] >= 0 for r in result["results"])
