"""Network topology generation.

Returns a plain adjacency list (list of neighbor-index lists) so the model core
has no dependency on any graph library at runtime. Tie strengths are returned in
parallel for the 90/10 weak/strong channel mechanism.
"""

from typing import List, Tuple
import numpy as np
import networkx as nx


def build_network(cfg: dict, rng: np.random.Generator) -> Tuple[List[List[int]], List[List[float]]]:
    """Build a network from config. Returns (adjacency, tie_strength).

    adjacency[i] is the list of neighbor indices of agent i.
    tie_strength[i][j_idx] in (0,1] is the strength of the tie from i to its
    j_idx-th neighbor (parallel to adjacency[i]). Strengths are symmetric.
    """
    n = cfg["n_agents"]
    topo = cfg["topology"]
    k = max(2, int(cfg["mean_degree"]))
    # networkx expects even k for ring-based generators; round up.
    if k % 2 == 1:
        k += 1
    seed = int(rng.integers(0, 2**31 - 1))

    if topo == "small_world":
        g = nx.watts_strogatz_graph(n, min(k, n - 1), cfg["rewire_prob"], seed=seed)
    elif topo == "ring_lattice":
        g = nx.watts_strogatz_graph(n, min(k, n - 1), 0.0, seed=seed)
    elif topo == "random":
        p = min(1.0, k / max(1, n - 1))
        g = nx.gnp_random_graph(n, p, seed=seed)
    elif topo == "uniform_mixing":
        # Complete graph: every agent can contact every other (well-mixed).
        g = nx.complete_graph(n)
    else:
        raise ValueError(f"unknown topology {topo!r}")

    adjacency: List[List[int]] = [sorted(g.neighbors(i)) for i in range(n)]

    # Assign tie strengths. Default uniform 1.0; if the 90/10 channel is on,
    # mark a strong_tie_fraction of each agent's ties as strong (1.0) and the
    # rest weak (a small value), keeping symmetry.
    tie_strength = _assign_tie_strengths(adjacency, cfg, rng)
    return adjacency, tie_strength


def _assign_tie_strengths(adjacency, cfg, rng) -> List[List[float]]:
    n = len(adjacency)
    if not cfg.get("tie_strength_channels", False):
        return [[1.0] * len(adj) for adj in adjacency]

    weak = 0.1
    strong = 1.0
    frac = cfg["strong_tie_fraction"]
    # Decide each undirected edge's strength once, then mirror.
    edge_strength = {}
    for i in range(n):
        for j in adjacency[i]:
            key = (min(i, j), max(i, j))
            if key not in edge_strength:
                edge_strength[key] = strong if rng.random() < frac else weak
    out = []
    for i in range(n):
        out.append([edge_strength[(min(i, j), max(i, j))] for j in adjacency[i]])
    return out


def network_summary(adjacency: List[List[int]]) -> dict:
    n = len(adjacency)
    degrees = [len(a) for a in adjacency]
    n_edges = sum(degrees) // 2
    return {
        "n_agents": n,
        "n_edges": n_edges,
        "mean_degree": (sum(degrees) / n) if n else 0.0,
        "min_degree": min(degrees) if degrees else 0,
        "max_degree": max(degrees) if degrees else 0,
    }


def layout_positions(adjacency: List[List[int]], rng: np.random.Generator) -> List[Tuple[float, float]]:
    """2-D positions for drawing the network in the viewer (spring layout)."""
    n = len(adjacency)
    g = nx.Graph()
    g.add_nodes_from(range(n))
    for i in range(n):
        for j in adjacency[i]:
            if j > i:
                g.add_edge(i, j)
    seed = int(rng.integers(0, 2**31 - 1))
    pos = nx.spring_layout(g, seed=seed, k=None, iterations=50)
    return [(float(pos[i][0]), float(pos[i][1])) for i in range(n)]
