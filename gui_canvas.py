"""
gui_canvas.py
-------------
Interactive Network Graph Canvas for Dijkstra Network Explorer.
Renders nodes, weighted edges, badges, hover feedback, responsive resizing,
and active shortest-path highlighting.
"""

import math
import tkinter as tk
from typing import Dict, List, Tuple, Optional, Callable
from graph import NetworkGraph


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

        # Cached pixel positions of nodes
        self.node_coords: Dict[str, Tuple[float, float]] = {}
        self.node_radius: float = 24.0

        # Colors (Modern Light Theme)
        self.COLOR_BG = "#FFFFFF"
        self.COLOR_PANEL_BORDER = "#E2E8F0"
        self.COLOR_EDGE = "#94A3B8"
        self.COLOR_EDGE_ACTIVE = "#2563EB"
        self.COLOR_EDGE_HOVER = "#64748B"
        
        self.COLOR_NODE_DEFAULT_BG = "#FFFFFF"
        self.COLOR_NODE_DEFAULT_BORDER = "#334155"
        self.COLOR_NODE_DEFAULT_TEXT = "#0F172A"

        self.COLOR_NODE_SOURCE_BG = "#2563EB"
        self.COLOR_NODE_SOURCE_BORDER = "#1D4ED8"
        self.COLOR_NODE_SOURCE_RING = "#BFDBFE"
        self.COLOR_NODE_SOURCE_TEXT = "#FFFFFF"

        self.COLOR_NODE_PATH_BG = "#10B981"
        self.COLOR_NODE_PATH_BORDER = "#059669"
        self.COLOR_NODE_PATH_RING = "#A7F3D0"
        self.COLOR_NODE_PATH_TEXT = "#FFFFFF"

        self.COLOR_BADGE_BG = "#FFFFFF"
        self.COLOR_BADGE_BORDER = "#CBD5E1"
        self.COLOR_BADGE_TEXT = "#1E293B"

        # Edge label placement parameters: (u, v) -> (t_along_edge, normal_offset_pixels)
        # t in [0.0, 1.0]: 0.5 is midpoint. Offset is perpendicular in pixels.
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
        """Update selected source and redraw."""
        self.selected_source = source
        self.highlighted_path = []
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
        w = max(self.canvas.winfo_width(), 400)
        h = max(self.canvas.winfo_height(), 320)

        # Dynamic margins to ensure nodes and badges fit comfortably
        margin_x = 55
        margin_y = 50

        usable_w = w - (2 * margin_x)
        usable_h = h - (2 * margin_y)

        # Adapt node radius smoothly to canvas dimensions
        base_size = min(w, h)
        self.node_radius = max(20.0, min(26.0, base_size * 0.045))

        self.node_coords.clear()
        for node, (nx, ny) in self.graph.node_positions.items():
            px = margin_x + nx * usable_w
            py = margin_y + ny * usable_h
            self.node_coords[node] = (px, py)

    def redraw(self) -> None:
        """Completely redraw graph elements: edges, badges, nodes, and legend."""
        self.canvas.delete("all")
        self._calculate_pixel_positions()

        if not self.node_coords:
            return

        # 1. Draw Edges
        self._draw_edges()

        # 2. Draw Edge Weight Badges
        self._draw_edge_badges()

        # 3. Draw Nodes
        self._draw_nodes()

        # 4. Draw Legend
        self._draw_legend()

    def _draw_edges(self) -> None:
        """Draw connections between nodes."""
        # Set of edges currently on the highlighted shortest path
        path_edges = set()
        if len(self.highlighted_path) >= 2:
            for i in range(len(self.highlighted_path) - 1):
                u, v = self.highlighted_path[i], self.highlighted_path[i + 1]
                path_edges.add((min(u, v), max(u, v)))

        # Draw regular edges first
        for u, v, _ in self.graph.get_all_edges():
            edge_key = (min(u, v), max(u, v))
            if edge_key in path_edges:
                continue  # Draw active path edges on top

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

        # Draw active shortest path edges prominently
        for u, v, _ in self.graph.get_all_edges():
            edge_key = (min(u, v), max(u, v))
            if edge_key in path_edges:
                x1, y1 = self.node_coords[u]
                x2, y2 = self.node_coords[v]

                # Outer glow for path edge
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill="#93C5FD",
                    width=6.0,
                    capstyle=tk.ROUND,
                    tags="active_path_edge_glow"
                )
                # Core active path edge
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=self.COLOR_EDGE_ACTIVE,
                    width=3.5,
                    capstyle=tk.ROUND,
                    tags="active_path_edge"
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

            # Normalized tangent and perpendicular normal vectors
            tx = dx / length
            ty = dy / length
            nx = -ty
            ny = tx

            # Lookup specific offset config
            key = (min(u, v), max(u, v))
            if (u, v) in self.edge_label_offsets:
                t_pos, norm_offset = self.edge_label_offsets[(u, v)]
            elif (v, u) in self.edge_label_offsets:
                t_pos, norm_offset = self.edge_label_offsets[(v, u)]
                norm_offset = -norm_offset
            else:
                t_pos, norm_offset = 0.5, 12.0

            # Base point along edge
            bx = x1 + t_pos * dx
            by = y1 + t_pos * dy

            # Offset point
            badge_x = bx + norm_offset * nx
            badge_y = by + norm_offset * ny

            # Badge pill dimensions
            label_text = str(weight)
            pw, ph = 18, 14

            # Draw white badge pill with subtle border
            self.canvas.create_oval(
                badge_x - pw / 2, badge_y - ph / 2,
                badge_x + pw / 2, badge_y + ph / 2,
                fill=self.COLOR_BADGE_BG,
                outline=self.COLOR_BADGE_BORDER,
                width=1.2,
                tags="badge_bg"
            )

            # Badge text
            self.canvas.create_text(
                badge_x, badge_y,
                text=label_text,
                fill=self.COLOR_BADGE_TEXT,
                font=("Segoe UI", 9, "bold"),
                tags="badge_text"
            )

    def _draw_nodes(self) -> None:
        """Draw each node with distinct states for source, path, hover, and regular."""
        r = self.node_radius

        for node in self.graph.nodes:
            x, y = self.node_coords[node]
            is_source = (node == self.selected_source)
            is_path_dest = (len(self.highlighted_path) > 1 and node == self.highlighted_path[-1])
            is_on_path = (node in self.highlighted_path and not is_source and not is_path_dest)
            is_hovered = (node == self.hovered_node)

            # 1. Outer Glow Ring for source or path dest
            if is_source:
                self.canvas.create_oval(
                    x - r - 6, y - r - 6,
                    x + r + 6, y + r + 6,
                    fill="",
                    outline=self.COLOR_NODE_SOURCE_RING,
                    width=4.0,
                    tags="node_ring"
                )
            elif is_path_dest:
                self.canvas.create_oval(
                    x - r - 5, y - r - 5,
                    x + r + 5, y + r + 5,
                    fill="",
                    outline=self.COLOR_NODE_PATH_RING,
                    width=4.0,
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

            # 2. Main Node Circle
            if is_source:
                fill_color = self.COLOR_NODE_SOURCE_BG
                border_color = self.COLOR_NODE_SOURCE_BORDER
                text_color = self.COLOR_NODE_SOURCE_TEXT
                border_width = 2.5
            elif is_path_dest:
                fill_color = self.COLOR_NODE_PATH_BG
                border_color = self.COLOR_NODE_PATH_BORDER
                text_color = self.COLOR_NODE_PATH_TEXT
                border_width = 2.5
            elif is_on_path:
                fill_color = "#E0E7FF"
                border_color = "#4338CA"
                text_color = "#1E1B4B"
                border_width = 2.0
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

            # 3. Node Letter Label
            self.canvas.create_text(
                x, y,
                text=node,
                fill=text_color,
                font=("Segoe UI", 12, "bold"),
                tags=(f"node_{node}", "node_text")
            )

    def _draw_legend(self) -> None:
        """Render a compact, elegant legend explaining node & edge styling."""
        w = max(self.canvas.winfo_width(), 400)
        h = max(self.canvas.winfo_height(), 320)

        lx = 14
        ly = h - 34

        # Background card for legend
        self.canvas.create_rectangle(
            lx - 4, ly - 8,
            lx + 430, ly + 22,
            fill="#F8FAFC",
            outline="#E2E8F0",
            width=1.0,
            tags="legend"
        )

        # Legend item 1: Selected Source
        self.canvas.create_oval(lx + 6, ly + 2, lx + 18, ly + 14, fill=self.COLOR_NODE_SOURCE_BG, outline=self.COLOR_NODE_SOURCE_BORDER, width=1.5)
        self.canvas.create_text(lx + 24, ly + 8, text="Source Node", anchor="w", fill="#475569", font=("Segoe UI", 8, "bold"))

        # Legend item 2: Destination / Path
        self.canvas.create_oval(lx + 104, ly + 2, lx + 116, ly + 14, fill=self.COLOR_NODE_PATH_BG, outline=self.COLOR_NODE_PATH_BORDER, width=1.5)
        self.canvas.create_text(lx + 122, ly + 8, text="Active Path Dest", anchor="w", fill="#475569", font=("Segoe UI", 8, "bold"))

        # Legend item 3: Regular Node
        self.canvas.create_oval(lx + 222, ly + 2, lx + 234, ly + 14, fill=self.COLOR_NODE_DEFAULT_BG, outline=self.COLOR_NODE_DEFAULT_BORDER, width=1.5)
        self.canvas.create_text(lx + 240, ly + 8, text="Network Node", anchor="w", fill="#475569", font=("Segoe UI", 8, "bold"))

        # Legend item 4: Edge weight
        self.canvas.create_line(lx + 328, ly + 8, lx + 352, ly + 8, fill=self.COLOR_EDGE, width=2.0)
        self.canvas.create_oval(lx + 335, ly + 2, lx + 345, ly + 14, fill="#FFFFFF", outline="#CBD5E1", width=1.0)
        self.canvas.create_text(lx + 358, ly + 8, text="Edge (Weight)", anchor="w", fill="#475569", font=("Segoe UI", 8, "bold"))

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
