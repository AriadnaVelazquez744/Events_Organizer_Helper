
# crawler/graph.py
import json
from typing import List, Dict, Any

class KnowledgeGraphInterface:
    def __init__(self):
        self.nodes = []
        self.edges = []

    def insert_knowledge(self, knowledge: Dict[str, Any]):
        self.nodes.append(knowledge)

    def query(self, entity: str) -> List[Dict[str, Any]]:
        return [node for node in self.nodes if entity in node.get("entities", [])]

    def save_to_file(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({"nodes": self.nodes, "edges": self.edges}, f, ensure_ascii=False, indent=2)

    def load_from_file(self, filename: str):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.nodes = data.get("nodes", [])
            self.edges = data.get("edges", [])
