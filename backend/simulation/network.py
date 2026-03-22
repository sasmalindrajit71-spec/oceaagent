"""
OCEAN Social Network — small-world topology builder.
Generates structured social graphs mirroring real platforms.
"""

import networkx as nx
import random
import json
from typing import List


def build_social_graph(agents: list[dict], k: int = 6, p: float = 0.1) -> dict:
    """
    Build a small-world social graph using Watts-Strogatz model.
    
    k: each node connected to k nearest neighbours
    p: rewiring probability (weak-tie bridges)
    
    Returns serializable graph dict with nodes and edges.
    """
    n = len(agents)
    if n < 4:
        k = n - 1

    # Generate small-world graph
    G = nx.watts_strogatz_graph(n, k=min(k, n-1), p=p, seed=42)

    # Enrich with cluster-based preferential attachment
    # Agents in the same cluster get additional edges
    for i, agent_a in enumerate(agents):
        for j, agent_b in enumerate(agents[i+1:], start=i+1):
            if agent_a["cluster_id"] == agent_b["cluster_id"]:
                if not G.has_edge(i, j) and random.random() < 0.3:
                    G.add_edge(i, j)

    # Build serializable output
    nodes = []
    for i, agent in enumerate(agents):
        degree = G.degree(i)
        nodes.append({
            "id": agent["id"],
            "index": i,
            "tier": agent["tier"],
            "cluster_id": agent["cluster_id"],
            "degree": degree,
            "influence_score": agent["influence_score"],
            "political_lean": agent["political_lean"],
        })

    edges = []
    for u, v in G.edges():
        edges.append({
            "source": agents[u]["id"],
            "target": agents[v]["id"],
            "weight": 1.0,
            "interaction_count": 0,
        })

    # Calculate cluster statistics
    clusters = {}
    for agent in agents:
        cid = agent["cluster_id"]
        if cid not in clusters:
            clusters[cid] = {"count": 0, "avg_lean": 0.0, "members": []}
        clusters[cid]["count"] += 1
        clusters[cid]["avg_lean"] += agent["political_lean"]
        clusters[cid]["members"].append(agent["id"])

    for cid in clusters:
        clusters[cid]["avg_lean"] /= clusters[cid]["count"]

    return {
        "nodes": nodes,
        "edges": edges,
        "clusters": clusters,
        "stats": {
            "node_count": n,
            "edge_count": len(edges),
            "avg_clustering": nx.average_clustering(G),
            "avg_path_length": nx.average_shortest_path_length(G) if nx.is_connected(G) else None,
        }
    }


def get_agent_neighbours(graph: dict, agent_id: str, limit: int = 10) -> list[str]:
    """Get neighbour agent IDs for a given agent."""
    neighbours = []
    for edge in graph["edges"]:
        if edge["source"] == agent_id:
            neighbours.append(edge["target"])
        elif edge["target"] == agent_id:
            neighbours.append(edge["source"])
    return neighbours[:limit]


def get_weak_tie_bridges(graph: dict, agent_id: str, agent_cluster: int) -> list[str]:
    """Get agents from different clusters (weak ties / bridges)."""
    bridges = []
    agent_ids_in_other_clusters = [
        n["id"] for n in graph["nodes"]
        if n["cluster_id"] != agent_cluster and n["id"] != agent_id
    ]
    # Return a random sample of cross-cluster agents
    return random.sample(agent_ids_in_other_clusters, min(3, len(agent_ids_in_other_clusters)))
