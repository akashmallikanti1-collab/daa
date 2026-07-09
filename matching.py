"""
Matching Module – RideShareVCE (Enhanced)
Algorithms used:
  1. Dijkstra's Algorithm  – finds shortest weighted path between two areas
  2. BFS Sub-path Check    – checks if requester's route is a sub-path of giver's route
  3. Greedy Best Match     – selects highest-overlap candidate
"""

import heapq
from collections import deque
from areas import AREAS, GRAPH, get_route_areas, haversine


# ─────────────────────────────────────────────
# 1. DIJKSTRA'S SHORTEST PATH ALGORITHM
# ─────────────────────────────────────────────

def dijkstra(source, target):
    """
    Dijkstra's algorithm on the GRAPH adjacency dict.
    Returns (total_distance, path_list, steps_log) where steps_log is a
    list of dicts describing each relaxation step (for visualization).
    """
    dist = {node: float('inf') for node in GRAPH}
    dist[source] = 0
    prev = {node: None for node in GRAPH}
    visited = set()
    pq = [(0, source)]      # (cost, node)
    steps = []              # visualization log

    while pq:
        cost, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)

        step = {
            "visiting": u,
            "cost": round(cost, 2),
            "visited": list(visited),
            "distances": {k: (round(v, 2) if v != float('inf') else "∞") for k, v in dist.items()},
        }
        steps.append(step)

        if u == target:
            break

        for neighbor, weight in GRAPH.get(u, {}).items():
            if neighbor in visited:
                continue
            new_cost = cost + weight
            if new_cost < dist[neighbor]:
                dist[neighbor] = new_cost
                prev[neighbor] = u
                heapq.heappush(pq, (new_cost, neighbor))

    # Reconstruct path
    path = []
    cur = target
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()

    total = dist[target] if dist[target] != float('inf') else None
    return total, path, steps


# ─────────────────────────────────────────────
# 2. BFS SUB-PATH CHECK
# ─────────────────────────────────────────────

def bfs_subpath_check(giver_path, requester_path):
    """
    BFS-based check: verifies that requester_path is a contiguous
    sub-path within giver_path.
    Returns (is_subpath: bool, overlap_ratio: float, bfs_log: list)
    where bfs_log records each BFS frontier expansion step.
    """
    bfs_log = []

    if not giver_path or not requester_path:
        return False, 0.0, bfs_log

    r_start = requester_path[0]
    r_end   = requester_path[-1]

    # Find where requester's start appears in giver's path
    try:
        start_idx = giver_path.index(r_start)
        end_idx   = giver_path.index(r_end)
    except ValueError:
        bfs_log.append({"step": "Requester endpoints not found in giver path", "frontier": []})
        return False, 0.0, bfs_log

    if start_idx >= end_idx:
        bfs_log.append({"step": "Order mismatch – requester dropoff before pickup in giver path", "frontier": []})
        return False, 0.0, bfs_log

    giver_segment = giver_path[start_idx: end_idx + 1]

    # BFS from r_start to r_end within giver_segment graph
    queue   = deque([[r_start]])
    visited = {r_start}
    found   = False

    while queue:
        current_path = queue.popleft()
        node = current_path[-1]

        bfs_log.append({
            "step": f"Exploring: {node}",
            "frontier": list(current_path),
            "giver_segment": giver_segment,
        })

        if node == r_end:
            found = True
            break

        for neighbor in GRAPH.get(node, {}):
            if neighbor not in visited and neighbor in giver_segment:
                visited.add(neighbor)
                queue.append(current_path + [neighbor])

    # Overlap ratio: how many requester stops are covered
    common = sum(1 for stop in requester_path if stop in giver_segment)
    overlap = common / max(len(requester_path), 1)
    return found, round(overlap, 3), bfs_log


# ─────────────────────────────────────────────
# 3. MAIN MATCH FUNCTION (Greedy Best Match)
# ─────────────────────────────────────────────

def match_rides(new_ride, all_rides):
    """
    Find the best matching ride.
    Returns (best_match_ride | None, algo_trace) where algo_trace
    carries Dijkstra steps + BFS log for on-screen visualization.
    """
    target_type = 'give' if new_ride['type'] == 'request' else 'request'

    # Get shortest path for the new ride using Dijkstra
    new_dist, new_path, dijkstra_steps = dijkstra(new_ride['pickup'], new_ride['dropoff'])

    algo_trace = {
        "new_ride": {
            "pickup": new_ride['pickup'],
            "dropoff": new_ride['dropoff'],
            "dijkstra_steps": dijkstra_steps,
            "shortest_path": new_path,
            "distance_km": round(new_dist, 2) if new_dist else None,
        },
        "candidates": [],
        "winner": None,
    }

    candidates = []

    for ride in all_rides:
        if ride['status'] != 'searching':
            continue
        if ride['user_id'] == new_ride['user_id']:
            continue
        if ride['type'] != target_type:
            continue
        if ride['vehicle'] != new_ride['vehicle']:
            continue

        # Dijkstra for the candidate ride
        r_dist, r_path, r_dijkstra_steps = dijkstra(ride['pickup'], ride['dropoff'])

        # BFS sub-path check
        if new_ride['type'] == 'request':
            is_sub, overlap, bfs_log = bfs_subpath_check(r_path, new_path)
        else:
            is_sub, overlap, bfs_log = bfs_subpath_check(new_path, r_path)

        candidate_trace = {
            "ride_id": ride['id'],
            "pickup": ride['pickup'],
            "dropoff": ride['dropoff'],
            "shortest_path": r_path,
            "distance_km": round(r_dist, 2) if r_dist else None,
            "bfs_log": bfs_log,
            "is_subpath": is_sub,
            "overlap": overlap,
        }
        algo_trace["candidates"].append(candidate_trace)

        if overlap > 0:
            candidates.append((overlap, ride, candidate_trace))

    if not candidates:
        return None, algo_trace

    # Greedy: pick highest overlap
    candidates.sort(key=lambda x: -x[0])
    best_overlap, best_ride, best_trace = candidates[0]
    algo_trace["winner"] = {**best_trace, "overlap": best_overlap}

    return best_ride, algo_trace
