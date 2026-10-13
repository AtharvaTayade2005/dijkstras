"""
dijkstra.py
-----------
Core Dijkstra Shortest-Path Algorithm implementation with comprehensive,
deterministic event tracing, Temporary/Permanent list state tracking,
granular visual simulation frames, and path reconstruction for network routing.

Independent from UI widgets to facilitate automated headless testing.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from graph import NetworkGraph


def format_distance(val: float) -> str:
    """Helper to format distance numbers cleanly."""
    if math.isinf(val):
        return "∞"
    return str(int(val) if isinstance(val, (int, float)) and float(val).is_integer() else val)


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
        return format_distance(val)

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
        return format_distance(val)

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
class SimulationFrame:
    """
    Granular atomic visual step for interactive step-by-step playback.
    Captures live distances, active node, examined edge, formulas, and decisions.
    """
    frame_index: int
    step_number: int
    phase: str  # "INIT", "PICK_MIN", "EXAMINE_EDGE", "STEP_DONE", "COMPLETE"
    title: str
    current_node: str
    selected_cost: float
    examining_neighbor: Optional[str] = None
    edge_weight: Optional[int] = None
    candidate_dist: Optional[float] = None
    prev_dist: Optional[float] = None
    status: str = "INFO"  # "UPDATED", "UNCHANGED", "SKIPPED", "PICKED", "INIT", "FINALIZED", "COMPLETE"
    explanation_text: str = ""
    math_formula: str = ""
    comparison_text: str = ""
    distances_snapshot: Dict[str, float] = field(default_factory=dict)
    predecessors_snapshot: Dict[str, Optional[str]] = field(default_factory=dict)
    permanent_nodes: List[str] = field(default_factory=list)
    temporary_nodes: List[Tuple[str, float]] = field(default_factory=list)
    active_edge: Optional[Tuple[str, str]] = None
    highlight_path: List[str] = field(default_factory=list)


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
        return format_distance(self.distance)


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
    frames: List[SimulationFrame] = field(default_factory=list)


def reconstruct_path_at(source: str, target: str, preds: Dict[str, Optional[str]]) -> List[str]:
    """Helper to reconstruct the current known shortest path to target."""
    if target == source:
        return [source]
    curr: Optional[str] = target
    path_rev: List[str] = []
    visited_set = set()
    while curr is not None and curr not in visited_set:
        visited_set.add(curr)
        path_rev.append(curr)
        if curr == source:
            break
        curr = preds.get(curr, None)

    rev = list(reversed(path_rev))
    if len(rev) >= 1 and rev[0] == source:
        return rev
    return []


def run_dijkstra(graph: NetworkGraph, source: str) -> DijkstraResult:
    """
    Executes Dijkstra's algorithm from `source` on `graph`.
    
    Generates a full trace of steps with Temporary and Permanent lists,
    tie-breaking, neighbor evaluations, granular simulation frames,
    and complete routing table.
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
    frames: List[SimulationFrame] = []

    # Initial state record before step 1
    initial_temp = [(n, distances[n]) for n in sorted(all_nodes, key=lambda x: (distances[x], x))]

    # Frame 0: Initialization
    frames.append(SimulationFrame(
        frame_index=0,
        step_number=0,
        phase="INIT",
        title=f"Initialization: Source Node '{source}'",
        current_node=source,
        selected_cost=0.0,
        status="INIT",
        explanation_text=(
            f"Algorithm initialized at source Node '{source}'. "
            f"Source distance set to 0. All other node distances set to ∞. All predecessors set to None."
        ),
        math_formula=f"dist[{source}] = 0  |  dist[v] = ∞ for all other nodes v",
        comparison_text="Ready to begin. The algorithm will now find the unfinalized node with the lowest tentative distance.",
        distances_snapshot=distances.copy(),
        predecessors_snapshot=predecessors.copy(),
        permanent_nodes=[],
        temporary_nodes=initial_temp.copy(),
        active_edge=None,
        highlight_path=[source],
    ))

    step_counter = 1

    while unfinalized:
        # 6. Select unfinalized node with lowest tentative distance.
        # Deterministic tie-breaking: (distances[n], n)
        candidates = sorted(list(unfinalized), key=lambda n: (distances[n], n))
        selected_node = candidates[0]
        selected_dist = distances[selected_node]

        # If all remaining unfinalized nodes have infinity distance, they are unreachable
        if math.isinf(selected_dist):
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
                f"({format_distance(selected_dist)}) among all remaining unfinalized nodes."
            )

        step = DijkstraStep(
            step_number=step_counter,
            selected_node=selected_node,
            selected_distance=selected_dist,
            selection_reason=selection_reason,
        )

        # Frame: Pick Min Node
        frames.append(SimulationFrame(
            frame_index=len(frames),
            step_number=step_counter,
            phase="PICK_MIN",
            title=f"Step {step_counter}: Select Node '{selected_node}' (Cost = {format_distance(selected_dist)})",
            current_node=selected_node,
            selected_cost=selected_dist,
            status="PICKED",
            explanation_text=(
                f"Node '{selected_node}' has the smallest tentative distance ({format_distance(selected_dist)}) "
                f"among unfinalized nodes. It is moved to the Permanent List."
            ),
            math_formula=f"u* = argmin {{ dist[v] : v ∉ Permanent }} = '{selected_node}' (cost = {format_distance(selected_dist)})",
            comparison_text=f"Node '{selected_node}' is now locked. Examining all its outgoing edges...",
            distances_snapshot=distances.copy(),
            predecessors_snapshot=predecessors.copy(),
            permanent_nodes=permanent_order.copy(),
            temporary_nodes=[(n, distances[n]) for n in sorted(list(unfinalized), key=lambda x: (distances[x], x))],
            active_edge=None,
            highlight_path=reconstruct_path_at(source, selected_node, predecessors),
        ))

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
                    reason=f"Node {neighbor} is already in the Permanent List with finalized distance {format_distance(curr_dist)}.",
                    predecessor_before=predecessors[neighbor],
                    predecessor_after=predecessors[neighbor],
                    already_finalized=True,
                )
                step.neighbor_evaluations.append(eval_record)

                # Frame: Skipped neighbor
                frames.append(SimulationFrame(
                    frame_index=len(frames),
                    step_number=step_counter,
                    phase="EXAMINE_EDGE",
                    title=f"Step {step_counter}: Edge {selected_node} — {neighbor} (wt {edge_w})",
                    current_node=selected_node,
                    selected_cost=selected_dist,
                    examining_neighbor=neighbor,
                    edge_weight=edge_w,
                    candidate_dist=cand_dist,
                    prev_dist=curr_dist,
                    status="SKIPPED",
                    explanation_text=(
                        f"Neighbor Node '{neighbor}' is already in the Permanent List with finalized distance {format_distance(curr_dist)}. "
                        f"Skipping edge {selected_node} — {neighbor}."
                    ),
                    math_formula=f"'{neighbor}' ∈ Permanent List  ➔  Optimal shortest path already finalized",
                    comparison_text="No update performed because finalized nodes cannot have their distances improved.",
                    distances_snapshot=distances.copy(),
                    predecessors_snapshot=predecessors.copy(),
                    permanent_nodes=permanent_order.copy(),
                    temporary_nodes=[(n, distances[n]) for n in sorted(list(unfinalized), key=lambda x: (distances[x], x))],
                    active_edge=(selected_node, neighbor),
                    highlight_path=reconstruct_path_at(source, neighbor, predecessors),
                ))
                continue

            # 10 & 11. Compare candidate distance with neighbor's tentative distance
            if cand_dist < curr_dist:
                old_pred = predecessors[neighbor]
                old_dist = curr_dist
                distances[neighbor] = cand_dist
                predecessors[neighbor] = selected_node
                
                eval_record = NeighborEvaluation(
                    neighbor=neighbor,
                    edge_weight=edge_w,
                    current_known_distance=old_dist,
                    candidate_distance=cand_dist,
                    is_updated=True,
                    status_summary="Updated",
                    reason=(
                        f"Candidate distance ({cand_dist}) < previous distance ({format_distance(old_dist)}). "
                        f"Updated distance to {cand_dist} and set predecessor to '{selected_node}'."
                    ),
                    predecessor_before=old_pred,
                    predecessor_after=selected_node,
                    already_finalized=False,
                )

                # Frame: Updated neighbor
                frames.append(SimulationFrame(
                    frame_index=len(frames),
                    step_number=step_counter,
                    phase="EXAMINE_EDGE",
                    title=f"Step {step_counter}: Relax Edge {selected_node} — {neighbor} (wt {edge_w})",
                    current_node=selected_node,
                    selected_cost=selected_dist,
                    examining_neighbor=neighbor,
                    edge_weight=edge_w,
                    candidate_dist=cand_dist,
                    prev_dist=old_dist,
                    status="UPDATED",
                    explanation_text=(
                        f"Shorter route discovered to Node '{neighbor}' via '{selected_node}'! "
                        f"Candidate distance ({cand_dist}) < Previous tentative distance ({format_distance(old_dist)})."
                    ),
                    math_formula=f"Candidate = dist[{selected_node}] ({format_distance(selected_dist)}) + weight({selected_node}, {neighbor}) ({edge_w}) = {cand_dist}",
                    comparison_text=(
                        f"Decision: {cand_dist} < {format_distance(old_dist)}  ➔  "
                        f"UPDATED! dist[{neighbor}] becomes {cand_dist}, pred[{neighbor}] = '{selected_node}' (was {old_pred or 'None'})."
                    ),
                    distances_snapshot=distances.copy(),
                    predecessors_snapshot=predecessors.copy(),
                    permanent_nodes=permanent_order.copy(),
                    temporary_nodes=[(n, distances[n]) for n in sorted(list(unfinalized), key=lambda x: (distances[x], x))],
                    active_edge=(selected_node, neighbor),
                    highlight_path=reconstruct_path_at(source, neighbor, predecessors),
                ))
            else:
                eval_record = NeighborEvaluation(
                    neighbor=neighbor,
                    edge_weight=edge_w,
                    current_known_distance=curr_dist,
                    candidate_distance=cand_dist,
                    is_updated=False,
                    status_summary="Unchanged",
                    reason=(
                        f"Candidate distance ({cand_dist}) ≥ current distance ({format_distance(curr_dist)}). "
                        f"Tentative distance kept at {format_distance(curr_dist)}."
                    ),
                    predecessor_before=predecessors[neighbor],
                    predecessor_after=predecessors[neighbor],
                    already_finalized=False,
                )

                # Frame: Unchanged neighbor
                frames.append(SimulationFrame(
                    frame_index=len(frames),
                    step_number=step_counter,
                    phase="EXAMINE_EDGE",
                    title=f"Step {step_counter}: Inspect Edge {selected_node} — {neighbor} (wt {edge_w})",
                    current_node=selected_node,
                    selected_cost=selected_dist,
                    examining_neighbor=neighbor,
                    edge_weight=edge_w,
                    candidate_dist=cand_dist,
                    prev_dist=curr_dist,
                    status="UNCHANGED",
                    explanation_text=(
                        f"Alternative route to Node '{neighbor}' via '{selected_node}' costs {cand_dist}, "
                        f"which is not better than the current known distance of {format_distance(curr_dist)}."
                    ),
                    math_formula=f"Candidate = dist[{selected_node}] ({format_distance(selected_dist)}) + weight({selected_node}, {neighbor}) ({edge_w}) = {cand_dist}",
                    comparison_text=(
                        f"Decision: {cand_dist} ≥ {format_distance(curr_dist)}  ➔  "
                        f"UNCHANGED. Kept current distance {format_distance(curr_dist)} and predecessor '{predecessors[neighbor] or 'None'}'."
                    ),
                    distances_snapshot=distances.copy(),
                    predecessors_snapshot=predecessors.copy(),
                    permanent_nodes=permanent_order.copy(),
                    temporary_nodes=[(n, distances[n]) for n in sorted(list(unfinalized), key=lambda x: (distances[x], x))],
                    active_edge=(selected_node, neighbor),
                    highlight_path=reconstruct_path_at(source, neighbor, predecessors),
                ))

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

        # Frame: Step Completed
        frames.append(SimulationFrame(
            frame_index=len(frames),
            step_number=step_counter,
            phase="STEP_DONE",
            title=f"Step {step_counter} Complete: Node '{selected_node}' Fully Finalized",
            current_node=selected_node,
            selected_cost=selected_dist,
            status="FINALIZED",
            explanation_text=(
                f"All adjacent edges of Node '{selected_node}' have been examined. "
                f"Its distance {format_distance(selected_dist)} is permanently finalized."
            ),
            math_formula=f"dist[{selected_node}] = {format_distance(selected_dist)} (Permanently Finalized)",
            comparison_text=(
                f"Permanent: {step.perm_list_str()}  |  Temporary: {step.temp_list_str()}"
            ),
            distances_snapshot=distances.copy(),
            predecessors_snapshot=predecessors.copy(),
            permanent_nodes=permanent_order.copy(),
            temporary_nodes=step.temporary_list.copy(),
            active_edge=None,
            highlight_path=reconstruct_path_at(source, selected_node, predecessors),
        ))

        steps.append(step)
        step_counter += 1

    # Final Frame: All Complete
    frames.append(SimulationFrame(
        frame_index=len(frames),
        step_number=step_counter - 1,
        phase="COMPLETE",
        title="Algorithm Complete: All Shortest Paths Found",
        current_node=source,
        selected_cost=0.0,
        status="COMPLETE",
        explanation_text=(
            f"All reachable nodes from source Node '{source}' have been finalized. "
            f"The shortest path and minimum cost to every node in the network are established."
        ),
        math_formula="Optimal Shortest Path Tree (SPT) is complete for all destinations.",
        comparison_text="All destinations locked. See final live routing table.",
        distances_snapshot=distances.copy(),
        predecessors_snapshot=predecessors.copy(),
        permanent_nodes=permanent_order.copy(),
        temporary_nodes=[],
        active_edge=None,
        highlight_path=[],
    ))

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
            path = reconstruct_path_at(source, dest, predecessors)
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
        frames=frames,
    )
