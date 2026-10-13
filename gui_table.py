"""
gui_table.py
------------
Live Routing Table Widget for Dijkstra Network Explorer.
Displays Destination, Shortest Distance, Next Hop, and Complete Shortest Path
with alternating row colors, source node highlight, and interactive path selection.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Callable
from dijkstra import RoutingEntry


class RoutingTableView(tk.Frame):
    """Modern interactive table showing the live routing table."""

    def __init__(
        self,
        parent: tk.Widget,
        on_path_selected: Optional[Callable[[List[str]], None]] = None,
        **kwargs
    ):
        super().__init__(parent, bg="#FFFFFF", **kwargs)
        self.on_path_selected = on_path_selected
        self.current_entries: Dict[str, RoutingEntry] = {}
        self.source_node: str = "A"

        self._init_style()
        self._build_ui()

    def _init_style(self) -> None:
        """Configure ttk Treeview styles for clean modern aesthetics."""
        style = ttk.Style()
        style.theme_use("clam")

        # Configure Treeview styling
        style.configure(
            "Routing.Treeview",
            background="#FFFFFF",
            foreground="#1E293B",
            rowheight=30,
            fieldbackground="#FFFFFF",
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        style.configure(
            "Routing.Treeview.Heading",
            background="#F1F5F9",
            foreground="#334155",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padding=(6, 8),
        )
        style.map(
            "Routing.Treeview.Heading",
            background=[("active", "#E2E8F0")],
            relief=[("pressed", "flat")],
        )

    def _build_ui(self) -> None:
        """Assemble the table widget with headers and scrollbars."""
        # Top banner info
        header_frame = tk.Frame(self, bg="#FFFFFF")
        header_frame.pack(fill=tk.X, padx=12, pady=(10, 6))

        title_lbl = tk.Label(
            header_frame,
            text="LIVE ROUTING TABLE",
            font=("Segoe UI", 10, "bold"),
            fg="#1E293B",
            bg="#FFFFFF",
        )
        title_lbl.pack(side=tk.LEFT)

        hint_lbl = tk.Label(
            header_frame,
            text="(Click a row to highlight path)",
            font=("Segoe UI", 8),
            fg="#64748B",
            bg="#FFFFFF",
        )
        hint_lbl.pack(side=tk.LEFT, padx=(8, 0))

        # Container frame for treeview + scrollbar with border
        container = tk.Frame(self, bg="#E2E8F0", bd=1)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        columns = ("dest", "dist", "next_hop", "path")
        self.tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            style="Routing.Treeview",
            selectmode="browse",
        )

        # Define column headings and widths
        self.tree.heading("dest", text="Destination", anchor=tk.CENTER)
        self.tree.heading("dist", text="Cost / Dist", anchor=tk.CENTER)
        self.tree.heading("next_hop", text="Next Hop", anchor=tk.CENTER)
        self.tree.heading("path", text="Complete Shortest Path", anchor=tk.W)

        self.tree.column("dest", width=90, minwidth=70, anchor=tk.CENTER)
        self.tree.column("dist", width=85, minwidth=70, anchor=tk.CENTER)
        self.tree.column("next_hop", width=85, minwidth=70, anchor=tk.CENTER)
        self.tree.column("path", width=180, minwidth=140, anchor=tk.W)

        # Scrollbar
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Tag configurations for colors
        self.tree.tag_configure("source_row", background="#EFF6FF", foreground="#1D4ED8", font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("even_row", background="#FFFFFF", foreground="#1E293B")
        self.tree.tag_configure("odd_row", background="#F8FAFC", foreground="#1E293B")
        self.tree.tag_configure("selected_path", background="#ECFDF5", foreground="#065F46", font=("Segoe UI", 9, "bold"))

        # Row selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    def update_table(self, source: str, entries: Dict[str, RoutingEntry]) -> None:
        """Refresh routing table rows for the current source node."""
        self.source_node = source
        self.current_entries = entries

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert sorted by destination
        destinations = sorted(entries.keys())
        for idx, dest in enumerate(destinations):
            entry = entries[dest]
            is_source = (dest == source)

            tag = "source_row" if is_source else ("even_row" if idx % 2 == 0 else "odd_row")

            dest_display = f"Node {dest}" + (" (Source)" if is_source else "")
            dist_display = entry.distance_display
            next_hop_display = entry.next_hop
            path_display = entry.path_str

            self.tree.insert(
                "",
                tk.END,
                iid=dest,
                values=(dest_display, dist_display, next_hop_display, path_display),
                tags=(tag,)
            )

    def _on_row_select(self, event) -> None:
        """Notify listener when user clicks a row to highlight that path."""
        selected_items = self.tree.selection()
        if not selected_items or not self.on_path_selected:
            return

        selected_dest = selected_items[0]
        if selected_dest in self.current_entries:
            path = self.current_entries[selected_dest].path
            self.on_path_selected(path)
