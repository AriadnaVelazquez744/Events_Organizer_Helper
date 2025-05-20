
# crawler/graph.py
import json
from typing import List, Dict, Any, Optional

class KnowledgeGraphInterface:
    def __init__(self):
        self.nodes = {}  # clave: id o url
        self.edges = []  # tuplas (from_id, relation, to_id)

    def insert_knowledge(self, knowledge: Dict[str, Any]):
        node_id = knowledge.get("url") or f"node_{len(self.nodes)}"
        
        if node_id in self.nodes:
            print(f"[GRAPH] Actualizando nodo existente: {node_id}")
            self.nodes[node_id].update(knowledge)
        else:
            print(f"[GRAPH] Insertando nuevo nodo: {node_id}")
            self.nodes[node_id] = knowledge

        # Crear relaciones semánticas seguras
        ciudad = knowledge.get("ciudad")
        if ciudad:
            city_id = f"city::{ciudad.lower().strip()}"
            if city_id not in self.nodes:
                self.nodes[city_id] = {"tipo": "ciudad", "nombre": ciudad}
            self.edges.append((node_id, "ubicado_en", city_id))

        tipo_evento = knowledge.get("tipo_evento")
        if tipo_evento:
            tipo_id = f"tipo::{tipo_evento.lower().strip()}"
            if tipo_id not in self.nodes:
                self.nodes[tipo_id] = {"tipo": "tipo_evento", "nombre": tipo_evento}
            self.edges.append((node_id, "apto_para", tipo_id))

        # Marcar completitud del nodo
        knowledge["completitud"] = "completa" if all([
            knowledge.get("capacidad"),
            knowledge.get("precio"),
            knowledge.get("ciudad")
        ]) else "parcial"

    def query(self, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if entity_type:
            return [n for n in self.nodes.values() if n.get("tipo") == entity_type]
        return list(self.nodes.values())

    def find_by_relation(self, from_type: str, relation: str) -> List[Dict[str, Any]]:
        results = []
        for from_id, rel, to_id in self.edges:
            if rel == relation and self.nodes[from_id].get("tipo") == from_type:
                results.append((self.nodes[from_id], rel, self.nodes[to_id]))
        return results

    def save_to_file(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "nodes": self.nodes,
                "edges": self.edges
            }, f, ensure_ascii=False, indent=2)

    def load_from_file(self, filename: str):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.nodes = data.get("nodes", {})
            self.edges = data.get("edges", [])

