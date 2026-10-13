"""
gui_working_panel.py
--------------------
Interactive Step-by-Step Working & Distance Calculation Panel for Dijkstra Network Explorer.
Provides stepper controls (Reset, Prev, Play/Pause, Next, Jump to End), speed controls,
slider scrubbing, live mathematical formulas, candidate comparisons, and set snapshots.
"""

import math
import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable
from dijkstra import SimulationFrame, format_distance


class WorkingCalculationPanel(tk.Frame):
    """Renders the actual working, formulas, and stepper playback controls."""

    def __init__(
        self,
        parent: tk.Widget,
        on_frame_change: Callable[[int], None],
        **kwargs
    ):
        super().__init__(parent, bg="#FFFFFF", bd=0, highlightthickness=1, highlightbackground="#E2E8F0", **kwargs)
        self.on_frame_change = on_frame_change

        self.frames: List[SimulationFrame] = []
        self.current_frame_idx: int = 0
        self.is_playing: bool = False
        self.playback_speed_ms: int = 1100  # Default 1.1s
        self._timer_id: Optional[str] = None

        self._build_ui()

    def set_frames(self, frames: List[SimulationFrame]) -> None:
        """Load new simulation frames from DijkstraResult."""
        self.stop_playback()
        self.frames = frames
        self.current_frame_idx = 0

        # Update slider range
        max_idx = max(0, len(frames) - 1)
        self.slider.config(to=max_idx)
        self.slider.set(0)

        self.render_current_frame()

    def _build_ui(self) -> None:
        """Construct control bar and formula working display."""
        # Top Bar: Stepper Playback Controls
        top_bar = tk.Frame(self, bg="#F8FAFC", padx=16, pady=8)
        top_bar.pack(fill=tk.X, side=tk.TOP)

        # Left: Title and Step Indicator
        left_box = tk.Frame(top_bar, bg="#F8FAFC")
        left_box.pack(side=tk.LEFT)

        tk.Label(
            left_box,
            text="ACTUAL WORKING & CALCULATION",
            font=("Segoe UI", 9, "bold"),
            fg="#0F172A",
            bg="#F8FAFC",
        ).pack(side=tk.LEFT)

        self.lbl_step_counter = tk.Label(
            left_box,
            text="Step 0 / 0",
            font=("Segoe UI", 8, "bold"),
            fg="#1D4ED8",
            bg="#EFF6FF",
            padx=8,
            pady=2,
        )
        self.lbl_step_counter.pack(side=tk.LEFT, padx=(10, 0))

        # Center/Right: Stepper Buttons
        btn_box = tk.Frame(top_bar, bg="#F8FAFC")
        btn_box.pack(side=tk.RIGHT)

        self.btn_reset = tk.Button(
            btn_box,
            text="⏮ Start",
            command=self.jump_to_start,
            font=("Segoe UI", 8, "bold"),
            bg="#FFFFFF",
            fg="#334155",
            relief="flat",
            activebackground="#E2E8F0",
            cursor="hand2",
            padx=8,
            pady=3,
        )
        self.btn_reset.pack(side=tk.LEFT, padx=2)

        self.btn_prev = tk.Button(
            btn_box,
            text="◀ Prev",
            command=self.prev_frame,
            font=("Segoe UI", 8, "bold"),
            bg="#FFFFFF",
            fg="#334155",
            relief="flat",
            activebackground="#E2E8F0",
            cursor="hand2",
            padx=8,
            pady=3,
        )
        self.btn_prev.pack(side=tk.LEFT, padx=2)

        self.btn_play = tk.Button(
            btn_box,
            text="▶ Auto Play",
            command=self.toggle_play,
            font=("Segoe UI", 8, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            relief="flat",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            cursor="hand2",
            padx=12,
            pady=3,
        )
        self.btn_play.pack(side=tk.LEFT, padx=3)

        self.btn_next = tk.Button(
            btn_box,
            text="Next ▶",
            command=self.next_frame,
            font=("Segoe UI", 8, "bold"),
            bg="#FFFFFF",
            fg="#334155",
            relief="flat",
            activebackground="#E2E8F0",
            cursor="hand2",
            padx=8,
            pady=3,
        )
        self.btn_next.pack(side=tk.LEFT, padx=2)

        self.btn_end = tk.Button(
            btn_box,
            text="⏭ End",
            command=self.jump_to_end,
            font=("Segoe UI", 8, "bold"),
            bg="#FFFFFF",
            fg="#334155",
            relief="flat",
            activebackground="#E2E8F0",
            cursor="hand2",
            padx=8,
            pady=3,
        )
        self.btn_end.pack(side=tk.LEFT, padx=2)

        # Speed Dropdown
        tk.Label(
            btn_box,
            text="Speed:",
            font=("Segoe UI", 8),
            fg="#64748B",
            bg="#F8FAFC",
        ).pack(side=tk.LEFT, padx=(8, 2))

        self.speed_var = tk.StringVar(value="Normal (1.1s)")
        speed_menu = ttk.Combobox(
            btn_box,
            textvariable=self.speed_var,
            values=["Fast (0.5s)", "Normal (1.1s)", "Slow (2.0s)"],
            state="readonly",
            width=11,
            font=("Segoe UI", 8),
        )
        speed_menu.pack(side=tk.LEFT, padx=2)
        speed_menu.bind("<<ComboboxSelected>>", self._on_speed_change)

        # Scrubber Slider Bar
        scrubber_bar = tk.Frame(self, bg="#FFFFFF", padx=16, pady=4)
        scrubber_bar.pack(fill=tk.X, side=tk.TOP)

        self.slider = ttk.Scale(
            scrubber_bar,
            from_=0,
            to=1,
            orient=tk.HORIZONTAL,
            command=self._on_slider_scrub,
        )
        self.slider.pack(fill=tk.X)

        # Main Working & Formula Content Box
        self.content_frame = tk.Frame(self, bg="#FFFFFF", padx=16, pady=10)
        self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        # Header Title of the Step
        self.lbl_title = tk.Label(
            self.content_frame,
            text="Step Title",
            font=("Segoe UI", 11, "bold"),
            fg="#0F172A",
            bg="#FFFFFF",
            anchor="w",
        )
        self.lbl_title.pack(fill=tk.X)

        # Explanation sentence
        self.lbl_explanation = tk.Label(
            self.content_frame,
            text="Step explanation goes here.",
            font=("Segoe UI", 9),
            fg="#475569",
            bg="#FFFFFF",
            anchor="w",
            wraplength=1050,
            justify=tk.LEFT,
        )
        self.lbl_explanation.pack(fill=tk.X, pady=(2, 6))

        # Formula & Math Callout Card
        self.math_card = tk.Frame(self.content_frame, bg="#F8FAFC", bd=0, highlightthickness=1, highlightbackground="#E2E8F0", padx=12, pady=8)
        self.math_card.pack(fill=tk.X, pady=(0, 6))

        self.lbl_formula = tk.Label(
            self.math_card,
            text="Formula: dist[u] + weight(u, v)",
            font=("Consolas", 10, "bold"),
            fg="#1E293B",
            bg="#F8FAFC",
            anchor="w",
        )
        self.lbl_formula.pack(fill=tk.X)

        self.lbl_comparison = tk.Label(
            self.math_card,
            text="Comparison & Decision text",
            font=("Segoe UI", 9),
            fg="#334155",
            bg="#F8FAFC",
            anchor="w",
            wraplength=1030,
            justify=tk.LEFT,
        )
        self.lbl_comparison.pack(fill=tk.X, pady=(4, 0))

        # Bottom Bar: Live Sets (Permanent & Temporary)
        sets_bar = tk.Frame(self.content_frame, bg="#FFFFFF")
        sets_bar.pack(fill=tk.X)

        # Permanent List Tag
        perm_box = tk.Frame(sets_bar, bg="#FFFFFF")
        perm_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(
            perm_box,
            text="Permanent (Finalized):",
            font=("Segoe UI", 8, "bold"),
            fg="#047857",
            bg="#FFFFFF",
        ).pack(side=tk.LEFT)

        self.lbl_permanent = tk.Label(
            perm_box,
            text="A(0)",
            font=("Consolas", 8, "bold"),
            fg="#065F46",
            bg="#DCFCE7",
            padx=8,
            pady=2,
        )
        self.lbl_permanent.pack(side=tk.LEFT, padx=(6, 12))

        # Temporary List Tag
        temp_box = tk.Frame(sets_bar, bg="#FFFFFF")
        temp_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(
            temp_box,
            text="Temporary (Tentative):",
            font=("Segoe UI", 8, "bold"),
            fg="#475569",
            bg="#FFFFFF",
        ).pack(side=tk.LEFT)

        self.lbl_temporary = tk.Label(
            temp_box,
            text="B(6), C(2), ...",
            font=("Consolas", 8),
            fg="#1E293B",
            bg="#F1F5F9",
            padx=8,
            pady=2,
        )
        self.lbl_temporary.pack(side=tk.LEFT, padx=(6, 0))

    def _on_speed_change(self, event=None) -> None:
        """Update playback speed interval."""
        val = self.speed_var.get()
        if "Fast" in val:
            self.playback_speed_ms = 500
        elif "Slow" in val:
            self.playback_speed_ms = 2000
        else:
            self.playback_speed_ms = 1100

    def _on_slider_scrub(self, val_str: str) -> None:
        """Handle dragging the progress scrubber."""
        try:
            target_idx = int(float(val_str))
            if 0 <= target_idx < len(self.frames) and target_idx != self.current_frame_idx:
                self.current_frame_idx = target_idx
                self.render_current_frame()
                self.on_frame_change(self.current_frame_idx)
        except Exception:
            pass

    def render_current_frame(self) -> None:
        """Render the details of the active frame in the working card."""
        if not self.frames or self.current_frame_idx >= len(self.frames):
            return

        frame = self.frames[self.current_frame_idx]
        total_frames = len(self.frames)

        # 1. Step Counter
        self.lbl_step_counter.config(text=f"Frame {self.current_frame_idx + 1} of {total_frames}")

        # 2. Update Slider without triggering loop
        self.slider.set(self.current_frame_idx)

        # 3. Step Title
        self.lbl_title.config(text=frame.title)

        # 4. Step Explanation
        self.lbl_explanation.config(text=frame.explanation_text)

        # 5. Formula & Comparison formatting based on status
        if frame.status == "UPDATED":
            card_bg = "#F0FDF4"
            card_border = "#86EFAC"
            formula_fg = "#166534"
        elif frame.status == "UNCHANGED":
            card_bg = "#FFFBEB"
            card_border = "#FDE68A"
            formula_fg = "#92400E"
        elif frame.status == "SKIPPED":
            card_bg = "#F8FAFC"
            card_border = "#CBD5E1"
            formula_fg = "#475569"
        elif frame.status == "PICKED":
            card_bg = "#EFF6FF"
            card_border = "#93C5FD"
            formula_fg = "#1E40AF"
        elif frame.status == "COMPLETE":
            card_bg = "#F5F3FF"
            card_border = "#C4B5FD"
            formula_fg = "#5B21B6"
        else:
            card_bg = "#F8FAFC"
            card_border = "#E2E8F0"
            formula_fg = "#1E293B"

        self.math_card.config(bg=card_bg, highlightbackground=card_border)
        self.lbl_formula.config(text=frame.math_formula, fg=formula_fg, bg=card_bg)
        self.lbl_comparison.config(text=frame.comparison_text, bg=card_bg)

        # 6. Sets Snapshot
        perm_str = ", ".join([f"{n}({format_distance(frame.distances_snapshot.get(n, 0))})" for n in frame.permanent_nodes]) or "Empty (Ø)"
        self.lbl_permanent.config(text=perm_str)

        temp_str = ", ".join([f"{n}({format_distance(d)})" for n, d in frame.temporary_nodes]) or "Empty (Ø)"
        self.lbl_temporary.config(text=temp_str)

    def jump_to_start(self) -> None:
        """Jump to the first initialization frame."""
        self.stop_playback()
        self.current_frame_idx = 0
        self.render_current_frame()
        self.on_frame_change(self.current_frame_idx)

    def jump_to_end(self) -> None:
        """Jump to the final complete frame."""
        self.stop_playback()
        if self.frames:
            self.current_frame_idx = len(self.frames) - 1
            self.render_current_frame()
            self.on_frame_change(self.current_frame_idx)

    def prev_frame(self) -> None:
        """Step back by one frame."""
        self.stop_playback()
        if self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            self.render_current_frame()
            self.on_frame_change(self.current_frame_idx)

    def next_frame(self) -> None:
        """Step forward by one frame."""
        if self.current_frame_idx < len(self.frames) - 1:
            self.current_frame_idx += 1
            self.render_current_frame()
            self.on_frame_change(self.current_frame_idx)
        else:
            self.stop_playback()

    def toggle_play(self) -> None:
        """Toggle auto-play animation."""
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self) -> None:
        """Start auto-stepping through frames."""
        if not self.frames:
            return

        if self.current_frame_idx >= len(self.frames) - 1:
            self.current_frame_idx = 0
            self.render_current_frame()
            self.on_frame_change(self.current_frame_idx)

        self.is_playing = True
        self.btn_play.config(text="⏸ Pause", bg="#DC2626", activebackground="#B91C1C")
        self._schedule_next_step()

    def stop_playback(self) -> None:
        """Pause auto-stepping."""
        self.is_playing = False
        if self._timer_id is not None:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        self.btn_play.config(text="▶ Auto Play", bg="#2563EB", activebackground="#1D4ED8")

    def _schedule_next_step(self) -> None:
        """Schedule the next animation frame tick."""
        if not self.is_playing:
            return

        if self.current_frame_idx < len(self.frames) - 1:
            self.next_frame()
            self._timer_id = self.after(self.playback_speed_ms, self._schedule_next_step)
        else:
            self.stop_playback()
