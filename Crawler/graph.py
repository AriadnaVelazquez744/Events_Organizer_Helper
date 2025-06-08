
# crawler/graph.py
import json
import os
from typing import List, Dict, Any, Optional


class KnowledgeGraphInterface:
    def __init__(self, filename: str = "graph.json"):
        self.nodes = {}  
        self.edges = []  
        self.filename = filename
        
        if os.path.exists(self.filename):
            self.load_from_file(self.filename)
            print(f"[GRAPH] Grafo cargado desde {self.filename}")
        else:
            print(f"[GRAPH] No existe {self.filename}, creando nuevo grafo.")

    def insert_knowledge(self, knowledge: Dict[str, Any]):
        venue_id = knowledge.get("url")
        title = knowledge.get("title", "Sin Título")

        # Nodo principal del venue
        if venue_id not in self.nodes:
            self.nodes[venue_id] = {
                "tipo": "venue",
                "nombre": title,
                "original_data": knowledge,
                "completitud": "parcial"  # esto se puede actualizar más abajo
                
            }
            
        def safe_add_node(nid, tipo, valor):
            if nid not in self.nodes:
                self.nodes[nid] = {"tipo": tipo, "valor": valor}
            return nid

        def safe_add_edge(from_id, rel, to_id):
            if (from_id, rel, to_id) not in self.edges:
                self.edges.append((from_id, rel, to_id))

        # Capacidad
        capacidad = knowledge.get("capacity")
        if isinstance(capacidad, int):
            nid = safe_add_node(f"capacity::{capacidad}", "capacity", capacidad)
            safe_add_edge(venue_id, "capacity", nid)

        # Precio
        precio = knowledge.get("price")
        if isinstance(precio, dict):
            for subkey, val in precio.items():
                if val:
                    pid = safe_add_node(f"price:{subkey}::{val}", f"price_{subkey}", val)
                    safe_add_edge(venue_id, f"price_{subkey}", pid)

        # Ambiente
        ambiente = knowledge.get("atmosphere")
        if isinstance(ambiente, str):
            ambiente = [x.strip() for x in ambiente.split(",")]
        for amb in ambiente or []:
            nid = safe_add_node(f"atmosphere::{amb.lower()}", "atmosphere", amb)
            safe_add_edge(venue_id, "atmosphere", nid)

        # Tipo local
        tipo_local = knowledge.get("tvenue_type")
        if isinstance(tipo_local, str):
            tipo_local = [x.strip() for x in tipo_local.split(",")]
        for tipo in tipo_local or []:
            nid = safe_add_node(f"venue_type::{tipo.lower()}", "venue_type", tipo)
            safe_add_edge(venue_id, "venue_type", nid)

        # Servicios
        for s in knowledge.get("services", []):
            nid = safe_add_node(f"service::{s.lower().strip()}", "service", s)
            safe_add_edge(venue_id, "service", nid)

        # Restricciones
        restricciones = knowledge.get("restrictions")
        if isinstance(restricciones, str):
            restricciones = [restricciones]
        for r in restricciones or []:
            nid = safe_add_node(f"restriction::{r.lower().strip()}", "restriction", r)
            safe_add_edge(venue_id, "restriction", nid)

        # Eventos
        for e in knowledge.get("supported_events", []):
            nid = safe_add_node(f"event::{e.lower().strip()}", "event", e)
            safe_add_edge(venue_id, "supported_event", nid)

        # Outlinks
        for link in knowledge.get("outlinks", []):
            if isinstance(link, str) and link.startswith("http"):
                nid = safe_add_node(f"outlink::{link}", "outlink", link)
                safe_add_edge(venue_id, "referencia", nid)

        # Completitud
        has_essential = all([
            isinstance(knowledge.get("capacity"), int),
            isinstance(knowledge.get("price"), dict),
            knowledge.get("title")
        ])
        self.nodes[venue_id]["completitud"] = "completa" if has_essential else "parcial"



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

