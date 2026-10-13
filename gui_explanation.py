"""
gui_explanation.py
------------------
Dedicated Step-by-Step Explanation Window for Dijkstra Network Explorer.
Renders an interactive, scrollable breakdown of every iteration, neighbor
relaxation, Temporary List and Permanent List state transitions, and final
routing summary. Synchronizes live with the main dashboard.
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from dijkstra import DijkstraResult, DijkstraStep, NeighborEvaluation


class ExplanationWindow(tk.Toplevel):
    """Large, scrollable Toplevel window displaying detailed step-by-step trace."""

    def __init__(self, parent: tk.Widget, result: DijkstraResult, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.result = result

        # Window settings
        self.title(f"Dijkstra Algorithm Walkthrough — Source Node {result.source}")
        self.geometry("860x740")
        self.minsize(700, 500)
        self.configure(bg="#F8FAFC")

        # Keep alive tracking
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self.render_explanation(result)

    def _on_close(self) -> None:
        """Destroy window and notify parent if tracked."""
        self.destroy()

    def update_result(self, result: DijkstraResult) -> None:
        """Update trace contents dynamically when user picks another source node."""
        self.result = result
        self.title(f"Dijkstra Algorithm Walkthrough — Source Node {result.source}")
        self.render_explanation(result)

    def _build_ui(self) -> None:
        """Create scrollable container and header controls."""
        # Top sticky header
        header_bar = tk.Frame(self, bg="#FFFFFF", bd=0, highlightthickness=1, highlightbackground="#E2E8F0")
        header_bar.pack(fill=tk.X, side=tk.TOP)

        header_inner = tk.Frame(header_bar, bg="#FFFFFF")
        header_inner.pack(fill=tk.X, padx=20, pady=12)

        self.header_title = tk.Label(
            header_inner,
            text=f"Algorithm Execution Trace: Source {self.result.source}",
            font=("Segoe UI", 13, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
        )
        self.header_title.pack(side=tk.LEFT)

        sync_badge = tk.Label(
            header_inner,
            text="● Live Synchronized",
            font=("Segoe UI", 9, "bold"),
            fg="#16A34A",
            bg="#DCFCE7",
            padx=8,
            pady=3,
        )
        sync_badge.pack(side=tk.LEFT, padx=(12, 0))

        # Copy explanation button
        copy_btn = tk.Button(
            header_inner,
            text="📋 Copy Plain Text Trace",
            command=self._copy_to_clipboard,
            font=("Segoe UI", 9),
            bg="#F1F5F9",
            fg="#334155",
            relief="flat",
            activebackground="#E2E8F0",
            cursor="hand2",
            padx=10,
            pady=3,
        )
        copy_btn.pack(side=tk.RIGHT)

        # Scrollable area
        canvas_frame = tk.Frame(self, bg="#F8FAFC")
        canvas_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        self.canvas = tk.Canvas(canvas_frame, bg="#F8FAFC", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)

        self.scrollable_frame = tk.Frame(self.canvas, bg="#F8FAFC")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Ensure scrollable frame expands with canvas width
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window_id, width=e.width)
        )

        # Mousewheel scrolling
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event) -> None:
        """Handle mouse wheel scrolling."""
        if self.winfo_exists() and self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _copy_to_clipboard(self) -> None:
        """Copy formatted explanation text to clipboard."""
        text = self._generate_plain_text_explanation()
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo(
            "Copied",
            "The full step-by-step Dijkstra trace has been copied to your clipboard!",
            parent=self,
        )

    def render_explanation(self, result: DijkstraResult) -> None:
        """Clear and redraw all cards for the current result."""
        self.header_title.config(text=f"Algorithm Execution Trace: Source {result.source}")

        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        content = tk.Frame(self.scrollable_frame, bg="#F8FAFC")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        # 1. Initialization Overview Card
        self._render_init_card(content, result)

        # 2. Iteration Cards (Step 1..N)
        for step in result.steps:
            self._render_step_card(content, step)

        # 3. Final Routing Summary Card
        self._render_final_summary_card(content, result)

    def _render_init_card(self, parent: tk.Widget, result: DijkstraResult) -> None:
        """Render card showing initialization state before step 1."""
        card = tk.Frame(parent, bg="#FFFFFF", bd=0, highlightthickness=1, highlightbackground="#E2E8F0")
        card.pack(fill=tk.X, pady=(0, 14))

        header = tk.Frame(card, bg="#F1F5F9")
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="Initial Algorithm Setup (Pre-Iteration State)",
            font=("Segoe UI", 10, "bold"),
            fg="#1E293B",
            bg="#F1F5F9",
            padx=14,
            pady=8,
        ).pack(side=tk.LEFT)

        body = tk.Frame(card, bg="#FFFFFF", padx=14, pady=12)
        body.pack(fill=tk.X)

        init_temp_str = ", ".join(f"{n}({'∞' if math.isinf(d) else int(d)})" for n, d in result.initial_temp_list)

        setup_text = (
            f"1. Source distance initialized: dist[{result.source}] = 0\n"
            f"2. All other node distances initialized: dist[v] = ∞\n"
            f"3. All predecessors initialized to None (empty)\n"
            f"4. Initial Temporary List: {init_temp_str}\n"
            f"5. Initial Permanent List: Empty (Ø)"
        )

        tk.Label(
            body,
            text=setup_text,
            font=("Segoe UI", 9),
            fg="#334155",
            bg="#FFFFFF",
            justify=tk.LEFT,
        ).pack(anchor="w")

    def _render_step_card(self, parent: tk.Widget, step: DijkstraStep) -> None:
        """Render card for a single Dijkstra iteration step."""
        card = tk.Frame(parent, bg="#FFFFFF", bd=0, highlightthickness=1, highlightbackground="#CBD5E1")
        card.pack(fill=tk.X, pady=(0, 14))

        # Step Header
        header = tk.Frame(card, bg="#EFF6FF")
        header.pack(fill=tk.X)

        title_text = f"Step {step.step_number}: Selected Node '{step.selected_node}'"
        tk.Label(
            header,
            text=title_text,
            font=("Segoe UI", 11, "bold"),
            fg="#1E40AF",
            bg="#EFF6FF",
            padx=14,
            pady=8,
        ).pack(side=tk.LEFT)

        cost_val = int(step.selected_distance) if step.selected_distance.is_integer() else step.selected_distance
        cost_badge = tk.Label(
            header,
            text=f"Current Distance = {cost_val}",
            font=("Segoe UI", 9, "bold"),
            fg="#1E40AF",
            bg="#DBEAFE",
            padx=10,
            pady=4,
        )
        cost_badge.pack(side=tk.RIGHT, padx=14)

        # Body
        body = tk.Frame(card, bg="#FFFFFF", padx=14, pady=10)
        body.pack(fill=tk.X)

        # Section A & B: Selection rationale & Current distance
        tk.Label(
            body,
            text=f"• Selection Rationale: {step.selection_reason}",
            font=("Segoe UI", 9, "italic"),
            fg="#475569",
            bg="#FFFFFF",
            wraplength=760,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(0, 8))

        # Section C: Neighbor Examination
        tk.Label(
            body,
            text="Neighbor Examination & Relaxation:",
            font=("Segoe UI", 9, "bold"),
            fg="#1E293B",
            bg="#FFFFFF",
        ).pack(anchor="w", pady=(2, 4))

        for n_eval in step.neighbor_evaluations:
            self._render_neighbor_box(body, step.selected_node, step.selected_distance, n_eval)

        # Section D & E: Temporary and Permanent Lists after iteration
        list_box = tk.Frame(body, bg="#F8FAFC", bd=0, highlightthickness=1, highlightbackground="#E2E8F0", padx=10, pady=8)
        list_box.pack(fill=tk.X, pady=(10, 0))

        # Permanent List (Finalized)
        perm_frame = tk.Frame(list_box, bg="#F8FAFC")
        perm_frame.pack(fill=tk.X, pady=(0, 4))

        tk.Label(
            perm_frame,
            text="Permanent List:",
            font=("Segoe UI", 9, "bold"),
            fg="#047857",
            bg="#F8FAFC",
            width=14,
            anchor="w",
        ).pack(side=tk.LEFT)

        tk.Label(
            perm_frame,
            text=step.perm_list_str(),
            font=("Consolas", 9, "bold"),
            fg="#065F46",
            bg="#D1FAE5",
            padx=8,
            pady=2,
        ).pack(side=tk.LEFT)

        # Temporary List (Unfinalized)
        temp_frame = tk.Frame(list_box, bg="#F8FAFC")
        temp_frame.pack(fill=tk.X)

        tk.Label(
            temp_frame,
            text="Temporary List:",
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="#F8FAFC",
            width=14,
            anchor="w",
        ).pack(side=tk.LEFT)

        tk.Label(
            temp_frame,
            text=step.temp_list_str(),
            font=("Consolas", 9),
            fg="#1E293B",
            bg="#F1F5F9",
            padx=8,
            pady=2,
        ).pack(side=tk.LEFT)

    def _render_neighbor_box(
        self,
        parent: tk.Widget,
        selected_node: str,
        selected_dist: float,
        neval: NeighborEvaluation
    ) -> None:
        """Render single neighbor relaxation breakdown matching exact prompt specification."""
        if neval.already_finalized:
            bg_color = "#F8FAFC"
            border_color = "#E2E8F0"
            badge_text = "SKIPPED"
            badge_bg = "#E2E8F0"
            badge_fg = "#475569"
        elif neval.is_updated:
            bg_color = "#F0FDF4"
            border_color = "#86EFAC"
            badge_text = "✓ UPDATED"
            badge_bg = "#DCFCE7"
            badge_fg = "#15803D"
        else:
            bg_color = "#FFFBEB"
            border_color = "#FDE68A"
            badge_text = "UNCHANGED"
            badge_bg = "#FEF3C7"
            badge_fg = "#B45309"

        box = tk.Frame(parent, bg=bg_color, bd=0, highlightthickness=1, highlightbackground=border_color, padx=10, pady=6)
        box.pack(fill=tk.X, pady=3)

        top_line = tk.Frame(box, bg=bg_color)
        top_line.pack(fill=tk.X)

        tk.Label(
            top_line,
            text=f"Neighbor: Node {neval.neighbor}  |  Edge {selected_node} — {neval.neighbor} (weight = {neval.edge_weight})",
            font=("Segoe UI", 9, "bold"),
            fg="#1E293B",
            bg=bg_color,
        ).pack(side=tk.LEFT)

        tk.Label(
            top_line,
            text=badge_text,
            font=("Segoe UI", 8, "bold"),
            fg=badge_fg,
            bg=badge_bg,
            padx=6,
            pady=1,
        ).pack(side=tk.RIGHT)

        # Calculation breakdown
        calc_frame = tk.Frame(box, bg=bg_color)
        calc_frame.pack(fill=tk.X, pady=(4, 0))

        dist_sel_str = str(int(selected_dist) if selected_dist.is_integer() else selected_dist)
        cand_str = neval.format_distance(neval.candidate_distance)
        curr_str = neval.format_distance(neval.current_known_distance)

        if neval.already_finalized:
            detail_str = f"Node {neval.neighbor} was already finalized in a previous step with distance {curr_str}."
        elif neval.is_updated:
            pred_prev = neval.predecessor_before or "None"
            detail_str = (
                f"Candidate distance = {dist_sel_str} + {neval.edge_weight} = {cand_str}\n"
                f"Previous distance to {neval.neighbor} = {curr_str}\n"
                f"Result: Candidate ({cand_str}) < Previous ({curr_str}) → Updated distance to {cand_str}, predecessor set to '{selected_node}' (was {pred_prev})."
            )
        else:
            detail_str = (
                f"Candidate distance = {dist_sel_str} + {neval.edge_weight} = {cand_str}\n"
                f"Previous distance to {neval.neighbor} = {curr_str}\n"
                f"Result: Candidate ({cand_str}) ≥ Current ({curr_str}) → Kept existing distance {curr_str}, predecessor unchanged ({neval.predecessor_after or 'None'})."
            )

        tk.Label(
            calc_frame,
            text=detail_str,
            font=("Consolas", 8),
            fg="#334155",
            bg=bg_color,
            justify=tk.LEFT,
        ).pack(anchor="w")

    def _render_final_summary_card(self, parent: tk.Widget, result: DijkstraResult) -> None:
        """Render final routing summary at end of trace."""
        card = tk.Frame(parent, bg="#FFFFFF", bd=0, highlightthickness=1, highlightbackground="#CBD5E1")
        card.pack(fill=tk.X, pady=(6, 14))

        header = tk.Frame(card, bg="#F8FAFC")
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text=f"Final Routing Summary from Source '{result.source}'",
            font=("Segoe UI", 11, "bold"),
            fg="#0F172A",
            bg="#F8FAFC",
            padx=14,
            pady=8,
        ).pack(side=tk.LEFT)

        body = tk.Frame(card, bg="#FFFFFF", padx=14, pady=12)
        body.pack(fill=tk.X)

        summary_table = tk.Frame(body, bg="#FFFFFF")
        summary_table.pack(fill=tk.X)

        # Header row
        headers = ["Destination", "Shortest Distance", "Next Hop", "Complete Shortest Path"]
        widths = [14, 18, 12, 28]

        hrow = tk.Frame(summary_table, bg="#F1F5F9", pady=4)
        hrow.pack(fill=tk.X)
        for h, w in zip(headers, widths):
            tk.Label(
                hrow,
                text=h,
                font=("Segoe UI", 9, "bold"),
                fg="#334155",
                bg="#F1F5F9",
                width=w,
                anchor="w",
            ).pack(side=tk.LEFT, padx=6)

        # Data rows
        for dest in sorted(result.routing_table.keys()):
            entry = result.routing_table[dest]
            is_src = (dest == result.source)
            row_bg = "#EFF6FF" if is_src else "#FFFFFF"

            row = tk.Frame(summary_table, bg=row_bg, pady=4)
            row.pack(fill=tk.X)

            vals = [
                f"Node {dest}" + (" (Source)" if is_src else ""),
                entry.distance_display,
                entry.next_hop,
                entry.path_str,
            ]

            for val, w in zip(vals, widths):
                tk.Label(
                    row,
                    text=val,
                    font=("Segoe UI", 9, "bold" if is_src else "normal"),
                    fg="#1D4ED8" if is_src else "#1E293B",
                    bg=row_bg,
                    width=w,
                    anchor="w",
                ).pack(side=tk.LEFT, padx=6)

    def _generate_plain_text_explanation(self) -> str:
        """Format the complete trace into plain text for copying."""
        init_temp_str = ", ".join(f"{n}({'∞' if math.isinf(d) else int(d)})" for n, d in self.result.initial_temp_list)
        lines = [
            "=" * 70,
            f"DIJKSTRA SHORTEST-PATH ALGORITHM TRACE — SOURCE: {self.result.source}",
            "=" * 70,
            "",
            "INITIAL STATE:",
            f"• Source node: {self.result.source} (Distance = 0)",
            f"• Initial Temporary List: {init_temp_str}",
            "• Initial Permanent List: Empty (Ø)",
            "",
        ]

        for step in self.result.steps:
            lines.append("-" * 70)
            cost_str = int(step.selected_distance) if step.selected_distance.is_integer() else step.selected_distance
            lines.append(f"STEP {step.step_number}: Selected Node '{step.selected_node}' (Cost = {cost_str})")
            lines.append(f"Reason: {step.selection_reason}")
            lines.append("\nNeighbor Examinations:")
            for ne in step.neighbor_evaluations:
                lines.append(ne.detailed_text())
            lines.append(f"\nTemporary List: {step.temp_list_str()}")
            lines.append(f"Permanent List: {step.perm_list_str()}")
            lines.append("")

        lines.append("=" * 70)
        lines.append("FINAL ROUTING TABLE SUMMARY:")
        lines.append(f"{'Destination':<15} {'Distance':<12} {'Next Hop':<12} {'Complete Shortest Path'}")
        lines.append("-" * 70)
        for dest in sorted(self.result.routing_table.keys()):
            e = self.result.routing_table[dest]
            lines.append(f"Node {e.destination:<10} {e.distance_display:<12} {e.next_hop:<12} {e.path_str}")
        lines.append("=" * 70)

        return "\n".join(lines)
