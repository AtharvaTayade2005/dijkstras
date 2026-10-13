"""
dijkstra.py
-----------
Core Dijkstra Shortest-Path Algorithm implementation with comprehensive,
deterministic event tracing, Temporary/Permanent list state tracking,
and path reconstruction for network routing.

Independent from UI widgets to facilitate automated headless testing.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from graph import NetworkGraph


@dataclass
class NeighborEvaluation:
    """Detailed record of examining a single adjacent neighbor."""
    neighbor: str
    edge_weight: int
    current_known_distance: float
    candidate_distance: float
    is_updated: bool
    status_summary: str
    reason: str
    predecessor_before: Optional[str]
    predecessor_after: Optional[str]
    already_finalized: bool = False

    def format_distance(self, val: float) -> str:
        return "∞" if math.isinf(val) else str(int(val) if val.is_integer() else val)

    def detailed_text(self) -> str:
        curr_str = self.format_distance(self.current_known_distance)
        cand_str = self.format_distance(self.candidate_distance)
        
        lines = [
            f"• Neighbor {self.neighbor}:",
            f"   - Edge weight: {self.edge_weight}",
            f"   - Current known distance: {curr_str}",
            f"   - Candidate distance: {cand_str}",
        ]
        if self.already_finalized:
            lines.append("   - Status: Skipped (Already in Permanent List)")
        elif self.is_updated:
            pred_prev = self.predecessor_before or "None"
            lines.append(f"   - Status: UPDATED (Candidate {cand_str} < Current {curr_str})")
            lines.append(f"   - Predecessor: {pred_prev} → {self.predecessor_after}")
        else:
            lines.append(f"   - Status: UNCHANGED (Candidate {cand_str} ≥ Current {curr_str})")
            lines.append(f"   - Predecessor remained: {self.predecessor_after or 'None'}")
        return "\n".join(lines)


@dataclass
class DijkstraStep:
    """Represents a single iteration of Dijkstra's algorithm."""
    step_number: int
    selected_node: str
    selected_distance: float
    selection_reason: str
    neighbor_evaluations: List[NeighborEvaluation] = field(default_factory=list)
    # Snapshots after the iteration:
    temporary_list: List[Tuple[str, float]] = field(default_factory=list)
    permanent_list: List[Tuple[str, float]] = field(default_factory=list)

    @staticmethod
    def format_dist(val: float) -> str:
        return "∞" if math.isinf(val) else str(int(val) if isinstance(val, (int, float)) and float(val).is_integer() else val)

    def temp_list_str(self) -> str:
        if not self.temporary_list:
            return "Empty (Ø)"
        items = [f"{n}({self.format_dist(d)})" for n, d in self.temporary_list]
        return ", ".join(items)

    def perm_list_str(self) -> str:
        if not self.permanent_list:
            return "Empty (Ø)"
        items = [f"{n}({self.format_dist(d)})" for n, d in self.permanent_list]
        return ", ".join(items)


@dataclass
class RoutingEntry:
    """Row in the final routing table for a destination."""
    destination: str
    distance: float
    next_hop: str
    path: List[str]
    path_str: str

    @property
    def distance_display(self) -> str:
        return "∞" if math.isinf(self.distance) else str(int(self.distance) if self.distance.is_integer() else self.distance)


@dataclass
class DijkstraResult:
    """Full execution output of Dijkstra's algorithm from a chosen source."""
    source: str
    distances: Dict[str, float]
    predecessors: Dict[str, Optional[str]]
    routing_table: Dict[str, RoutingEntry]
    steps: List[DijkstraStep]
    initial_temp_list: List[Tuple[str, float]]
    final_perm_list: List[Tuple[str, float]]


def run_dijkstra(graph: NetworkGraph, source: str) -> DijkstraResult:
    """
    Executes Dijkstra's algorithm from `source` on `graph`.
    
    Generates a full trace of steps with Temporary and Permanent lists,
    tie-breaking, neighbor evaluations, and complete routing table.
    """
    if source not in graph.nodes:
        raise ValueError(f"Source node '{source}' not in graph.")

    all_nodes = sorted(graph.nodes)
    
    # 1. Initialize distances and predecessors
    distances: Dict[str, float] = {node: float("inf") for node in all_nodes}
    distances[source] = 0.0

    predecessors: Dict[str, Optional[str]] = {node: None for node in all_nodes}

    # Unfinalized nodes set (Temporary List)
    unfinalized = set(all_nodes)
    # Finalized nodes order (Permanent List)
    permanent_order: List[str] = []

    steps: List[DijkstraStep] = []

    # Initial state record before step 1
    initial_temp = [(n, distances[n]) for n in sorted(all_nodes, key=lambda x: (distances[x], x))]

    step_counter = 1

    while unfinalized:
        # 6. Select unfinalized node with lowest tentative distance.
        # Deterministic tie-breaking: (distances[n], n)
        candidates = sorted(list(unfinalized), key=lambda n: (distances[n], n))
        selected_node = candidates[0]
        selected_dist = distances[selected_node]

        # If all remaining unfinalized nodes have infinity distance, they are unreachable
        if math.isinf(selected_dist):
            # Finalize remaining as unreachable
            for unreachable_node in candidates:
                permanent_order.append(unreachable_node)
                unfinalized.remove(unreachable_node)
            break

        # 7. Move selected node to Permanent List
        unfinalized.remove(selected_node)
        permanent_order.append(selected_node)

        # Build step explanation
        if step_counter == 1:
            selection_reason = (
                f"Selected source node '{selected_node}' initialized with tentative distance 0. "
                f"All other nodes initialized to ∞."
            )
        else:
            selection_reason = (
                f"Selected node '{selected_node}' because it has the minimum tentative distance "
                f"({int(selected_dist) if selected_dist.is_integer() else selected_dist}) "
                f"among all remaining unfinalized nodes."
            )

        step = DijkstraStep(
            step_number=step_counter,
            selected_node=selected_node,
            selected_distance=selected_dist,
            selection_reason=selection_reason,
        )

        # 8. Examine adjacent neighbors in deterministic alphabetical order
        neighbors = graph.get_neighbors(selected_node)
        for neighbor in sorted(neighbors.keys()):
            edge_w = neighbors[neighbor]
            curr_dist = distances[neighbor]
            cand_dist = selected_dist + edge_w
            already_perm = neighbor in permanent_order

            if already_perm:
                eval_record = NeighborEvaluation(
                    neighbor=neighbor,
                    edge_weight=edge_w,
                    current_known_distance=curr_dist,
                    candidate_distance=cand_dist,
                    is_updated=False,
                    status_summary="Already Finalized",
                    reason=f"Node {neighbor} is already in the Permanent List with finalized distance {int(curr_dist) if curr_dist.is_integer() else curr_dist}.",
                    predecessor_before=predecessors[neighbor],
                    predecessor_after=predecessors[neighbor],
                    already_finalized=True,
                )
                step.neighbor_evaluations.append(eval_record)
                continue

            # 10 & 11. Compare candidate distance with neighbor's tentative distance
            if cand_dist < curr_dist:
                old_pred = predecessors[neighbor]
                distances[neighbor] = cand_dist
                predecessors[neighbor] = selected_node
                
                eval_record = NeighborEvaluation(
                    neighbor=neighbor,
                    edge_weight=edge_w,
                    current_known_distance=curr_dist,
                    candidate_distance=cand_dist,
                    is_updated=True,
                    status_summary="Updated",
                    reason=(
                        f"Candidate distance ({cand_dist}) < previous distance ({'∞' if math.isinf(curr_dist) else curr_dist}). "
                        f"Updated distance to {cand_dist} and set predecessor to '{selected_node}'."
                    ),
                    predecessor_before=old_pred,
                    predecessor_after=selected_node,
                    already_finalized=False,
                )
            else:
                eval_record = NeighborEvaluation(
                    neighbor=neighbor,
                    edge_weight=edge_w,
                    current_known_distance=curr_dist,
                    candidate_distance=cand_dist,
                    is_updated=False,
                    status_summary="Unchanged",
                    reason=(
                        f"Candidate distance ({cand_dist}) ≥ current distance ({curr_dist}). "
                        f"Tentative distance kept at {curr_dist}."
                    ),
                    predecessor_before=predecessors[neighbor],
                    predecessor_after=predecessors[neighbor],
                    already_finalized=False,
                )

            step.neighbor_evaluations.append(eval_record)

        # Snapshot Temporary List (sorted by tentative distance, then name)
        step.temporary_list = [
            (n, distances[n])
            for n in sorted(list(unfinalized), key=lambda x: (distances[x], x))
        ]

        # Snapshot Permanent List (in order of finalization)
        step.permanent_list = [
            (n, distances[n]) for n in permanent_order
        ]

        steps.append(step)
        step_counter += 1

    # 14. Build final routing table & path reconstruction
    routing_table: Dict[str, RoutingEntry] = {}
    for dest in all_nodes:
        dist = distances[dest]
        if math.isinf(dist):
            routing_table[dest] = RoutingEntry(
                destination=dest,
                distance=float("inf"),
                next_hop="-",
                path=[],
                path_str="Unreachable",
            )
        elif dest == source:
            routing_table[dest] = RoutingEntry(
                destination=dest,
                distance=0.0,
                next_hop="-",
                path=[source],
                path_str=source,
            )
        else:
            # Reconstruct path backwards from dest to source
            path_rev: List[str] = []
            curr: Optional[str] = dest
            while curr is not None:
                path_rev.append(curr)
                if curr == source:
                    break
                curr = predecessors[curr]

            path = list(reversed(path_rev))
            if len(path) >= 2 and path[0] == source:
                next_hop = path[1]
                path_str = " → ".join(path)
            else:
                next_hop = "-"
                path_str = "-"

            routing_table[dest] = RoutingEntry(
                destination=dest,
                distance=dist,
                next_hop=next_hop,
                path=path,
                path_str=path_str,
            )

    final_perm = [(n, distances[n]) for n in permanent_order]

    return DijkstraResult(
        source=source,
        distances=distances,
        predecessors=predecessors,
        routing_table=routing_table,
        steps=steps,
        initial_temp_list=initial_temp,
        final_perm_list=final_perm,
    )
