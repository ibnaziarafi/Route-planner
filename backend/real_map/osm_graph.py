"""Cached Hobart driving graph acquisition and loading."""

from pathlib import Path
from threading import Lock
from xml.etree.ElementTree import ParseError

CACHE_PATH = Path(__file__).resolve().parents[2] / "data" / "maps" / "hobart_drive.graphml"
HOBART_CENTER = (-42.8826, 147.3257)
HOBART_RADIUS_METERS = 7000

_graph_lock = Lock()
_cached_adapter = None


def load_hobart_graph(cache_path: Path = CACHE_PATH):
    import networkx as nx

    cache_path = Path(cache_path)
    if cache_path.exists():
        try:
            return nx.read_graphml(cache_path)
        except (OSError, ValueError, ParseError, nx.NetworkXError):
            cache_path.unlink(missing_ok=True)

    import osmnx as ox

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    graph = ox.graph_from_point(
        HOBART_CENTER,
        dist=HOBART_RADIUS_METERS,
        network_type="drive",
        simplify=True,
    )
    ox.save_graphml(graph, filepath=cache_path)
    return graph


def get_hobart_adapter():
    global _cached_adapter
    if _cached_adapter is None:
        with _graph_lock:
            if _cached_adapter is None:
                from backend.real_map.graph_adapter import OSMGraphAdapter

                _cached_adapter = OSMGraphAdapter(load_hobart_graph())
    return _cached_adapter


def clear_graph_cache() -> None:
    global _cached_adapter
    with _graph_lock:
        _cached_adapter = None
