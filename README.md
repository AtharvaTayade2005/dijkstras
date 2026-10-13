# Dijkstra Network Explorer 🌐

An interactive, educational desktop visualizer and routing simulation demonstrating **Dijkstra's Shortest-Path Algorithm** on a weighted network graph. Built using Python 3 and Tkinter/ttk with zero external dependencies.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (standard Python distribution with `tkinter` included).

### Launch the Application
Run the entry point directly from PowerShell or Command Prompt:

```powershell
cd C:\Users\athar\.gemini\antigravity-ide\scratch\dijkstra_explorer
python main.py
```

---

## 📋 Features Overview

1. **Interactive Network Topology Canvas**:
   - 6-node weighted, undirected network (Nodes A, B, C, D, E, F; 11 edges).
   - Crisp circular nodes with distinct styling for the selected source (vibrant royal blue with outer glow ring).
   - High-contrast edge weight badges with perpendicular offsets to prevent line overlap.
   - Hover feedback (cursor morphs to `hand2`, subtle halo glow).
   - Fully responsive canvas that recalculates coordinates without distortion during window resize.
   - Compact visual legend explaining styling semantics.

2. **Live Step-by-Step Distance Calculation & Working Panel**:
   - **Stepper Controls**: `⏮ Start`, `◀ Prev Step`, `▶ Auto Play / ⏸ Pause`, `Next Step ▶`, `⏭ End`.
   - **Progress Scrubber**: Interactive slider to scrub backward and forward through any moment in the algorithm.
   - **Speed Control**: Normal (1.1s), Slow (2.0s), Fast (0.5s) auto-play animations.
   - **Mathematical Working**: Displays candidate distance formula:
     $$\text{dist}[u] + \text{weight}(u, v) = \text{candidate}$$
   - **Decision Reasoning**: Explicitly compares candidate vs current tentative distance and explains whether the node distance was `UPDATED`, `UNCHANGED`, or `SKIPPED`.
   - **Real-time Canvas Distance Tags**: Every node on the network canvas displays a live distance pill tag (`[dist: 0 ✓]`, `[dist: 2 ⏳]`, `[dist: ∞]`, or `[visit: 2]`).
   - **Directional Edge Relaxation Arrows**: Evaluated edges glow in amber/green with animated directional arrows pointing from current node to neighbor.

3. **Live Routing Table**:
   - Destination Node
   - Shortest Distance from selected source (source is `0`; `∞` for unreachable)
   - Next Hop (represented as `-` for source; correct forwarding hop for destinations)
   - Complete Shortest Path (e.g. `A → C → D`)
   - Alternating row styling and clear highlight for the source row.
   - **Live Frame Synchronization**: Table rows display live status (`Final ✓`, `Tentative ⏳`, `Testing ⚡`, `Visiting ★`) matching the exact calculation frame!
   - **Interactive Path Inspection**: Clicking any row in the routing table illuminates the complete shortest path on the canvas in glowing blue/emerald.

3. **Dedicated Step-by-Step Explanation Window**:
   - Opened via the prominent **📘 View Step-by-Step Explanation** button.
   - Runs in a large, scrollable modal/toplevel window while keeping the main dashboard visible.
   - **Live Synchronization**: If the user clicks another source node in the main window while the explanation window is open, the explanation window instantly updates in real time.
   - For every iteration:
     - **A. Step Number & Selected Node**: States which node had the minimum tentative distance.
     - **B. Current Distance**: Displays current cost.
     - **C. Neighbor Examination**: Displays candidate vs known distance, whether distance was updated or unchanged, and predecessor changes.
     - **D. Temporary List**: Snapshot of unfinalized nodes and tentative distances, e.g. `B(5), D(3), E(10), F(9)`.
     - **E. Permanent List**: Monotonically growing list of finalized nodes and final costs, e.g. `A(0), C(2), D(3)`.
     - **F. Final Routing Summary**: Complete destination recap at the end of the trace.
   - **Clipboard Export**: One-click copy of the entire formatted text trace.

4. **Summary & Controls**:
   - Live summary metric cards: Selected Source, Network Nodes, Network Edges, Algorithm Name.
   - Quick Source Selector buttons (A–F) for rapid keyboard/mouse navigation.
   - One-click **↺ Reset to Node A** action.

---

## 📐 Network Graph Specification

The network topology matches the exact requirements:

| Edge | Weight | Reverse Edge |
|:---:|:---:|:---:|
| A — B | 6 | B — A (6) |
| A — C | 2 | C — A (2) |
| A — D | 4 | D — A (4) |
| B — C | 3 | C — B (3) |
| B — E | 5 | E — B (5) |
| B — F | 9 | F — B (9) |
| C — D | 1 | D — C (1) |
| C — E | 8 | E — C (8) |
| C — F | 7 | F — C (7) |
| D — F | 7 | F — D (7) |
| E — F | 2 | F — E (2) |

---

## 🏗️ Architecture & Project Structure

The project strictly decouples algorithm logic from GUI widgets, enabling full automated headless verification:

```
dijkstra_explorer/
│
├── main.py                 # Application launcher
├── graph.py                # NetworkGraph class, topology, normalized 2D coordinates
├── dijkstra.py             # Pure algorithm logic, step event recording, path reconstruction
├── gui_canvas.py           # NetworkCanvas widget, geometry scaling, edge badges, hover
├── gui_table.py            # RoutingTableView widget (ttk.Treeview), row selection
├── gui_explanation.py      # ExplanationWindow (Toplevel), scrollable iteration cards
├── gui_main.py             # DijkstraExplorerApp coordinating state, summary cards & views
│
├── tests/
│   ├── test_dijkstra.py    # Unit tests for algorithm, tie-breaking, path sums, disconnected nodes
│   └── test_gui.py         # Integration tests for UI rendering, source switching, live sync, resize
│
└── README.md               # Documentation and execution guide
```

### Key Modules:
- **`graph.py`**: Encapsulates nodes, edges, weights, and normalized coordinates `(nx, ny)`.
- **`dijkstra.py`**: Executes Dijkstra with deterministic tie-breaking (`(distance, node_label)`). Generates rich `DijkstraStep` and `NeighborEvaluation` records preserving Temporary List and Permanent List states.
- **`gui_canvas.py`**: Draws anti-aliased nodes, edges, perpendicular offset weight pills, and path highlights. Re-scales dynamically on `<Configure>` events.
- **`gui_explanation.py`**: Formats each step into readable visual cards with color-coded badges (`UPDATED`, `UNCHANGED`, `SKIPPED`).

---

## 🧪 Automated Tests

The application includes an automated test suite covering:
1. Exact graph edge counts and weights.
2. Shortest-path calculations for all 6 source nodes (A, B, C, D, E, F).
3. Verification that every path's edge weights sum exactly to the reported distance.
4. Next hop correspondence to path reconstruction.
5. Monotonic growth of Permanent List and shrinking of Temporary List.
6. Handling of disconnected / unreachable nodes.
7. GUI initialization, routing table population, source switching, and live explanation sync.
8. Dynamic window resizing and click coordinate hit-testing.

### Running the Test Suite:
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

### Test Result:
```
Ran 13 tests in 3.401s
OK
```

---

## 📦 Dependencies

No third-party packages are required:
- `python >= 3.8`
- Standard library: `tkinter`, `ttk`, `dataclasses`, `typing`, `math`, `unittest`, `os`, `sys`.
