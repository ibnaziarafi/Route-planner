# 🗺️ Route Planner — Phase 1

A full-stack route planning web application powered by **custom Data Structures & Algorithms** (Graph, Dijkstra's algorithm, and Doubly Linked List), built with a **FastAPI** backend and an interactive **React** frontend.

---

## 🌟 Key Features

- **Custom Graph Structure**: Adjacency list representation supporting node creation, weighted undirected edges, and neighbor lookups.
- **Custom Dijkstra Shortest Path**: Pure Python implementation built from scratch without external pathfinding libraries.
- **Custom Doubly Linked List**: `RouteLinkedList` and `RouteNode` structure managing ordered route stops (`append`, `insert`, `remove`, `clear`, `get_all`, and segment concatenation).
- **Multi-Stop Route Calculation**: Calculates multi-stop routes (`Start -> Stop1 -> ... -> StopN -> Destination`) segment-by-segment using Dijkstra and combines them into a unified Doubly Linked List.
- **FastAPI REST API**: Clean API endpoints (`GET /graph`, `POST /route`, `POST /route/multi-stop`, `POST /pdp/solve`) with automatic Pydantic request/response validation.
- **Pickup & Delivery Optimization**: Multi-driver parcel routing with a from-scratch heuristic, Google OR-Tools, or PyVRP hybrid genetic search solver, selectable from the PDP frontend page at `/pdp`.
- **Real Map Routing**: Cached Hobart OpenStreetMap driving data with the existing Dijkstra, Dijkstra V2, and A* algorithms, available at `/real-map`.
- **Real Map PDP**: Coordinate-based drivers and pickup/dropoff orders optimized on the cached Hobart road graph, available at `/real-map-pdp` through `POST /api/real-map-pdp/solve`.
- **100% Test Coverage**: Comprehensive pytest suite (18 automated tests) validating Graph data structures, Dijkstra algorithm edge cases, Linked List memory operations, and API endpoints.
- **Interactive SVG Map & React UI**: Modern dark theme glassmorphism interface featuring node selection, dynamic stop ordering (add, remove, move up/down), glowing SVG route path visualization, and sequence step badges.

---

## 📁 Repository Structure

```
Route-planner/
├── backend/
│   ├── main.py                     # FastAPI app entrypoint & CORS setup
│   ├── models/
│   │   └── route_models.py         # Pydantic schemas for API requests/responses
│   ├── graph/
│   │   ├── graph.py                # Custom Graph (Adjacency List) class
│   │   └── graph_data.py           # Default road network graph & 2D positions
│   ├── algorithms/
│   │   └── dijkstra.py             # Pure Python Dijkstra implementation
│   ├── structures/
│   │   ├── route_node.py           # Doubly Linked List node (RouteNode)
│   │   └── linked_list.py          # RouteLinkedList data structure
│   ├── services/
│   │   └── route_service.py        # Business logic binding Graph, Dijkstra & Linked List
│   └── tests/
│       ├── test_graph.py           # Unit tests for Graph
│       ├── test_dijkstra.py        # Unit tests for Dijkstra algorithm
│       ├── test_linked_list.py     # Unit tests for RouteLinkedList
│       └── test_api.py             # Integration tests for FastAPI endpoints
└── frontend/                       # React + Vite application
    ├── src/
    │   ├── App.jsx                 # Main application UI container
    │   ├── index.css               # Dark mode styling & glassmorphism theme
    │   ├── components/
    │   │   ├── Header.jsx          # Top branding bar & backend connection badge
    │   │   ├── RouteForm.jsx       # Trip configuration panel (Start, Stops, Destination)
    │   │   ├── GraphCanvas.jsx     # Interactive SVG road network graph visualizer
    │   │   └── RouteSummary.jsx    # Path pills, distance metrics & Linked List visualizer
    │   └── services/
    │       └── api.js              # Fetch requests to FastAPI backend
    └── package.json
```

---

## 🛠️ Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & `npm`

### 2. Backend Setup
```powershell
# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # On Windows (or source venv/bin/activate on Linux/Mac)

# Install backend dependencies
pip install fastapi uvicorn pydantic pytest httpx ortools pyvrp osmnx

# Run unit tests
pytest backend/tests

# Start FastAPI server
uvicorn backend.main:app --port 8000 --reload
```

The first real-map request provisions `data/maps/hobart_drive.graphml` from OpenStreetMap when the cache is missing. Later requests reuse that local graph.
Backend server will run at `http://127.0.0.1:8000`. OpenAPI docs available at `http://127.0.0.1:8000/docs`.

### 3. Frontend Setup
```powershell
cd frontend

# Install node dependencies
npm install

# Start Vite React dev server
npm run dev
```
Frontend application will be accessible at `http://localhost:5173`.

### 4. Docker Desktop

From the repository root:

```powershell
docker compose up --build
```

Open `http://localhost:5173`. The frontend container serves the React build and proxies API requests to the backend container. FastAPI is also available at `http://localhost:8000/docs`.

The OSMnx Hobart graph is persisted in `./data/maps`, so the first real-map request may download the graph, while later container restarts reuse the cache.

To stop the containers:

```powershell
docker compose down
```

---

## 🧭 Project Roadmap

- [x] **Phase 1**: Weighted Graph + Dijkstra + Doubly Linked List + Multi-Stop Routing + FastAPI + React UI.
- [ ] **Phase 2**: Real Geographic Map integration (Leaflet / OpenStreetMap) + Real-world road data.
- [ ] **Phase 3**: Min Heap / Priority Queue optimization for Dijkstra + Navigation history stack.
- [ ] **Phase 4**: A* Algorithm + Geographic heuristic distance function + Alternative routes.
- [ ] **Phase 5**: Machine Learning traffic prediction + Personalized route recommendations.
