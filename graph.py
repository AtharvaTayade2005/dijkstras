"""
graph.py
--------
Graph topology and representation for the Dijkstra Network Explorer.
Represents an undirected, weighted network with 6 nodes (A, B, C, D, E, F)
and normalized visual coordinates for responsive canvas rendering.
"""

from typing import Dict, List, Tuple, Optional


class NetworkGraph:
    """Represents a weighted, undirected network graph."""

    def __init__(self):
        # Default 6 nodes
        self.nodes: List[str] = ["A", "B", "C", "D", "E", "F"]

        # Normalized coordinates (nx, ny) in [0.0, 1.0] for balanced visual layout
        # Allows responsive scaling to any canvas size without distortion.
        self.node_positions: Dict[str, Tuple[float, float]] = {
            "A": (0.16, 0.32),
            "B": (0.54, 0.16),
            "C": (0.42, 0.48),
            "D": (0.18, 0.78),
            "E": (0.84, 0.38),
            "F": (0.68, 0.80),
        }

        # Undirected edge specifications: (node1, node2, weight)
        # Matches the network specification:
        # A - B: 6 | A - C: 2 | A - D: 4
        # B - C: 3 | B - E: 5 | B - F: 9
        # C - D: 1 | C - E: 8 | C - F: 7
        # D - F: 7 | E - F: 2
        self.raw_edges: List[Tuple[str, str, int]] = [
            ("A", "B", 6),
            ("A", "C", 2),
            ("A", "D", 4),
            ("B", "C", 3),
            ("B", "E", 5),
            ("B", "F", 9),
            ("C", "D", 1),
            ("C", "E", 8),
            ("C", "F", 7),
            ("D", "F", 7),
            ("E", "F", 2),
        ]

        # Adjacency list: node -> {neighbor: weight}
        self.adjacency: Dict[str, Dict[str, int]] = {n: {} for n in self.nodes}
        self._build_adjacency()

    def _build_adjacency(self) -> None:
        """Populate symmetric adjacency mapping."""
        for u, v, w in self.raw_edges:
            self.adjacency[u][v] = w
            self.adjacency[v][u] = w

    def get_neighbors(self, node: str) -> Dict[str, int]:
        """Return dict of {neighbor: weight} for a node."""
        return self.adjacency.get(node, {}).copy()

    def get_edge_weight(self, u: str, v: str) -> Optional[int]:
        """Return weight between u and v, or None if no edge."""
        return self.adjacency.get(u, {}).get(v, None)

    def get_all_edges(self) -> List[Tuple[str, str, int]]:
        """Return all unique undirected edges."""
        return list(self.raw_edges)

    def num_nodes(self) -> int:
        return len(self.nodes)

    def num_edges(self) -> int:
        return len(self.raw_edges)


def get_default_graph() -> NetworkGraph:
    """Factory function returning the standard 6-node network graph."""
    return NetworkGraph()
