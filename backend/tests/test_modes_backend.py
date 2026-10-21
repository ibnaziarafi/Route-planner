from backend.pdp.distance_matrix import DistanceMatrix
from backend.pdp.models import Driver, Order
from backend.pdp.mode_solver import solve_mode, feasible_insertions, metrics_for, refine, distance
from backend.pdp.validation import validate
from backend.pdp.scratch_solver import build_initial_solution, improve_with_or_opt
from collections import Counter


class Matrix:
    nodes = ["S1", "S2", "P", "D", "X", "Y"]
    def __init__(self, values): self.values = values
    def cost(self, a, b): return 0 if a == b else self.values.get((a,b), float("inf"))


def test_frozen_stale_route_regression_on_real_scratch_implementation():
    costs=[
        [0,17,19,24,28,12,15,15,31,10],[15,0,17,14,12,9,5,18,14,25],
        [13,2,0,13,9,11,7,1,16,10],[6,17,25,0,29,18,9,17,23,15],
        [32,38,36,36,0,28,41,24,28,41],[21,10,8,21,17,0,15,9,24,18],
        [15,26,34,9,29,27,0,26,29,24],[12,15,13,12,22,23,17,0,24,22],
        [17,20,18,26,9,25,21,19,0,16],[20,15,13,14,22,9,5,14,29,0],
    ]
    class Frozen:
        def cost(self,a,b): return costs[int(a)][int(b)]
    drivers=[Driver(1,"0",2),Driver(2,"1",2)]
    orders=[Order(i,p,d) for i,p,d in [(1,"7","6"),(2,"0","6"),(3,"0","3"),(4,"2","7"),(5,"7","4"),(6,"2","6")]]
    dm=Frozen(); initial=build_initial_solution(orders,drivers,dm)
    expected=Counter((o.order_id,k) for o in orders for k in ("pickup","dropoff"))
    initial_distance=initial.total_distance
    result=improve_with_or_opt(initial,orders,drivers,dm)
    counts=Counter((s.order_id,s.stop_type.value) for r in result.routes.values() for s in r.stops)
    assert counts==expected
    assert result.total_distance <= initial_distance


def test_save_activation_can_choose_more_efficient_fleet_and_switches_with_rate():
    dm=Matrix({("S1","P1"):1,("P1","D1"):0,("S1","P2"):10,("P2","D2"):0,
               ("D1","P2"):10,("D2","P1"):10,("S2","P1"):10,("S2","P2"):1})
    drivers=[Driver(1,"S1",2),Driver(2,"S2",2)]
    orders=[Order(1,"P1","D1"),Order(2,"P2","D2")]
    activation_dominates, _=solve_mode(orders,drivers,dm,mode="save",economics={"activation_cost":20,"cost_per_km":0},time_limit_seconds=1)
    distance_dominates, _=solve_mode(orders,drivers,dm,mode="save",economics={"activation_cost":0,"cost_per_km":1},time_limit_seconds=1)
    assert sum(bool(r.stops) for r in activation_dominates.routes.values()) == 1
    assert sum(bool(r.stops) for r in distance_dominates.routes.values()) == 2


def test_time_mode_uses_every_driver_and_reports_proven_count_failure():
    dm=Matrix({("S1","P"):1,("P","D"):1,("S2","X"):1,("X","Y"):1})
    drivers=[Driver(1,"S1",1),Driver(2,"S2",1)]
    orders=[Order(1,"P","D"),Order(2,"X","Y")]
    sol, _=solve_mode(orders,drivers,dm,mode="time",timing={"speed_kph":30,"service_minutes_per_stop":0},time_limit_seconds=1)
    report=validate(sol,orders,drivers,dm,mode="time",timing={"speed_kph":30,"service_minutes_per_stop":0})
    assert report["valid"] and report["complete"]
    assert report["metrics"]["active_drivers"] == 2
    too_many, reason=solve_mode(orders,[*drivers,Driver(3,"S1",1)],dm,mode="time",time_limit_seconds=1)
    assert reason == "drivers_exceed_orders"
    assert too_many.unassigned_orders == [1,2]


def test_candidate_protocol_ordering_and_no_live_mutation():
    dm=Matrix({("S","P"):1,("P","D"):1})
    d=Driver(1,"S",1); order=Order(1,"P","D")
    from backend.pdp.models import Route, Solution
    solution=Solution({1:Route(1)},[])
    options=feasible_insertions(solution,order,[order],[d],dm,mode="save",economics={},timing={},metres_per_unit=1000,remaining_orders=[order])
    assert options and options == sorted(options,key=lambda c:(c["driver_id"],c["pickup_index"],c["dropoff_index"]))
    assert solution.routes[1].stops == []


def test_validator_rejects_duplicate_service_even_if_not_unassigned():
    from backend.pdp.models import Route, Solution, Stop, StopType
    dm=Matrix({("S","P"):0,("P","D"):0})
    d=Driver(1,"S",1); o=Order(1,"P","D")
    route=Route(1,[Stop(1,"P",StopType.PICKUP),Stop(1,"D",StopType.DROPOFF),Stop(1,"P",StopType.PICKUP),Stop(1,"D",StopType.DROPOFF)])
    assert not validate(Solution({1:route},[]),[o],[d],dm)["valid"]


def test_validator_rejects_dropoff_before_pickup_when_capacity_stays_valid():
    from backend.pdp.models import Route, Solution, Stop, StopType
    dm=Matrix({("S","P1"):0,("P1","D2"):0,("D2","P2"):0,("P2","D1"):0})
    driver=Driver(1,"S",1)
    orders=[Order(1,"P1","D1"),Order(2,"P2","D2")]
    # Aggregate load is 1, 0, 1, 0, but order 2 is dropped before pickup.
    route=Route(1,[Stop(1,"P1",StopType.PICKUP),Stop(2,"D2",StopType.DROPOFF),
                   Stop(2,"P2",StopType.PICKUP),Stop(1,"D1",StopType.DROPOFF)])
    report=validate(Solution({1:route},[]),orders,[driver],dm)
    assert not report["valid"]
    assert "order 2 pickup does not precede dropoff" in report["errors"]


def test_refine_refreshes_all_route_distance_caches_after_cross_driver_move():
    from backend.pdp.models import Route, Solution, Stop, StopType
    dm=Matrix({("S","O"):1,("O","I"):1,("I","E"):50,("E","C"):1,
               ("J","E"):1})
    drivers=[Driver(1,"S",2),Driver(2,"J",2)]
    orders=[Order(1,"O","I"),Order(2,"E","C")]
    source=Route(1,[Stop(1,"O",StopType.PICKUP),Stop(1,"I",StopType.DROPOFF),
                    Stop(2,"E",StopType.PICKUP),Stop(2,"C",StopType.DROPOFF)],total_distance=53)
    solution=Solution({1:source,2:Route(2)},[])
    refined=refine(solution,orders,drivers,dm,mode="save",
                   economics={"activation_cost":0,"cost_per_km":1},metres_per_unit=1000)
    expected={driver.driver_id:distance(refined.routes[driver.driver_id],driver,dm) for driver in drivers}
    assert expected[1] == 2 and expected[2] == 2
    assert {did:route.total_distance for did,route in refined.routes.items()} == expected
    assert refined.total_distance == sum(expected.values())
