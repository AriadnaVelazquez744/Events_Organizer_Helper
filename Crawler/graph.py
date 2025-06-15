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
        entity_type = knowledge.get("tipo", "unknown")
        entity_id = knowledge.get("url")
        title = knowledge.get("title", "Sin Título")

        if entity_id not in self.nodes:
            self.nodes[entity_id] = {
                "tipo": entity_type,
                "nombre": title,
                "original_data": knowledge,
                "completitud": "parcial"
            }

        if entity_type == "venue":
            self._insert_venue(entity_id, knowledge)
        elif entity_type == "catering":
            self._insert_catering(entity_id, knowledge)
        elif entity_type == "decor":
            self._insert_decor(entity_id, knowledge)
        else:
            print(f"[GRAPH] Tipo desconocido: {entity_type}")


    # def insert_knowledge(self, knowledge: Dict[str, Any]):
    #     venue_id = knowledge.get("url")
    #     title = knowledge.get("title", "Sin Título")

    #     # Nodo principal del venue
    #     if venue_id not in self.nodes:
    #         self.nodes[venue_id] = {
    #             "tipo": "venue",
    #             "nombre": title,
    #             "original_data": knowledge,
    #             "completitud": "parcial"  # esto se puede actualizar más abajo
                
    #         }
            
    #     def safe_add_node(nid, tipo, valor):
    #         if nid not in self.nodes:
    #             self.nodes[nid] = {"tipo": tipo, "valor": valor}
    #         return nid

    #     def safe_add_edge(from_id, rel, to_id):
    #         if (from_id, rel, to_id) not in self.edges:
    #             self.edges.append((from_id, rel, to_id))

    #     # Capacidad
    #     capacidad = knowledge.get("capacity")
    #     if isinstance(capacidad, int):
    #         nid = safe_add_node(f"capacity::{capacidad}", "capacity", capacidad)
    #         safe_add_edge(venue_id, "capacity", nid)

    #     # Precio
    #     precio = knowledge.get("price")
    #     if isinstance(precio, dict):
    #         for subkey, val in precio.items():
    #             if val:
    #                 pid = safe_add_node(f"price:{subkey}::{val}", f"price_{subkey}", val)
    #                 safe_add_edge(venue_id, f"price_{subkey}", pid)

    #     # Ambiente
    #     ambiente = knowledge.get("atmosphere")
    #     if isinstance(ambiente, str):
    #         ambiente = [x.strip() for x in ambiente.split(",")]
    #     for amb in ambiente or []:
    #         nid = safe_add_node(f"atmosphere::{amb.lower()}", "atmosphere", amb)
    #         safe_add_edge(venue_id, "atmosphere", nid)

    #     # Tipo local
    #     tipo_local = knowledge.get("tvenue_type")
    #     if isinstance(tipo_local, str):
    #         tipo_local = [x.strip() for x in tipo_local.split(",")]
    #     for tipo in tipo_local or []:
    #         nid = safe_add_node(f"venue_type::{tipo.lower()}", "venue_type", tipo)
    #         safe_add_edge(venue_id, "venue_type", nid)

    #     # Servicios
    #     for s in knowledge.get("services", []):
    #         nid = safe_add_node(f"service::{s.lower().strip()}", "service", s)
    #         safe_add_edge(venue_id, "service", nid)

    #     # Restricciones
    #     restricciones = knowledge.get("restrictions")
    #     if isinstance(restricciones, str):
    #         restricciones = [restricciones]
    #     for r in restricciones or []:
    #         nid = safe_add_node(f"restriction::{r.lower().strip()}", "restriction", r)
    #         safe_add_edge(venue_id, "restriction", nid)

    #     # Eventos
    #     for e in knowledge.get("supported_events", []):
    #         nid = safe_add_node(f"event::{e.lower().strip()}", "event", e)
    #         safe_add_edge(venue_id, "supported_event", nid)

    #     # Outlinks
    #     for link in knowledge.get("outlinks", []):
    #         if isinstance(link, str) and link.startswith("http"):
    #             nid = safe_add_node(f"outlink::{link}", "outlink", link)
    #             safe_add_edge(venue_id, "referencia", nid)

    #     # Completitud
    #     has_essential = all([
    #         isinstance(knowledge.get("capacity"), int),
    #         isinstance(knowledge.get("price"), dict),
    #         knowledge.get("title")
    #     ])
    #     self.nodes[venue_id]["completitud"] = "completa" if has_essential else "parcial"
    
    def _insert_venue(self, entity_id: str, knowledge: Dict[str, Any]):
        def safe_add_node(nid, tipo, valor):
            if nid not in self.nodes:
                self.nodes[nid] = {"tipo": tipo, "valor": valor}
            return nid

        def safe_add_edge(from_id, rel, to_id):
            if (from_id, rel, to_id) not in self.edges:
                self.edges.append((from_id, rel, to_id))

        for campo, tipo_rel, rel_name in [
            ("capacity", "capacity", "capacity"),
            ("price", "price", "price"),
            ("atmosphere", "atmosphere", "atmosphere"),
            ("venue_type", "venue_type", "venue_type"),
            ("services", "service", "service"),
            ("restrictions", "restriction", "restriction"),
            ("supported_events", "event", "supported_event"),
            ("outlinks", "outlink", "referencia")
        ]:
            val = knowledge.get(campo)
            if val is None:
                continue

            if isinstance(val, dict):  # price
                for subk, subv in val.items():
                    if isinstance(subv, dict):
                        for kk, vv in subv.items():
                            if isinstance(vv, (int, float)):
                                nid = safe_add_node(f"{rel_name}:{subk}:{kk}:{vv}", f"{tipo_rel}_{subk}_{kk}", vv)
                                safe_add_edge(entity_id, f"{rel_name}_{subk}_{kk}", nid)
                    elif subv:
                        nid = safe_add_node(f"{rel_name}:{subk}::{subv}", f"{tipo_rel}_{subk}", subv)
                        safe_add_edge(entity_id, f"{rel_name}_{subk}", nid)
            elif isinstance(val, list):
                for item in val:
                    nid = safe_add_node(f"{rel_name}::{item.lower().strip()}", tipo_rel, item)
                    safe_add_edge(entity_id, rel_name, nid)
            elif isinstance(val, str):
                for item in [x.strip() for x in val.split(",")]:
                    nid = safe_add_node(f"{rel_name}::{item.lower()}", tipo_rel, item)
                    safe_add_edge(entity_id, rel_name, nid)
            elif isinstance(val, (int, float)):
                nid = safe_add_node(f"{rel_name}::{val}", tipo_rel, val)
                safe_add_edge(entity_id, rel_name, nid)

        # Completitud
        has_essential = all([
            isinstance(knowledge.get("capacity"), int),
            isinstance(knowledge.get("price"), dict),
            knowledge.get("title")
        ])
        self.nodes[entity_id]["completitud"] = "completa" if has_essential else "parcial"
        
        
    def _insert_catering(self, entity_id: str, knowledge: Dict[str, Any]):
        def safe_add_node(nid, tipo, valor):
            if nid not in self.nodes:
                self.nodes[nid] = {"tipo": tipo, "valor": valor}
            return nid

        def safe_add_edge(from_id, rel, to_id):
            if (from_id, rel, to_id) not in self.edges:
                self.edges.append((from_id, rel, to_id))

        fields = [
            ("service area", "service_area"),
            ("price", "price"),
            ("cuisine", "cuisine"),
            ("dietary_options", "dietary_option"),
            ("catering", "catering"),
            ("restrictions", "restriction"),
            ("outlinks", "outlink")
        ]

        for field, rel in fields:
            val = knowledge.get(field)
            if not val:
                continue

            if isinstance(val, list):
                for v in val:
                    nid = safe_add_node(f"{rel}::{v.lower().strip()}", rel, v)
                    safe_add_edge(entity_id, rel, nid)
            elif isinstance(val, str):
                for item in [v.strip() for v in val.split(",")]:
                    nid = safe_add_node(f"{rel}::{item.lower()}", rel, item)
                    safe_add_edge(entity_id, rel, nid)
            elif isinstance(val, (int, float, dict)):
                nid = safe_add_node(f"{rel}::{val}", rel, val)
                safe_add_edge(entity_id, rel, nid)

    def _insert_decor(self, entity_id: str, knowledge: Dict[str, Any]):
        """Inserta un nodo de decoración floral en el grafo."""
        def safe_add_node(nid, tipo, valor):
            if nid not in self.nodes:
                self.nodes[nid] = {"tipo": tipo, "valor": valor}
            return nid

        def safe_add_edge(from_id, rel, to_id):
            if (from_id, rel, to_id) not in self.edges:
                self.edges.append((from_id, rel, to_id))

        fields = [
            ("ubication", "ubication"),
            ("price", "price"),
            ("service_levels", "service_level"),
            ("pre_wedding_services", "pre_wedding_service"),
            ("post_wedding_services", "post_wedding_service"),
            ("day_of_services", "day_of_service"),
            ("arrangement_styles", "arrangement_style"),
            ("floral_arrangements", "floral_arrangement"),
            ("restrictions", "restriction"),
            ("outlinks", "outlink")
        ]

        for field, rel in fields:
            val = knowledge.get(field)
            if not val:
                continue

            if isinstance(val, list):
                for v in val:
                    nid = safe_add_node(f"{rel}::{v.lower().strip()}", rel, v)
                    safe_add_edge(entity_id, rel, nid)
            elif isinstance(val, str):
                for item in [v.strip() for v in val.split(",")]:
                    nid = safe_add_node(f"{rel}::{item.lower()}", rel, item)
                    safe_add_edge(entity_id, rel, nid)
            elif isinstance(val, (int, float, dict)):
                nid = safe_add_node(f"{rel}::{val}", rel, val)
                safe_add_edge(entity_id, rel, nid)

        # Completitud
        has_essential = all([
            knowledge.get("title"),
            knowledge.get("price"),
            knowledge.get("service_levels"),
            knowledge.get("floral_arrangements")
        ])
        self.nodes[entity_id]["completitud"] = "completa" if has_essential else "parcial"

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
            
    def clean_errors(self):
        """Elimina nodos con errores (nombre == 'ERROR' o title == 'ERROR') y sus edges"""
        to_remove = []

        for node_id, node_data in self.nodes.items():
            if node_data.get("tipo") == "venue":
                if node_data.get("nombre") == "ERROR":
                    to_remove.append(node_id)
                elif node_data.get("original_data", {}).get("title") == "ERROR":
                    to_remove.append(node_id)

        print(f"[GRAPH] Nodos con errores detectados: {len(to_remove)}")

        # Eliminar nodos y edges asociadas
        for node_id in to_remove:
            del self.nodes[node_id]
            self.edges = [e for e in self.edges if e[0] != node_id and e[2] != node_id]

        print(f"[GRAPH] Nodos y edges eliminados con éxito.")


