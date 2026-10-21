"""Bounded interactive PDP comparison API and persisted report readers."""
import hashlib, json, time
from math import isfinite
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from backend.graph.graph_data import get_graph_and_positions
from backend.pdp.distance_matrix import DistanceMatrix
from backend.pdp.models import Driver, Order
from backend.pdp.mode_solver import solve_mode, metrics_for, distance
from backend.pdp.validation import validate

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])

class _CountGraph:
    def __init__(self, graph): self.graph=graph; self.examined=0; self.expansions=0
    def has_node(self,node): return self.graph.has_node(node)
    def get_nodes(self): return self.graph.get_nodes()
    def get_neighbors(self,node):
        self.expansions+=1; values=self.graph.get_neighbors(node); self.examined+=len(values); return values

def _reference_distance(graph,start,end):
    import heapq
    dist={start:0.0}; heap=[(0.0,start)]
    while heap:
        cost,node=heapq.heappop(heap)
        if cost!=dist.get(node): continue
        if node==end: return cost
        for nxt,weight in graph.get_neighbors(node):
            alt=cost+weight
            if alt < dist.get(nxt,float("inf")): dist[nxt]=alt; heapq.heappush(heap,(alt,nxt))
    return float("inf")

@router.get("/paths")
def compare_paths(graph_type: str = Query("medium", pattern="^(small|medium)$"), repeats: int = Query(5, ge=1, le=20)):
    from backend.algorithms.dijkstra import dijkstra as scan
    from backend.algorithms.dijkstra_v2 import dijkstra_v2 as heap
    from backend.algorithms.astar import astar
    graph,positions=get_graph_and_positions(graph_type)
    start,end=("A","T") if graph_type=="medium" else ("A","F")
    expected=_reference_distance(graph,start,end)
    rows=[]
    for name,algorithm in (("scan",lambda g:scan(g,start,end)),("heap",lambda g:heap(g,start,end)),("astar",lambda g:astar(g,start,end,positions))):
        samples=[]
        for _ in range(repeats):
            t=time.perf_counter(); path,distance_value=algorithm(graph); samples.append((time.perf_counter()-t)*1000)
        counter=_CountGraph(graph); path,distance_value=algorithm(counter)
        path_cost=0.0
        for a,b in zip(path,path[1:]):
            edge=next((w for n,w in graph.get_neighbors(a) if n==b),None)
            if edge is None: path_cost=float("inf"); break
            path_cost+=edge
        valid=(distance_value==expected and path_cost==expected and (not expected==float("inf") or not path))
        rows.append({"method":name,"path":path,"distance":distance_value if distance_value!=float("inf") else None,"valid":valid,"median_ms":sorted(samples)[len(samples)//2],"expansions":counter.expansions,"examined_arcs":counter.examined})
    return {"graph_type":graph_type,"graph_nodes":len(graph.get_nodes()),"graph_edges":len(graph.get_edges()),"query":{"start":start,"destination":end},"repeats":repeats,"reference_distance":expected if expected!=float("inf") else None,"results":rows,"timing_note":"Algorithm call time only; expansion and examined-arc counts are collected in a separate untimed pass."}

class DriverInput(BaseModel):
    driver_id: int = Field(ge=1); start_node: str = Field(min_length=1); capacity: int = Field(ge=1)
class OrderInput(BaseModel):
    order_id: int = Field(ge=1); pickup_node: str = Field(min_length=1); dropoff_node: str = Field(min_length=1); demand: int = Field(default=1, ge=1)
class Economics(BaseModel):
    activation_cost: float = Field(default=20, ge=0, allow_inf_nan=False)
    cost_per_km: float = Field(default=.5, ge=0, allow_inf_nan=False)
class Timing(BaseModel):
    speed_kph: float = Field(default=30, gt=0, allow_inf_nan=False)
    service_minutes_per_stop: float = Field(default=1, ge=0, allow_inf_nan=False)
class CompareRequest(BaseModel):
    dataset: str = Field(default="synthetic", pattern="^synthetic$")
    graph_type: str = Field(default="medium", pattern="^(small|medium)$")
    scenario: str = "custom"
    mode: str = Field(default="save", pattern="^(save|time)$")
    methods: list[str] = Field(default_factory=lambda:["scratch"], min_length=1, max_length=4)
    seed: int = 0
    time_limit_seconds: float = Field(default=2, ge=1, le=10, allow_inf_nan=False)
    metres_per_unit: float = Field(default=1000, gt=0, allow_inf_nan=False)
    economics: Economics = Field(default_factory=Economics)
    timing: Timing = Field(default_factory=Timing)
    drivers: list[DriverInput] = Field(min_length=1, max_length=8)
    orders: list[OrderInput] = Field(default_factory=list, max_length=20)
    @model_validator(mode="after")
    def unique_ids_methods(self):
        if len({d.driver_id for d in self.drivers}) != len(self.drivers): raise ValueError("driver IDs must be unique")
        if len({o.order_id for o in self.orders}) != len(self.orders): raise ValueError("order IDs must be unique")
        allowed={"scratch","ortools","pyvrp","learned"}
        if len(set(self.methods)) != len(self.methods) or not set(self.methods) <= allowed: raise ValueError("methods must be unique supported solver names")
        return self

@router.post("/compare")
def compare(req: CompareRequest):
    start = time.perf_counter()
    graph, positions = get_graph_and_positions(req.graph_type)
    drivers=[Driver(**d.model_dump()) for d in req.drivers]; orders=[Order(**o.model_dump()) for o in req.orders]
    nodes=set(graph.adj.keys())
    unknown=({d.start_node for d in drivers} | {n for o in orders for n in (o.pickup_node,o.dropoff_node)}) - nodes
    if unknown: raise HTTPException(422, f"Unknown graph nodes: {', '.join(sorted(unknown))}")
    matrix_start=time.perf_counter(); dm=DistanceMatrix(sorted({d.start_node for d in drivers}|{n for o in orders for n in (o.pickup_node,o.dropoff_node)}),graph); matrix_ms=(time.perf_counter()-matrix_start)*1000
    request_dump=req.model_dump(mode="json"); canonical=json.dumps(request_dump,sort_keys=True,separators=(",",":")); request_id=hashlib.sha256(canonical.encode()).hexdigest()
    results=[]
    for method in req.methods:
        t=time.perf_counter(); warnings=[]; termination="local_optimum"; label=method
        try:
            if req.mode == "time" and len(drivers) > len(orders):
                results.append({"method":method,"method_label":method,"status":"infeasible","objective_value":None,"metrics":None,"routes":[],"unassigned_orders":[o.order_id for o in orders],"validation":{"valid":False,"errors":["Time mode requires at least one complete order per supplied driver; drivers exceed orders."],"complete":False},"timings":{"solve_ms":0.0,"validation_ms":0.0,"expansion_ms":0.0,"total_ms":0.0},"search":{"budget_seconds":req.time_limit_seconds,"seed":req.seed,"termination":"necessary_condition_failed"},"warnings":[]})
                continue
            solve_started=time.perf_counter()
            if method == "scratch":
                solution, termination=solve_mode(orders,drivers,dm,mode=req.mode,economics=req.economics.model_dump(),timing=req.timing.model_dump(),metres_per_unit=req.metres_per_unit,time_limit_seconds=req.time_limit_seconds,seed=req.seed); label="Objective-aware insertion + relocation"
            elif method == "learned":
                label="Locally trained linear RL insertion policy"
                from backend.ml.policy import solve
                solution=solve(orders,drivers,dm,mode=req.mode,economics=req.economics.model_dump(),timing=req.timing.model_dump(),metres_per_unit=req.metres_per_unit,time_limit_seconds=req.time_limit_seconds,seed=req.seed)
            elif method == "ortools":
                from backend.pdp.ortools_solver import solve
                solution=solve(orders,drivers,dm,time_limit_seconds=req.time_limit_seconds,mode=req.mode,economics=req.economics.model_dump(),timing=req.timing.model_dump(),metres_per_unit=req.metres_per_unit); label="OR-Tools economic objective" if req.mode=="save" else "OR-Tools makespan search"
                if solution.metadata.get("adapter"):
                    label=solution.metadata["adapter"]
                    if "fallback" in label: warnings.append("OR-Tools returned no incumbent; a bounded common Time fallback was used.")
                    termination=solution.metadata.get("termination", termination)
            else:
                from backend.pdp.pyvrp_solver import solve
                solution=solve(orders,drivers,dm,max_runtime_seconds=req.time_limit_seconds,seed=req.seed,mode=req.mode,economics=req.economics.model_dump(),timing=req.timing.model_dump(),metres_per_unit=req.metres_per_unit); label="PyVRP distance seed + Time refinement" if req.mode=="time" else "PyVRP economic seed + refinement"
            solve_ms=(time.perf_counter()-solve_started)*1000
            if method == "learned": termination="policy_completed"
            elif method == "pyvrp": termination="native_seed_and_refinement_completed"
            elif method == "ortools" and solution.metadata.get("native_objective"): termination="native_search_completed"
            validation_started=time.perf_counter()
            audit=validate(solution,orders,drivers,dm,mode=req.mode,economics=req.economics.model_dump(),timing=req.timing.model_dump(),metres_per_unit=req.metres_per_unit)
            validation_ms=(time.perf_counter()-validation_started)*1000
            complete=audit["complete"] and audit["valid"]
            status="feasible" if complete else ("partial" if not audit["errors"] and audit["metrics"]["served_orders"] else ("no_solution" if not audit["errors"] else "invalid"))
            route_rows=[]
            for d in drivers:
                route=solution.routes.get(d.driver_id)
                if route is None:
                    from backend.pdp.models import Route
                    route=Route(d.driver_id)
                rd=distance(route,d,dm)
                route_rows.append({"driver_id":d.driver_id,"start_node":d.start_node,"capacity":d.capacity,"total_distance":rd if isfinite(rd) else None,"distance_km":rd*req.metres_per_unit/1000 if isfinite(rd) else None,"completion_minutes":audit["metrics"]["completion_by_driver"].get(d.driver_id),"stops":[{"order_id":s.order_id,"node":s.node,"type":s.stop_type.value} for s in route.stops],"full_path":[]})
            if method == "pyvrp" and solution.metadata.get("adapter"):
                label=solution.metadata["adapter"]
                if "discarded" in label: warnings.append("Native distance seed could not be repaired to a complete all-driver Time solution; common construction replaced it.")
            refinement="none" if method=="learned" else "native_global_span" if method=="ortools" and req.mode=="time" and solution.metadata.get("native_objective") else "objective_aware"
            results.append({"method":method,"method_label":label,"status":status,"objective_value":audit["objective_value"],"metrics":audit["metrics"],"routes":route_rows,"unassigned_orders":solution.unassigned_orders,"validation":{"valid":audit["valid"],"errors":audit["errors"],"complete":audit["complete"]},"timings":{"solve_ms":solve_ms,"validation_ms":validation_ms,"expansion_ms":0.0,"total_ms":(time.perf_counter()-t)*1000},"search":{"budget_seconds":req.time_limit_seconds,"seed":req.seed if method=="pyvrp" else None,"termination":termination,"refinement":refinement},"warnings":warnings,"solver_metadata":solution.metadata})
        except Exception as exc:
            unavailable=isinstance(exc,(ImportError,NotImplementedError)) or (method=="learned" and isinstance(exc,RuntimeError) and "model is unavailable" in str(exc))
            results.append({"method":method,"method_label":label,"status":"unavailable" if unavailable else "error","objective_value":None,"metrics":None,"routes":[],"unassigned_orders":[o.order_id for o in orders],"validation":{"valid":False,"errors":[str(exc)]},"timings":{"solve_ms":(time.perf_counter()-t)*1000,"validation_ms":0.0,"expansion_ms":0.0,"total_ms":(time.perf_counter()-t)*1000},"search":{"budget_seconds":req.time_limit_seconds,"seed":req.seed,"termination":"unavailable" if unavailable else "error"},"warnings":[str(exc)]})
    return {"request_id":request_id,"request":request_dump,"dataset":"synthetic","mode":req.mode,"objective":{"name":"total_economic_cost" if req.mode=="save" else "makespan","unit":"currency_units" if req.mode=="save" else "minutes","definition":"activation*active + per_km*km" if req.mode=="save" else "max(distance_km/speed_kph*60 + service_minutes_per_stop*stops)"},"assumptions":{"metres_per_unit":req.metres_per_unit,"speed_kph":req.timing.speed_kph,"service_minutes_per_stop":req.timing.service_minutes_per_stop,"open_routes":True,"simultaneous_starts":True},"matrix_ms":matrix_ms,"positions":positions,"results":results,"total_ms":(time.perf_counter()-start)*1000}

@router.get("/report")
def report():
    path=Path(__file__).resolve().parents[2]/"artifacts"/"learned"/"benchmark_report.json"
    if not path.exists(): return {"status":"not_run","limitations":["No persisted held-out benchmark report is available."]}
    try: return json.loads(path.read_text())
    except (OSError,json.JSONDecodeError) as exc: raise HTTPException(500, f"Benchmark report unavailable: {exc}")

@router.get("/model")
def model_status():
    try:
        from backend.ml.policy import model_metadata as status
        return status()
    except (ImportError, RuntimeError, ValueError) as exc:
        return {"status":"unavailable","reason":str(exc),"training_triggered":False}
