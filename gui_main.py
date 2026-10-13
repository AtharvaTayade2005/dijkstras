"""
gui_main.py
-----------
Main Application Window for Dijkstra Network Explorer.
Coordinates Header, Summary Cards, Interactive Network Canvas with Live Distance Badges,
Working & Calculation Visualization Panel, Live Dynamic Routing Table,
and Step-by-Step Explanation Window.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from graph import NetworkGraph, get_default_graph
from dijkstra import run_dijkstra, DijkstraResult, SimulationFrame
from gui_canvas import NetworkCanvas
from gui_table import RoutingTableView
from gui_explanation import ExplanationWindow
from gui_working_panel import WorkingCalculationPanel


class DijkstraExplorerApp(tk.Tk):
    """Main application dashboard for Dijkstra Network Explorer."""

    def __init__(self):
        super().__init__()
        self.title("Dijkstra Network Explorer — Interactive Shortest-Path Routing Visualizer")
        self.geometry("1240x840")
        self.minsize(1040, 700)
        self.configure(bg="#F8FAFC")

        # Core Graph and Algorithm State
        self.graph: NetworkGraph = get_default_graph()
        self.current_source: str = "A"
        self.current_result: Optional[DijkstraResult] = None
        self.explanation_window: Optional[ExplanationWindow] = None

        # Build UI Structure
        self._build_ui()

        # Compute initial state and start at source A
        self.set_source(self.current_source)

    def _build_ui(self) -> None:
        """Construct top-level layout components."""
        # 1. Header Section
        self._build_header()

        # 2. Summary & Controls Card Bar
        self._build_summary_bar()

        # 3. Main Workspace (Canvas + Working Panel + Routing Table)
        self._build_main_workspace()

        # 4. Bottom Status Bar
        self._build_status_bar()

    def _build_header(self) -> None:
        """Render modern application header."""
        header_frame = tk.Frame(self, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E2E8F0")
        header_frame.pack(fill=tk.X, side=tk.TOP)

        inner = tk.Frame(header_frame, bg="#FFFFFF", padx=20, pady=12)
        inner.pack(fill=tk.X)

        left_box = tk.Frame(inner, bg="#FFFFFF")
        left_box.pack(side=tk.LEFT)

        title_lbl = tk.Label(
            left_box,
            text="Dijkstra Network Explorer",
            font=("Segoe UI", 17, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(
            left_box,
            text="Visual Shortest-Path Routing & Live Calculation Engine • Step-by-step edge relaxation & table updates",
            font=("Segoe UI", 9),
            fg="#64748B",
            bg="#FFFFFF",
        )
        subtitle_lbl.pack(anchor="w", pady=(1, 0))

        # Right side actions
        right_box = tk.Frame(inner, bg="#FFFFFF")
        right_box.pack(side=tk.RIGHT)

        # Prominent "View Step-by-Step Explanation" button
        self.btn_explain = tk.Button(
            right_box,
            text="📘 Detailed Text Walkthrough",
            command=self.open_explanation_window,
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7,
        )
        self.btn_explain.pack(side=tk.RIGHT, padx=(8, 0))

        # Reset button
        self.btn_reset = tk.Button(
            right_box,
            text="↺ Reset to Node A",
            command=lambda: self.set_source("A"),
            font=("Segoe UI", 9),
            bg="#F1F5F9",
            fg="#334155",
            activebackground="#E2E8F0",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=7,
        )
        self.btn_reset.pack(side=tk.RIGHT)

    def _build_summary_bar(self) -> None:
        """Render compact metric cards and quick source node picker buttons."""
        bar_frame = tk.Frame(self, bg="#F8FAFC", padx=20, pady=8)
        bar_frame.pack(fill=tk.X, side=tk.TOP)

        # 4 Metric Cards
        self.card_source = self._create_card(bar_frame, "SELECTED SOURCE", "Node A", "#2563EB")
        self.card_nodes = self._create_card(bar_frame, "NETWORK NODES", f"{self.graph.num_nodes()} Nodes", "#0F172A")
        self.card_edges = self._create_card(bar_frame, "NETWORK EDGES", f"{self.graph.num_edges()} Edges", "#0F172A")
        self.card_algo = self._create_card(bar_frame, "ALGORITHM", "Dijkstra (O(V²))", "#059669")

        # Source Node Quick Selectors
        picker_frame = tk.Frame(bar_frame, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E2E8F0", padx=10, pady=5)
        picker_frame.pack(side=tk.RIGHT)

        tk.Label(
            picker_frame,
            text="Source Node:",
            font=("Segoe UI", 8, "bold"),
            fg="#64748B",
            bg="#FFFFFF",
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.source_buttons = {}
        for node in self.graph.nodes:
            btn = tk.Button(
                picker_frame,
                text=node,
                font=("Segoe UI", 9, "bold"),
                width=3,
                relief="flat",
                cursor="hand2",
                command=lambda n=node: self.set_source(n),
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.source_buttons[node] = btn

    def _create_card(self, parent: tk.Widget, label_text: str, value_text: str, value_color: str) -> tk.Label:
        """Helper to create a neat summary card."""
        card = tk.Frame(parent, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E2E8F0", padx=12, pady=6)
        card.pack(side=tk.LEFT, padx=(0, 8))

        lbl = tk.Label(
            card,
            text=label_text,
            font=("Segoe UI", 7, "bold"),
            fg="#64748B",
            bg="#FFFFFF",
        )
        lbl.pack(anchor="w")

        val_lbl = tk.Label(
            card,
            text=value_text,
            font=("Segoe UI", 10, "bold"),
            fg=value_color,
            bg="#FFFFFF",
        )
        val_lbl.pack(anchor="w")
        return val_lbl

    def _build_main_workspace(self) -> None:
        """Create split layout for Visual Graph & Working Panel (left) and Routing Table (right)."""
        workspace = tk.Frame(self, bg="#F8FAFC", padx=20, pady=0)
        workspace.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        # Left Column: Canvas Card + Working Panel
        left_card = tk.Frame(workspace, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E2E8F0")
        left_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=(0, 8))

        # Canvas Header Banner
        canv_head = tk.Frame(left_card, bg="#FFFFFF", padx=12, pady=8)
        canv_head.pack(fill=tk.X)

        tk.Label(
            canv_head,
            text="NETWORK TOPOLOGY & LIVE DISTANCE VISUALIZATION",
            font=("Segoe UI", 9, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
        ).pack(side=tk.LEFT)

        tk.Label(
            canv_head,
            text="• Watch distance tags & relaxation arrows update during execution",
            font=("Segoe UI", 8),
            fg="#64748B",
            bg="#FFFFFF",
        ).pack(side=tk.LEFT, padx=(8, 0))

        # Network Canvas Widget
        self.canvas_view = NetworkCanvas(
            left_card,
            graph=self.graph,
            on_node_selected=self.set_source,
        )
        self.canvas_view.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        # Live Working & Calculation Panel (Directly beneath canvas)
        self.working_panel = WorkingCalculationPanel(
            left_card,
            on_frame_change=self._on_simulation_frame_changed,
        )
        self.working_panel.pack(fill=tk.X, side=tk.BOTTOM, padx=6, pady=(0, 6))

        # Right Column: Live Routing Table Card
        right_card = tk.Frame(workspace, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E2E8F0", width=460)
        right_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(0, 0), pady=(0, 8))
        right_card.pack_propagate(False)

        # Routing Table View
        self.table_view = RoutingTableView(
            right_card,
            on_path_selected=self._on_path_highlight_requested,
        )
        self.table_view.pack(fill=tk.BOTH, expand=True)

    def _build_status_bar(self) -> None:
        """Render bottom status bar."""
        status_frame = tk.Frame(self, bg="#F1F5F9", highlightthickness=1, highlightbackground="#E2E8F0", padx=18, pady=5)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_lbl = tk.Label(
            status_frame,
            text="Ready. Select any node or click '▶ Auto Play' to watch the calculation.",
            font=("Segoe UI", 8),
            fg="#475569",
            bg="#F1F5F9",
        )
        self.status_lbl.pack(side=tk.LEFT)

        tip_lbl = tk.Label(
            status_frame,
            text="Use controls: ⏮ Start | ◀ Prev | ▶ Auto Play | Next ▶ | ⏭ End",
            font=("Segoe UI", 8, "italic"),
            fg="#64748B",
            bg="#F1F5F9",
        )
        tip_lbl.pack(side=tk.RIGHT)

    def set_source(self, source: str) -> None:
        """Recalculate Dijkstra from new source and refresh all UI elements."""
        if source not in self.graph.nodes:
            return

        self.current_source = source
        # 1. Execute Dijkstra and generate simulation frames
        self.current_result = run_dijkstra(self.graph, source)

        # 2. Update Summary Card
        self.card_source.config(text=f"Node {source}")

        # 3. Update Quick Selector Buttons
        for node, btn in self.source_buttons.items():
            if node == source:
                btn.config(bg="#2563EB", fg="#FFFFFF", activebackground="#1D4ED8")
            else:
                btn.config(bg="#F1F5F9", fg="#1E293B", activebackground="#E2E8F0")

        # 4. Set Frames in Working Panel
        self.working_panel.set_frames(self.current_result.frames)

        # 5. Synchronize Canvas and Routing Table to Frame 0
        if self.current_result.frames:
            initial_frame = self.current_result.frames[0]
            self.canvas_view.set_source(source)
            self.canvas_view.set_simulation_frame(initial_frame)
            self.table_view.update_live_frame(initial_frame, source, self.graph.nodes)

        # 6. Synchronize Explanation Window if open
        if self.explanation_window is not None and self.explanation_window.winfo_exists():
            self.explanation_window.update_result(self.current_result)

        # 7. Update Status Bar
        self.status_lbl.config(
            text=f"Loaded Dijkstra calculation for Source Node '{source}'. Click '▶ Auto Play' or 'Next ▶' to step through."
        )

    def _on_simulation_frame_changed(self, frame_idx: int) -> None:
        """Callback when stepper/slider advances to a new calculation frame."""
        if not self.current_result or not self.current_result.frames:
            return

        if frame_idx >= len(self.current_result.frames):
            return

        frame = self.current_result.frames[frame_idx]

        # 1. Update Canvas with live distance tags, active node, and examined edge
        self.canvas_view.set_simulation_frame(frame)

        # 2. Update Live Routing Table with current snapshot state
        self.table_view.update_live_frame(frame, self.current_source, self.graph.nodes)

        # 3. Status Bar update
        if frame.phase == "EXAMINE_EDGE":
            status_text = f"Frame {frame_idx + 1}: Relaxing Edge {frame.active_edge[0]}—{frame.active_edge[1]} | {frame.comparison_text}"
        elif frame.phase == "PICK_MIN":
            status_text = f"Frame {frame_idx + 1}: Selected unfinalized Node '{frame.current_node}' with minimum tentative cost {frame.selected_cost}."
        elif frame.phase == "COMPLETE":
            status_text = f"Frame {frame_idx + 1}: Algorithm complete! All shortest paths finalized."
        else:
            status_text = f"Frame {frame_idx + 1}: {frame.title}"

        self.status_lbl.config(text=status_text)

    def _on_path_highlight_requested(self, path: List[str]) -> None:
        """Handle user clicking a table row to highlight that path on the network."""
        self.canvas_view.set_highlighted_path(path)
        if len(path) > 1:
            dest = path[-1]
            dist = self.current_result.routing_table[dest].distance_display
            path_str = " → ".join(path)
            self.status_lbl.config(
                text=f"Highlighted Shortest Path to Node {dest}: {path_str} (Cost: {dist})"
            )
        else:
            self.status_lbl.config(
                text=f"Source node '{self.current_source}' selected (Cost: 0)."
            )

    def open_explanation_window(self) -> None:
        """Open or refocus the step-by-step explanation window."""
        if self.explanation_window is not None and self.explanation_window.winfo_exists():
            self.explanation_window.update_result(self.current_result)
            self.explanation_window.lift()
            self.explanation_window.focus_force()
        else:
            self.explanation_window = ExplanationWindow(self, self.current_result)


def launch():
    """Launch the Dijkstra Network Explorer application."""
    app = DijkstraExplorerApp()
    app.mainloop()


if __name__ == "__main__":
    launch()
