"""
gui_canvas.py
-------------
Interactive Network Graph Canvas for Dijkstra Network Explorer.
Renders nodes, weighted edges, badges, hover feedback, responsive resizing,
active shortest-path highlighting, and real-time step-by-step distance calculation tags.
"""

import math
import tkinter as tk
from typing import Dict, List, Tuple, Optional, Callable
from graph import NetworkGraph
from dijkstra import SimulationFrame, format_distance


class NetworkCanvas(tk.Frame):
    """Interactive Canvas displaying the weighted network graph."""

    def __init__(
        self,
        parent: tk.Widget,
        graph: NetworkGraph,
        on_node_selected: Callable[[str], None],
        **kwargs
    ):
        super().__init__(parent, bg="#FFFFFF", **kwargs)
        self.graph = graph
        self.on_node_selected = on_node_selected

        self.selected_source: str = "A"
        self.highlighted_path: List[str] = []
        self.hovered_node: Optional[str] = None

        # Live calculation simulation states
        self.current_distances: Dict[str, float] = {n: float("inf") for n in self.graph.nodes}
        self.current_distances["A"] = 0.0
        self.permanent_nodes: List[str] = []
        self.active_visiting_node: Optional[str] = None
        self.active_neighbor_node: Optional[str] = None
        self.active_edge: Optional[Tuple[str, str]] = None
        self.active_edge_status: str = ""

        # Cached pixel positions of nodes
        self.node_coords: Dict[str, Tuple[float, float]] = {}
        self.node_radius: float = 24.0

        # Colors (Modern Light Theme)
        self.COLOR_BG = "#FFFFFF"
        self.COLOR_PANEL_BORDER = "#E2E8F0"
        self.COLOR_EDGE = "#94A3B8"
        self.COLOR_EDGE_ACTIVE = "#2563EB"
        self.COLOR_EDGE_CALC_EXAMINE = "#D97706"
        self.COLOR_EDGE_CALC_UPDATE = "#059669"
        
        self.COLOR_NODE_DEFAULT_BG = "#FFFFFF"
        self.COLOR_NODE_DEFAULT_BORDER = "#334155"
        self.COLOR_NODE_DEFAULT_TEXT = "#0F172A"

        self.COLOR_NODE_SOURCE_BG = "#2563EB"
        self.COLOR_NODE_SOURCE_BORDER = "#1D4ED8"
        self.COLOR_NODE_SOURCE_RING = "#BFDBFE"
        self.COLOR_NODE_SOURCE_TEXT = "#FFFFFF"

        self.COLOR_NODE_FINAL_BG = "#10B981"
        self.COLOR_NODE_FINAL_BORDER = "#059669"
        self.COLOR_NODE_FINAL_RING = "#A7F3D0"
        self.COLOR_NODE_FINAL_TEXT = "#FFFFFF"

        self.COLOR_NODE_EXAMINE_BG = "#F59E0B"
        self.COLOR_NODE_EXAMINE_BORDER = "#D97706"
        self.COLOR_NODE_EXAMINE_RING = "#FDE68A"
        self.COLOR_NODE_EXAMINE_TEXT = "#FFFFFF"

        self.COLOR_BADGE_BG = "#FFFFFF"
        self.COLOR_BADGE_BORDER = "#CBD5E1"
        self.COLOR_BADGE_TEXT = "#1E293B"

        # Edge label placement parameters: (u, v) -> (t_along_edge, normal_offset_pixels)
        self.edge_label_offsets: Dict[Tuple[str, str], Tuple[float, float]] = {
            ("A", "B"): (0.50, -14.0),
            ("A", "C"): (0.45, -13.0),
            ("A", "D"): (0.50, -15.0),
            ("B", "C"): (0.42, -14.0),
            ("B", "E"): (0.50, -14.0),
            ("B", "F"): (0.30, 15.0),   # Placed near B to avoid C-E crossing
            ("C", "D"): (0.48, 14.0),
            ("C", "E"): (0.72, -14.0),  # Placed near E to avoid B-F crossing
            ("C", "F"): (0.48, 14.0),
            ("D", "F"): (0.50, 15.0),
            ("E", "F"): (0.50, 14.0),
        }

        # Setup Canvas
        self.canvas = tk.Canvas(
            self,
            bg=self.COLOR_BG,
            highlightthickness=1,
            highlightbackground=self.COLOR_PANEL_BORDER,
            cursor="arrow"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Event bindings
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)

    def set_source(self, source: str) -> None:
        """Update selected source and reset temporary simulation highlights."""
        self.selected_source = source
        self.highlighted_path = []
        self.active_visiting_node = None
        self.active_neighbor_node = None
        self.active_edge = None
        self.active_edge_status = ""
        self.current_distances = {n: float("inf") for n in self.graph.nodes}
        self.current_distances[source] = 0.0
        self.permanent_nodes = []
        self.redraw()

    def set_simulation_frame(self, frame: SimulationFrame) -> None:
        """Apply visual state from an atomic calculation frame."""
        self.current_distances = frame.distances_snapshot.copy()
        self.permanent_nodes = frame.permanent_nodes.copy()
        self.active_visiting_node = frame.current_node
        self.active_neighbor_node = frame.examining_neighbor
        self.active_edge = frame.active_edge
        self.active_edge_status = frame.status
        self.highlighted_path = frame.highlight_path.copy()
        self.redraw()

    def set_final_state(self, distances: Dict[str, float]) -> None:
        """Apply the final algorithm state with all nodes locked."""
        self.current_distances = distances.copy()
        self.permanent_nodes = list(self.graph.nodes)
        self.active_visiting_node = None
        self.active_neighbor_node = None
        self.active_edge = None
        self.active_edge_status = ""
        self.redraw()

    def set_highlighted_path(self, path: List[str]) -> None:
        """Highlight a specific shortest path on the network."""
        self.highlighted_path = list(path)
        self.redraw()

    def _on_resize(self, event) -> None:
        """Handle canvas resize responsively."""
        self.redraw()

    def _calculate_pixel_positions(self) -> None:
        """Convert normalized graph positions to current pixel bounds."""
        w = max(self.canvas.winfo_width(), 420)
        h = max(self.canvas.winfo_height(), 340)

        # Dynamic margins to ensure distance tags and badges fit comfortably
        margin_x = 60
        margin_y = 65

        usable_w = w - (2 * margin_x)
        usable_h = h - (2 * margin_y)

        base_size = min(w, h)
        self.node_radius = max(21.0, min(26.0, base_size * 0.045))

        self.node_coords.clear()
        for node, (nx, ny) in self.graph.node_positions.items():
            px = margin_x + nx * usable_w
            py = margin_y + ny * usable_h
            self.node_coords[node] = (px, py)

    def redraw(self) -> None:
        """Completely redraw graph elements: edges, badges, nodes, calculation tags, and legend."""
        self.canvas.delete("all")
        self._calculate_pixel_positions()

        if not self.node_coords:
            return

        # 1. Draw Edges
        self._draw_edges()

        # 2. Draw Edge Weight Badges
        self._draw_edge_badges()

        # 3. Draw Nodes and their Live Calculation Distance Tags
        self._draw_nodes()

        # 4. Draw Legend
        self._draw_legend()

    def _draw_edges(self) -> None:
        """Draw connections between nodes, highlighting active calculation edges and shortest paths."""
        path_edges = set()
        if len(self.highlighted_path) >= 2:
            for i in range(len(self.highlighted_path) - 1):
                u, v = self.highlighted_path[i], self.highlighted_path[i + 1]
                path_edges.add((min(u, v), max(u, v)))

        active_exam_edge = None
        if self.active_edge:
            u, v = self.active_edge
            active_exam_edge = (min(u, v), max(u, v))

        # 1. Draw regular edges
        for u, v, _ in self.graph.get_all_edges():
            edge_key = (min(u, v), max(u, v))
            if edge_key in path_edges or edge_key == active_exam_edge:
                continue

            x1, y1 = self.node_coords[u]
            x2, y2 = self.node_coords[v]

            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=self.COLOR_EDGE,
                width=2.0,
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND,
                tags="edge"
            )

        # 2. Draw active shortest path edges
        for u, v, _ in self.graph.get_all_edges():
            edge_key = (min(u, v), max(u, v))
            if edge_key in path_edges and edge_key != active_exam_edge:
                x1, y1 = self.node_coords[u]
                x2, y2 = self.node_coords[v]

                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill="#93C5FD",
                    width=6.0,
                    capstyle=tk.ROUND,
                    tags="active_path_edge_glow"
                )
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=self.COLOR_EDGE_ACTIVE,
                    width=3.5,
                    capstyle=tk.ROUND,
                    tags="active_path_edge"
                )

        # 3. Draw currently evaluated calculation edge with arrow indicator
        if self.active_edge:
            u, v = self.active_edge
            x1, y1 = self.node_coords[u]
            x2, y2 = self.node_coords[v]

            glow_color = "#A7F3D0" if self.active_edge_status == "UPDATED" else "#FDE68A"
            core_color = self.COLOR_EDGE_CALC_UPDATE if self.active_edge_status == "UPDATED" else self.COLOR_EDGE_CALC_EXAMINE

            # Outer glow
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=glow_color,
                width=8.0,
                capstyle=tk.ROUND,
                tags="active_exam_glow"
            )
            # Core line with arrow indicating relaxation direction
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=core_color,
                width=4.0,
                arrow=tk.LAST,
                arrowshape=(12, 14, 5),
                capstyle=tk.ROUND,
                tags="active_exam_edge"
            )

    def _draw_edge_badges(self) -> None:
        """Draw weight labels inside clean rounded badges offset from edge lines."""
        for u, v, weight in self.graph.get_all_edges():
            x1, y1 = self.node_coords[u]
            x2, y2 = self.node_coords[v]

            dx = x2 - x1
            dy = y2 - y1
            length = math.sqrt(dx * dx + dy * dy)
            if length == 0:
                continue

            tx = dx / length
            ty = dy / length
            nx = -ty
            ny = tx

            key = (min(u, v), max(u, v))
            if (u, v) in self.edge_label_offsets:
                t_pos, norm_offset = self.edge_label_offsets[(u, v)]
            elif (v, u) in self.edge_label_offsets:
                t_pos, norm_offset = self.edge_label_offsets[(v, u)]
                norm_offset = -norm_offset
            else:
                t_pos, norm_offset = 0.5, 12.0

            bx = x1 + t_pos * dx
            by = y1 + t_pos * dy

            badge_x = bx + norm_offset * nx
            badge_y = by + norm_offset * ny

            label_text = str(weight)
            pw, ph = 18, 14

            is_exam_edge = (self.active_edge is not None and key == (min(self.active_edge[0], self.active_edge[1]), max(self.active_edge[0], self.active_edge[1])))
            bg_col = "#FEF3C7" if is_exam_edge else self.COLOR_BADGE_BG
            border_col = "#F59E0B" if is_exam_edge else self.COLOR_BADGE_BORDER

            self.canvas.create_oval(
                badge_x - pw / 2, badge_y - ph / 2,
                badge_x + pw / 2, badge_y + ph / 2,
                fill=bg_col,
                outline=border_col,
                width=1.5 if is_exam_edge else 1.2,
                tags="badge_bg"
            )

            self.canvas.create_text(
                badge_x, badge_y,
                text=label_text,
                fill="#92400E" if is_exam_edge else self.COLOR_BADGE_TEXT,
                font=("Segoe UI", 9, "bold"),
                tags="badge_text"
            )

    def _draw_nodes(self) -> None:
        """Draw nodes, active visiting rings, and live distance computation badges."""
        r = self.node_radius

        for node in self.graph.nodes:
            x, y = self.node_coords[node]
            is_source = (node == self.selected_source)
            is_visiting = (node == self.active_visiting_node)
            is_examining = (node == self.active_neighbor_node)
            is_finalized = (node in self.permanent_nodes)
            is_path_dest = (len(self.highlighted_path) > 1 and node == self.highlighted_path[-1])
            is_hovered = (node == self.hovered_node)

            # 1. Outer Auras & Rings
            if is_visiting:
                # Active Visiting Node: Vibrant Blue Glow Ring
                self.canvas.create_oval(
                    x - r - 8, y - r - 8,
                    x + r + 8, y + r + 8,
                    fill="",
                    outline="#93C5FD",
                    width=4.5,
                    tags="node_ring"
                )
            elif is_examining:
                # Currently Evaluated Neighbor: Amber Glow Ring
                self.canvas.create_oval(
                    x - r - 7, y - r - 7,
                    x + r + 7, y + r + 7,
                    fill="",
                    outline=self.COLOR_NODE_EXAMINE_RING,
                    width=4.0,
                    tags="node_ring"
                )
            elif is_source:
                self.canvas.create_oval(
                    x - r - 6, y - r - 6,
                    x + r + 6, y + r + 6,
                    fill="",
                    outline=self.COLOR_NODE_SOURCE_RING,
                    width=3.5,
                    tags="node_ring"
                )
            elif is_finalized:
                self.canvas.create_oval(
                    x - r - 4, y - r - 4,
                    x + r + 4, y + r + 4,
                    fill="",
                    outline="#BBF7D0",
                    width=2.5,
                    tags="node_ring"
                )
            elif is_hovered:
                self.canvas.create_oval(
                    x - r - 4, y - r - 4,
                    x + r + 4, y + r + 4,
                    fill="",
                    outline="#CBD5E1",
                    width=3.0,
                    tags="node_ring"
                )

            # 2. Main Circle Body
            if is_visiting:
                fill_color = self.COLOR_NODE_SOURCE_BG
                border_color = "#1E40AF"
                text_color = "#FFFFFF"
                border_width = 3.0
            elif is_examining:
                fill_color = self.COLOR_NODE_EXAMINE_BG
                border_color = self.COLOR_NODE_EXAMINE_BORDER
                text_color = self.COLOR_NODE_EXAMINE_TEXT
                border_width = 2.8
            elif is_source:
                fill_color = self.COLOR_NODE_SOURCE_BG
                border_color = self.COLOR_NODE_SOURCE_BORDER
                text_color = self.COLOR_NODE_SOURCE_TEXT
                border_width = 2.5
            elif is_finalized:
                fill_color = "#ECFDF5"
                border_color = self.COLOR_NODE_FINAL_BORDER
                text_color = "#065F46"
                border_width = 2.4
            else:
                fill_color = "#F8FAFC" if is_hovered else self.COLOR_NODE_DEFAULT_BG
                border_color = self.COLOR_NODE_DEFAULT_BORDER
                text_color = self.COLOR_NODE_DEFAULT_TEXT
                border_width = 2.0

            self.canvas.create_oval(
                x - r, y - r,
                x + r, y + r,
                fill=fill_color,
                outline=border_color,
                width=border_width,
                tags=(f"node_{node}", "node_body")
            )

            # 3. Node Letter
            self.canvas.create_text(
                x, y,
                text=node,
                fill=text_color,
                font=("Segoe UI", 12, "bold"),
                tags=(f"node_{node}", "node_text")
            )

            # 4. Live Distance Calculation Tag (Above the Node)
            self._draw_distance_pill(node, x, y - r - 15, is_finalized, is_visiting, is_examining)

    def _draw_distance_pill(
        self,
        node: str,
        cx: float,
        cy: float,
        is_finalized: bool,
        is_visiting: bool,
        is_examining: bool
    ) -> None:
        """Render a crisp rounded pill showing the live tentative or finalized distance."""
        dist_val = self.current_distances.get(node, float("inf"))
        dist_str = format_distance(dist_val)

        if is_finalized:
            tag_text = f"dist: {dist_str} ✓"
            pill_bg = "#DCFCE7"
            pill_border = "#86EFAC"
            pill_fg = "#166534"
        elif is_examining:
            tag_text = f"cand: {dist_str}"
            pill_bg = "#FEF3C7"
            pill_border = "#F59E0B"
            pill_fg = "#B45309"
        elif is_visiting:
            tag_text = f"visit: {dist_str}"
            pill_bg = "#DBEAFE"
            pill_border = "#3B82F6"
            pill_fg = "#1E40AF"
        elif math.isinf(dist_val):
            tag_text = "dist: ∞"
            pill_bg = "#F8FAFC"
            pill_border = "#E2E8F0"
            pill_fg = "#94A3B8"
        else:
            tag_text = f"dist: {dist_str} ⏳"
            pill_bg = "#EFF6FF"
            pill_border = "#BFDBFE"
            pill_fg = "#1D4ED8"

        pw = max(52, len(tag_text) * 7.5 + 14)
        ph = 17

        # Rounded rectangle for distance pill
        self.canvas.create_rectangle(
            cx - pw / 2, cy - ph / 2,
            cx + pw / 2, cy + ph / 2,
            fill=pill_bg,
            outline=pill_border,
            width=1.2,
            tags="dist_pill_bg"
        )

        self.canvas.create_text(
            cx, cy,
            text=tag_text,
            fill=pill_fg,
            font=("Segoe UI", 8, "bold"),
            tags="dist_pill_text"
        )

    def _draw_legend(self) -> None:
        """Render an explanatory legend for the interactive calculation features."""
        w = max(self.canvas.winfo_width(), 420)
        h = max(self.canvas.winfo_height(), 340)

        lx = 14
        ly = h - 34

        self.canvas.create_rectangle(
            lx - 4, ly - 8,
            lx + 560, ly + 22,
            fill="#F8FAFC",
            outline="#E2E8F0",
            width=1.0,
            tags="legend"
        )

        # 1. Source / Visiting
        self.canvas.create_oval(lx + 4, ly + 2, lx + 16, ly + 14, fill=self.COLOR_NODE_SOURCE_BG, outline="#1D4ED8", width=1.5)
        self.canvas.create_text(lx + 22, ly + 8, text="Source / Visiting", anchor="w", fill="#334155", font=("Segoe UI", 8, "bold"))

        # 2. Finalized Node
        self.canvas.create_oval(lx + 128, ly + 2, lx + 140, ly + 14, fill="#ECFDF5", outline=self.COLOR_NODE_FINAL_BORDER, width=1.5)
        self.canvas.create_text(lx + 146, ly + 8, text="Finalized (Permanent ✓)", anchor="w", fill="#334155", font=("Segoe UI", 8, "bold"))

        # 3. Examining Neighbor
        self.canvas.create_oval(lx + 292, ly + 2, lx + 304, ly + 14, fill=self.COLOR_NODE_EXAMINE_BG, outline=self.COLOR_NODE_EXAMINE_BORDER, width=1.5)
        self.canvas.create_text(lx + 310, ly + 8, text="Evaluating Neighbor", anchor="w", fill="#334155", font=("Segoe UI", 8, "bold"))

        # 4. Live Distance Tag
        self.canvas.create_rectangle(lx + 436, ly + 2, lx + 476, ly + 14, fill="#EFF6FF", outline="#BFDBFE", width=1.0)
        self.canvas.create_text(lx + 456, ly + 8, text="dist: ⏳", fill="#1D4ED8", font=("Segoe UI", 7, "bold"))
        self.canvas.create_text(lx + 482, ly + 8, text="Live Distance Tag", anchor="w", fill="#334155", font=("Segoe UI", 8, "bold"))

    def _get_node_at(self, px: float, py: float) -> Optional[str]:
        """Check if pixel coordinates fall within any node circle."""
        click_radius = self.node_radius + 6.0
        for node, (nx, ny) in self.node_coords.items():
            dist = math.sqrt((px - nx) ** 2 + (py - ny) ** 2)
            if dist <= click_radius:
                return node
        return None

    def _on_click(self, event) -> None:
        """Handle canvas node click to set new source."""
        clicked_node = self._get_node_at(event.x, event.y)
        if clicked_node is not None:
            self.on_node_selected(clicked_node)

    def _on_motion(self, event) -> None:
        """Provide smooth cursor and hover highlight feedback."""
        hovered = self._get_node_at(event.x, event.y)
        if hovered != self.hovered_node:
            self.hovered_node = hovered
            self.canvas.config(cursor="hand2" if hovered is not None else "arrow")
            self.redraw()

    def _on_leave(self, event) -> None:
        """Reset hover state when mouse leaves canvas."""
        if self.hovered_node is not None:
            self.hovered_node = None
            self.canvas.config(cursor="arrow")
            self.redraw()
