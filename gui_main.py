"""
gui_main.py
-----------
Main Application Window for Dijkstra Network Explorer.
Coordinates Header, Summary Cards, Network Canvas, Live Routing Table,
and Step-by-Step Explanation Window.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from graph import NetworkGraph, get_default_graph
from dijkstra import run_dijkstra, DijkstraResult
from gui_canvas import NetworkCanvas
from gui_table import RoutingTableView
from gui_explanation import ExplanationWindow


class DijkstraExplorerApp(tk.Tk):
    """Main application dashboard for Dijkstra Network Explorer."""

    def __init__(self):
        super().__init__()
        self.title("Dijkstra Network Explorer — Interactive Shortest-Path Routing")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(bg="#F8FAFC")

        # Core Graph and Algorithm State
        self.graph: NetworkGraph = get_default_graph()
        self.current_source: str = "A"
        self.current_result: Optional[DijkstraResult] = None
        self.explanation_window: Optional[ExplanationWindow] = None

        # Build UI Structure
        self._build_ui()

        # Compute initial state
        self.set_source(self.current_source)

    def _build_ui(self) -> None:
        """Construct top-level layout components."""
        # 1. Header Section
        self._build_header()

        # 2. Summary & Controls Card Bar
        self._build_summary_bar()

        # 3. Main Workspace (Canvas + Routing Table)
        self._build_main_workspace()

        # 4. Bottom Status Bar
        self._build_status_bar()

    def _build_header(self) -> None:
        """Render modern application header."""
        header_frame = tk.Frame(self, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E2E8F0")
        header_frame.pack(fill=tk.X, side=tk.TOP)

        inner = tk.Frame(header_frame, bg="#FFFFFF", padx=24, pady=14)
        inner.pack(fill=tk.X)

        left_box = tk.Frame(inner, bg="#FFFFFF")
        left_box.pack(side=tk.LEFT)

        title_lbl = tk.Label(
            left_box,
            text="Dijkstra Network Explorer",
            font=("Segoe UI", 18, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(
            left_box,
            text="Interactive Shortest-Path Routing Visualizer • Select any node to recalculate routes in real time",
            font=("Segoe UI", 10),
            fg="#64748B",
            bg="#FFFFFF",
        )
        subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # Right side actions
        right_box = tk.Frame(inner, bg="#FFFFFF")
        right_box.pack(side=tk.RIGHT)

        # Prominent "View Step-by-Step Explanation" button
        self.btn_explain = tk.Button(
            right_box,
            text="📘 View Step-by-Step Explanation",
            command=self.open_explanation_window,
            font=("Segoe UI", 10, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8,
        )
        self.btn_explain.pack(side=tk.RIGHT, padx=(10, 0))

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
            pady=8,
        )
        self.btn_reset.pack(side=tk.RIGHT)

    def _build_summary_bar(self) -> None:
        """Render compact metric cards and quick source node picker buttons."""
        bar_frame = tk.Frame(self, bg="#F8FAFC", padx=24, pady=12)
        bar_frame.pack(fill=tk.X, side=tk.TOP)

        # 4 Metric Cards
        self.card_source = self._create_card(bar_frame, "SELECTED SOURCE", "Node A", "#2563EB")
        self.card_nodes = self._create_card(bar_frame, "NETWORK NODES", f"{self.graph.num_nodes()} Nodes", "#0F172A")
        self.card_edges = self._create_card(bar_frame, "NETWORK EDGES", f"{self.graph.num_edges()} Edges", "#0F172A")
        self.card_algo = self._create_card(bar_frame, "ALGORITHM", "Dijkstra's (O(V²))", "#059669")

        # Source Node Quick Selectors
        picker_frame = tk.Frame(bar_frame, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E2E8F0", padx=12, pady=6)
        picker_frame.pack(side=tk.RIGHT)

        tk.Label(
            picker_frame,
            text="Quick Select Source:",
            font=("Segoe UI", 8, "bold"),
            fg="#64748B",
            bg="#FFFFFF",
        ).pack(side=tk.LEFT, padx=(0, 8))

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
        card = tk.Frame(parent, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E2E8F0", padx=14, pady=8)
        card.pack(side=tk.LEFT, padx=(0, 10))

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
            font=("Segoe UI", 11, "bold"),
            fg=value_color,
            bg="#FFFFFF",
        )
        val_lbl.pack(anchor="w")
        return val_lbl

    def _build_main_workspace(self) -> None:
        """Create split layout for Canvas (left) and Routing Table (right)."""
        workspace = tk.Frame(self, bg="#F8FAFC", padx=24, pady=0)
        workspace.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        # PanedWindow or Side-by-side frames
        # Left Panel: Network Graph Canvas Card
        left_card = tk.Frame(workspace, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E2E8F0")
        left_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=(0, 10))

        # Canvas Header Banner
        canv_head = tk.Frame(left_card, bg="#FFFFFF", padx=14, pady=10)
        canv_head.pack(fill=tk.X)

        tk.Label(
            canv_head,
            text="NETWORK TOPOLOGY",
            font=("Segoe UI", 10, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
        ).pack(side=tk.LEFT)

        tk.Label(
            canv_head,
            text="• Click any node to set it as routing source",
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
        self.canvas_view.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        # Right Panel: Routing Table Card
        right_card = tk.Frame(workspace, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E2E8F0", width=460)
        right_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(0, 0), pady=(0, 10))
        right_card.pack_propagate(False)

        # Routing Table View
        self.table_view = RoutingTableView(
            right_card,
            on_path_selected=self._on_path_highlight_requested,
        )
        self.table_view.pack(fill=tk.BOTH, expand=True)

    def _build_status_bar(self) -> None:
        """Render bottom status bar."""
        status_frame = tk.Frame(self, bg="#F1F5F9", highlightthickness=1, highlightbackground="#E2E8F0", padx=20, pady=6)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_lbl = tk.Label(
            status_frame,
            text="Ready. Select any node to compute shortest path routing.",
            font=("Segoe UI", 8),
            fg="#475569",
            bg="#F1F5F9",
        )
        self.status_lbl.pack(side=tk.LEFT)

        tip_lbl = tk.Label(
            status_frame,
            text="Tip: Click a destination in the routing table to highlight the path on the graph.",
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
        # 1. Execute Dijkstra
        self.current_result = run_dijkstra(self.graph, source)

        # 2. Update Canvas
        self.canvas_view.set_source(source)

        # 3. Update Routing Table
        self.table_view.update_table(source, self.current_result.routing_table)

        # 4. Update Summary Card
        self.card_source.config(text=f"Node {source}")

        # 5. Update Quick Selector Buttons
        for node, btn in self.source_buttons.items():
            if node == source:
                btn.config(bg="#2563EB", fg="#FFFFFF", activebackground="#1D4ED8")
            else:
                btn.config(bg="#F1F5F9", fg="#1E293B", activebackground="#E2E8F0")

        # 6. Synchronize Explanation Window if open
        if self.explanation_window is not None and self.explanation_window.winfo_exists():
            self.explanation_window.update_result(self.current_result)

        # 7. Update Status Bar
        self.status_lbl.config(
            text=f"Computed shortest paths from Source Node '{source}'. Routing table updated."
        )

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
