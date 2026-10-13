"""
tests/test_gui.py
-----------------
Automated test suite verifying the GUI components, event handling,
source node transitions, routing table rendering, and explanation window synchronization.
Runs without blocking using Tkinter event processing.
"""

import unittest
import tkinter as tk
from graph import get_default_graph
from dijkstra import run_dijkstra
from gui_main import DijkstraExplorerApp
from gui_explanation import ExplanationWindow


class TestDijkstraGUI(unittest.TestCase):

    def setUp(self):
        try:
            self.app = DijkstraExplorerApp()
            self.app.withdraw()  # Hide window during test execution
        except tk.TclError as e:
            self.skipTest(f"Tkinter display not available in environment: {e}")

    def tearDown(self):
        if hasattr(self, "app") and self.app:
            try:
                if self.app.explanation_window and self.app.explanation_window.winfo_exists():
                    self.app.explanation_window.destroy()
                self.app.destroy()
            except Exception:
                pass

    def test_initial_state(self):
        """Verify initial default source is 'A' and all UI cards/tables are initialized."""
        self.app.update_idletasks()
        self.assertEqual(self.app.current_source, "A")
        self.assertIsNotNone(self.app.current_result)
        self.assertEqual(self.app.card_source.cget("text"), "Node A")

        # Verify all 6 rows in routing table
        children = self.app.table_view.tree.get_children()
        self.assertEqual(len(children), 6)
        self.assertEqual(set(children), {"A", "B", "C", "D", "E", "F"})

    def test_switching_all_source_nodes(self):
        """Verify that cycling through all 6 sources updates results and table accurately."""
        for node in ["A", "B", "C", "D", "E", "F"]:
            self.app.set_source(node)
            self.app.update_idletasks()
            self.assertEqual(self.app.current_source, node)
            self.assertEqual(self.app.current_result.source, node)
            self.assertEqual(self.app.card_source.cget("text"), f"Node {node}")

            # Routing table source row verification
            item_vals = self.app.table_view.tree.item(node)["values"]
            self.assertIn("Source", str(item_vals[0]))
            self.assertEqual(str(item_vals[1]), "0")
            self.assertEqual(str(item_vals[2]), "-")

    def test_explanation_window_live_synchronization(self):
        """Verify opening explanation window and live synchronization when source changes."""
        self.app.set_source("A")
        self.app.update_idletasks()

        # Open explanation window
        self.app.open_explanation_window()
        self.app.update_idletasks()

        self.assertIsNotNone(self.app.explanation_window)
        self.assertTrue(self.app.explanation_window.winfo_exists())
        self.assertIn("Node A", self.app.explanation_window.title())

        # Switch to Node C while window is open
        self.app.set_source("C")
        self.app.update_idletasks()

        # Explanation window should have updated its title and result immediately
        self.assertEqual(self.app.explanation_window.result.source, "C")
        self.assertIn("Node C", self.app.explanation_window.title())

        # Switch to Node F
        self.app.set_source("F")
        self.app.update_idletasks()
        self.assertEqual(self.app.explanation_window.result.source, "F")
        self.assertIn("Node F", self.app.explanation_window.title())

    def test_path_highlight_request(self):
        """Verify selecting a destination row triggers path highlighting on the canvas."""
        self.app.set_source("B")
        self.app.update_idletasks()

        # Path from B to F is B -> E -> F
        path_bf = self.app.current_result.routing_table["F"].path
        self.assertEqual(path_bf, ["B", "E", "F"])

        self.app._on_path_highlight_requested(path_bf)
        self.app.update_idletasks()
        self.assertEqual(self.app.canvas_view.highlighted_path, ["B", "E", "F"])

    def test_canvas_resize_and_click_detection(self):
        """Verify canvas scales node positions on resize and accurately detects clicks."""
        self.app.geometry("1400x900")
        self.app.update_idletasks()
        self.app.canvas_view.redraw()

        # Check that pixel coordinates exist for all 6 nodes
        self.assertEqual(len(self.app.canvas_view.node_coords), 6)

        # Simulate click on Node D's detected coordinate
        d_x, d_y = self.app.canvas_view.node_coords["D"]
        detected_node = self.app.canvas_view._get_node_at(d_x, d_y)
        self.assertEqual(detected_node, "D")

        # Simulate click event callback directly
        class MockEvent:
            x = int(d_x)
            y = int(d_y)

        self.app.canvas_view._on_click(MockEvent())
        self.app.update_idletasks()
        self.assertEqual(self.app.current_source, "D")

    def test_working_panel_stepper_controls(self):
        """Verify that stepper playback controls advance frames and update canvas tags."""
        self.app.set_source("A")
        self.app.update_idletasks()

        panel = self.app.working_panel
        total_frames = len(self.app.current_result.frames)
        self.assertGreater(total_frames, 10)

        # Initial frame
        self.assertEqual(panel.current_frame_idx, 0)
        self.assertEqual(self.app.canvas_view.current_distances["A"], 0.0)

        # Step forward
        panel.next_frame()
        self.app.update_idletasks()
        self.assertEqual(panel.current_frame_idx, 1)

        # Step back
        panel.prev_frame()
        self.app.update_idletasks()
        self.assertEqual(panel.current_frame_idx, 0)

        # Jump to end
        panel.jump_to_end()
        self.app.update_idletasks()
        self.assertEqual(panel.current_frame_idx, total_frames - 1)
        self.assertEqual(self.app.canvas_view.current_distances["A"], 0.0)
        self.assertEqual(self.app.canvas_view.current_distances["C"], 2.0)
        self.assertEqual(self.app.canvas_view.current_distances["D"], 3.0)


if __name__ == "__main__":
    unittest.main()
