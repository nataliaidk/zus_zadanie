import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Optional

import networkx as nx

from app.models.schemas import ExplainResponse, GraphEdgeOut, GraphNodeOut

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_GRAPH_PATH = DATA_DIR / "knowledge_graph.json"


def _node_out(graph: nx.DiGraph, node_id: str) -> GraphNodeOut:
    data = graph.nodes[node_id]
    return GraphNodeOut(
        id=node_id,
        type=data["type"],
        title=data["title"],
        plain_language=data["plain_language"],
        legal_basis=data["legal_basis"],
    )


def _edge_out(graph: nx.DiGraph, source: str, target: str) -> GraphEdgeOut:
    data = graph.edges[source, target]
    return GraphEdgeOut(
        source=source,
        target=target,
        relation=data.get("relation", ""),
        plain_language=data.get("plain_language", ""),
    )


class GraphService:
    def __init__(self, path: Path | None = None) -> None:
        payload = json.loads((path or DEFAULT_GRAPH_PATH).read_text(encoding="utf-8"))
        self.graph: nx.DiGraph = nx.DiGraph()
        for node in payload["nodes"]:
            self.graph.add_node(node["id"], **node)
        for edge in payload["edges"]:
            self.graph.add_edge(edge["source"], edge["target"], **edge)

    def dump(self) -> dict[str, Any]:
        nodes = [_node_out(self.graph, n).model_dump() for n in self.graph.nodes]
        edges = [_edge_out(self.graph, u, v).model_dump() for u, v in self.graph.edges]
        return {"nodes": nodes, "edges": edges}

    def has_node(self, node_id: str) -> bool:
        return node_id in self.graph

    def neighborhood(self, node_id: str, depth: int = 2) -> tuple[list[str], list[tuple[str, str]]]:
        """Undirected ego so both 'why' (incoming) and 'then' (outgoing) are visible."""
        undirected = self.graph.to_undirected()
        ego = nx.ego_graph(undirected, node_id, radius=depth)
        nodes = list(ego.nodes)
        edges = [
            (u, v)
            for u, v in self.graph.edges
            if u in ego and v in ego
        ]
        return nodes, edges

    def legal_path(self, source: str, target: str) -> Optional[list[str]]:
        if source == target:
            return [source]
        try:
            return nx.shortest_path(self.graph, source, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass
        try:
            return nx.shortest_path(self.graph, target, source)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def path_from_provision(self, node_id: str) -> Optional[list[str]]:
        """Prefer a path from a przepis node so 'Skąd ten wynik?' starts at the legal basis."""
        provisions = [
            n for n, data in self.graph.nodes(data=True) if data.get("type") == "przepis"
        ]
        best: Optional[list[str]] = None
        for provision in provisions:
            path = self.legal_path(provision, node_id)
            if path is None:
                continue
            if best is None or len(path) < len(best):
                best = path
        return best

    def explain(
        self,
        node_id: str,
        target_id: Optional[str] = None,
        depth: int = 2,
    ) -> dict[str, Any]:
        if node_id not in self.graph:
            raise KeyError(node_id)
        if target_id is not None and target_id not in self.graph:
            raise KeyError(target_id)

        path: Optional[list[str]]
        if target_id:
            path = self.legal_path(node_id, target_id)
        else:
            path = self.path_from_provision(node_id)

        if path:
            node_ids = path
            edge_pairs = list(zip(path, path[1:]))
            narrative = [
                self.graph.nodes[path[0]]["plain_language"],
            ]
            for src, dst in edge_pairs:
                rel = self.graph.edges[src, dst].get("plain_language") if self.graph.has_edge(src, dst) else None
                if rel is None and self.graph.has_edge(dst, src):
                    rel = self.graph.edges[dst, src].get("plain_language")
                narrative.append(rel or self.graph.nodes[dst]["plain_language"])
        else:
            node_ids, edge_pairs = self.neighborhood(node_id, depth)
            narrative = [
                self.graph.nodes[node_id]["plain_language"],
                "Brak jednej ścieżki od przepisu — poniżej sąsiedztwo węzła.",
            ]

        nodes = [_node_out(self.graph, n) for n in node_ids]
        edges = []
        for src, dst in edge_pairs:
            if self.graph.has_edge(src, dst):
                edges.append(_edge_out(self.graph, src, dst))
            elif self.graph.has_edge(dst, src):
                edges.append(_edge_out(self.graph, dst, src))

        return ExplainResponse(
            question="Skąd ten wynik?",
            node_id=node_id,
            target_id=target_id,
            narrative=narrative,
            path=path or [node_id],
            nodes=nodes,
            edges=edges,
        ).model_dump()

    def search(self, query: str, limit: int = 8) -> list[str]:
        """Rank node ids for GraphRAG. Keyword aliases plus folded token overlap."""
        folded = _fold(query)
        tokens = set(re.findall(r"[a-z0-9]+", folded))
        scores: dict[str, float] = {}
        for alias, node_ids in QUERY_ALIASES.items():
            if alias in folded:
                for node_id in node_ids:
                    scores[node_id] = scores.get(node_id, 0) + 5
        for node_id, data in self.graph.nodes(data=True):
            hay = _fold(f"{data.get('title', '')} {data.get('plain_language', '')} {data.get('legal_basis', '')}")
            overlap = tokens & set(re.findall(r"[a-z0-9]+", hay))
            if overlap:
                scores[node_id] = scores.get(node_id, 0) + len(overlap)
        ranked = sorted(scores, key=lambda n: scores[n], reverse=True)
        return ranked[:limit]

    def subgraph_for_query(self, query: str, limit: int = 6, depth: int = 1) -> dict[str, Any]:
        hits = self.search(query, limit=limit)
        node_ids: set[str] = set(hits)
        for hit in hits:
            neigh, _ = self.neighborhood(hit, depth=depth)
            node_ids.update(neigh)
        nodes = [_node_out(self.graph, n).model_dump() for n in node_ids if n in self.graph]
        edges = [
            _edge_out(self.graph, u, v).model_dump()
            for u, v in self.graph.edges
            if u in node_ids and v in node_ids
        ]
        return {"query": query, "hit_ids": hits, "nodes": nodes, "edges": edges}


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower()


QUERY_ALIASES = {
    "81,5": ["swiadczenie_stawka_815", "ryzyko_termin_wniosku_21"],
    "81.5": ["swiadczenie_stawka_815", "ryzyko_termin_wniosku_21"],
    "zam": ["dokument_zam", "przepis_formularze_zam"],
    "zur": ["dokument_zniesione_zur_zao_z3b", "przepis_formularze_zam"],
    "zao": ["dokument_zniesione_zur_zao_z3b"],
    "z-3b": ["dokument_zniesione_zur_zao_z3b"],
    "z-3": ["dokument_z3", "status_maly_platnik"],
    "wyczekiwanie": ["ryzyko_wyczekiwanie_30", "ryzyko_wyczekiwanie_90", "przepis_wyczekiwanie"],
    "14 tygod": ["ryzyko_14_tygodni_matka"],
    "14 tyg": ["ryzyko_14_tygodni_matka"],
    "9 tygod": ["ryzyko_9_tygodni_nieprzenoszalne"],
    "9 tyg": ["ryzyko_9_tygodni_nieprzenoszalne"],
    "za zyciem": ["status_za_zyciem", "przepis_za_zyciem", "dokument_za_zyciem"],
    "wczesniak": ["status_wczesniak", "swiadczenie_uzupelniajacy"],
    "ojcowski": ["swiadczenie_ojcowski"],
    "rodzicielsk": ["swiadczenie_rodzicielski"],
    "macierzynsk": ["swiadczenie_macierzynski"],
    "platnik": ["przepis_platnik_20", "status_duzy_platnik", "status_maly_platnik"],
    "zaleglos": ["ryzyko_zaleglosci_b2b", "status_zaleglosci_skladek"],
}
