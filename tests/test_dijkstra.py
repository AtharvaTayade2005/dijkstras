"""
tests/test_dijkstra.py
----------------------
Automated test suite verifying the correctness of the Dijkstra algorithm,
graph topology, path reconstruction, and trace generation across all 6 source nodes.
"""

import math
import unittest
from graph import NetworkGraph, get_default_graph
from dijkstra import run_dijkstra, DijkstraResult


class TestDijkstraExplorer(unittest.TestCase):

    def setUp(self):
        self.graph = get_default_graph()

    def test_graph_topology(self):
        """Verify the graph has exactly 6 nodes and 11 edges matching specification."""
        self.assertEqual(len(self.graph.nodes), 6)
        self.assertEqual(set(self.graph.nodes), {"A", "B", "C", "D", "E", "F"})
        self.assertEqual(self.graph.num_edges(), 11)

        # Check expected edges and weights
        expected_weights = {
            ("A", "B"): 6,
            ("A", "C"): 2,
            ("A", "D"): 4,
            ("B", "C"): 3,
            ("B", "E"): 5,
            ("B", "F"): 9,
            ("C", "D"): 1,
            ("C", "E"): 8,
            ("C", "F"): 7,
            ("D", "F"): 7,
            ("E", "F"): 2,
        }
        for (u, v), w in expected_weights.items():
            self.assertEqual(self.graph.get_edge_weight(u, v), w, f"Edge ({u}, {v}) weight mismatch")
            self.assertEqual(self.graph.get_edge_weight(v, u), w, f"Edge ({v}, {u}) symmetric mismatch")

    def test_all_sources_execution(self):
        """Verify Dijkstra runs successfully for every single node in the network."""
        for src in self.graph.nodes:
            result = run_dijkstra(self.graph, src)
            self.assertIsInstance(result, DijkstraResult)
            self.assertEqual(result.source, src)
            # Source to self distance must always be 0
            self.assertEqual(result.distances[src], 0.0)
            self.assertEqual(result.routing_table[src].distance, 0.0)
            self.assertEqual(result.routing_table[src].next_hop, "-")
            self.assertEqual(result.routing_table[src].path, [src])

    def test_path_weight_sums(self):
        """Verify that edge weights along every reconstructed path sum to total distance."""
        for src in self.graph.nodes:
            result = run_dijkstra(self.graph, src)
            for dest, entry in result.routing_table.items():
                if dest == src:
                    self.assertEqual(entry.distance, 0.0)
                    self.assertEqual(entry.path, [src])
                    continue

                path = entry.path
                self.assertGreaterEqual(len(path), 2, f"Path from {src} to {dest} too short: {path}")
                self.assertEqual(path[0], src)
                self.assertEqual(path[-1], dest)
                self.assertEqual(entry.next_hop, path[1])

                # Sum edge weights along the path
                path_sum = 0
                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    weight = self.graph.get_edge_weight(u, v)
                    self.assertIsNotNone(weight, f"Edge ({u}, {v}) does not exist in graph")
                    path_sum += weight

                self.assertEqual(path_sum, entry.distance, f"Path sum mismatch from {src} to {dest}")

    def test_source_a_known_distances(self):
        """Verify expected shortest distances from Node A."""
        result = run_dijkstra(self.graph, "A")
        # Direct & alternative paths from A:
        # A: 0
        # C: 2 (A->C)
        # D: 3 (A->C->D: 2+1=3 < A->D: 4)
        # B: 5 (A->C->B: 2+3=5 < A->B: 6)
        # F: 9 (A->C->F: 2+7=9 or A->C->D->F: 2+1+7=10)
        # E: 10 (A->C->E: 2+8=10, or A->C->B->E: 2+3+5=10)
        self.assertEqual(result.distances["A"], 0)
        self.assertEqual(result.distances["C"], 2)
        self.assertEqual(result.distances["D"], 3)
        self.assertEqual(result.distances["B"], 5)
        self.assertEqual(result.distances["F"], 9)
        self.assertEqual(result.distances["E"], 10)

        # Check next hops from A
        self.assertEqual(result.routing_table["B"].next_hop, "C")
        self.assertEqual(result.routing_table["C"].next_hop, "C")
        self.assertEqual(result.routing_table["D"].next_hop, "C")
        self.assertEqual(result.routing_table["E"].next_hop, "C")
        self.assertEqual(result.routing_table["F"].next_hop, "C")

    def test_source_b_known_distances(self):
        """Verify expected shortest distances from Node B."""
        result = run_dijkstra(self.graph, "B")
        # From B:
        # B: 0
        # C: 3 (B->C)
        # D: 4 (B->C->D: 3+1=4)
        # A: 5 (B->C->A: 3+2=5 < B->A: 6)
        # E: 5 (B->E: 5)
        # F: 7 (B->E->F: 5+2=7 < B->F: 9)
        self.assertEqual(result.distances["B"], 0)
        self.assertEqual(result.distances["C"], 3)
        self.assertEqual(result.distances["D"], 4)
        self.assertEqual(result.distances["A"], 5)
        self.assertEqual(result.distances["E"], 5)
        self.assertEqual(result.distances["F"], 7)

        self.assertEqual(result.routing_table["F"].next_hop, "E")
        self.assertEqual(result.routing_table["F"].path, ["B", "E", "F"])

    def test_source_f_known_distances(self):
        """Verify expected shortest distances from Node F."""
        result = run_dijkstra(self.graph, "F")
        # F: 0
        # E: 2 (F->E)
        # B: 7 (F->E->B: 2+5=7 < F->B: 9)
        # D: 7 (F->D: 7)
        # C: 7 (F->C: 7)
        # A: 9 (F->C->A: 7+2=9 or F->D->A: 7+4=11)
        self.assertEqual(result.distances["F"], 0)
        self.assertEqual(result.distances["E"], 2)
        self.assertEqual(result.distances["B"], 7)
        self.assertEqual(result.distances["D"], 7)
        self.assertEqual(result.distances["C"], 7)
        self.assertEqual(result.distances["A"], 9)

    def test_steps_temporary_and_permanent_lists(self):
        """Verify that Permanent List grows monotonically and Temporary List shrinks."""
        result = run_dijkstra(self.graph, "A")
        self.assertEqual(len(result.steps), 6)

        visited_nodes = []
        for i, step in enumerate(result.steps):
            self.assertEqual(step.step_number, i + 1)
            visited_nodes.append(step.selected_node)
            # Permanent list has length i + 1
            self.assertEqual(len(step.permanent_list), i + 1)
            # Temporary list has length 6 - (i + 1)
            self.assertEqual(len(step.temporary_list), 6 - (i + 1))
            # No duplicate nodes finalized
            self.assertEqual(len(visited_nodes), len(set(visited_nodes)))

        # Final step: Temporary list is empty, permanent list contains all 6 nodes
        self.assertEqual(len(result.steps[-1].temporary_list), 0)
        self.assertEqual(len(result.steps[-1].permanent_list), 6)

    def test_disconnected_graph_handling(self):
        """Verify algorithm handles unreachable nodes gracefully."""
        graph = NetworkGraph()
        # Add an isolated node G
        graph.nodes.append("G")
        graph.adjacency["G"] = {}

        result = run_dijkstra(graph, "A")
        self.assertTrue(math.isinf(result.distances["G"]))
        self.assertEqual(result.routing_table["G"].distance_display, "∞")
        self.assertEqual(result.routing_table["G"].next_hop, "-")
        self.assertEqual(result.routing_table["G"].path_str, "Unreachable")

    def test_simulation_frames(self):
        """Verify that simulation frames correctly capture every calculation step and formula."""
        for src in self.graph.nodes:
            result = run_dijkstra(self.graph, src)
            self.assertGreater(len(result.frames), 10)

            # Frame 0 is initialization
            f0 = result.frames[0]
            self.assertEqual(f0.phase, "INIT")
            self.assertEqual(f0.current_node, src)
            self.assertEqual(f0.distances_snapshot[src], 0.0)

            # Check that every EXAMINE_EDGE frame has valid math calculations
            for frame in result.frames:
                if frame.phase == "EXAMINE_EDGE":
                    self.assertIsNotNone(frame.examining_neighbor)
                    self.assertIsNotNone(frame.edge_weight)
                    self.assertIsNotNone(frame.candidate_dist)
                    expected_cand = frame.selected_cost + frame.edge_weight
                    self.assertEqual(frame.candidate_dist, expected_cand)
                    self.assertIn(frame.status, ["UPDATED", "UNCHANGED", "SKIPPED"])
                    self.assertTrue(len(frame.math_formula) > 0)

            # Last frame is complete
            f_last = result.frames[-1]
            self.assertEqual(f_last.phase, "COMPLETE")
            self.assertEqual(len(f_last.permanent_nodes), len(self.graph.nodes))


if __name__ == "__main__":
    unittest.main()
