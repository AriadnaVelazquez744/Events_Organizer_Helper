
# crawler/graph.py
import json
from typing import List, Dict, Any, Optional

class KnowledgeGraphInterface:
    def __init__(self):
        self.nodes = {}  # clave: id o url
        self.edges = []  # tuplas (from_id, relation, to_id)

    def insert_knowledge(self, knowledge: Dict[str, Any]):
        venue_id = knowledge.get("url")
        title = knowledge.get("title", "Sin Título")

        # Nodo principal del venue
        self.nodes[venue_id] = {
            "tipo": "venue",
            "nombre": title,
            "completitud": "parcial"  # esto se puede actualizar más abajo
        }

        # Capacidad (valor numérico)
        capacidad = knowledge.get("capacidad")
        if isinstance(capacidad, int):
            cap_id = f"capacidad::{capacidad}"
            self.nodes[cap_id] = {"tipo": "capacidad", "valor": capacidad}
            self.edges.append((venue_id, "capacidad", cap_id))

        # Precio (subvalores si es un dict)
        precio = knowledge.get("precio")
        if isinstance(precio, dict):
            for subkey, val in precio.items():
                if val:
                    pid = f"precio:{subkey}::{val}"
                    self.nodes[pid] = {"tipo": f"precio_{subkey}", "valor": val}
                    self.edges.append((venue_id, f"precio_{subkey}", pid))

       # Ambiente
        ambiente = knowledge.get("ambiente")
        print (ambiente)
        if isinstance(ambiente, str):
            ambiente = [x.strip() for x in ambiente.split(",")]
        for amb in ambiente or []:
            amb_id = f"ambiente::{amb.lower()}"
            self.nodes[amb_id] = {"tipo": "ambiente", "valor": amb}
            self.edges.append((venue_id, "ambiente", amb_id))

        # Tipo de local
        tipo_local = knowledge.get("tipo_local")
        print (tipo_local)
        if isinstance(tipo_local, str):
            tipo_local = [x.strip() for x in tipo_local.split(",")]
        for tipo in tipo_local or []:
            tid = f"tipo_local::{tipo.lower()}"
            self.nodes[tid] = {"tipo": "tipo_local", "valor": tipo}
            self.edges.append((venue_id, "tipo_local", tid))

        # Servicios
        # print(servicio)
        for servicio in knowledge.get("servicios", []):
            sid = f"servicio::{servicio.lower().strip()}"
            self.nodes[sid] = {"tipo": "servicio", "valor": servicio}
            self.edges.append((venue_id, "servicio", sid))

        # Restricciones
        
        restricciones = knowledge.get("restricciones")
        print(restricciones)
        if isinstance(restricciones, str):
            restricciones = [restricciones]
        for restric in restricciones or []:
            rid = f"restriccion::{restric.lower().strip()}"
            self.nodes[rid] = {"tipo": "restriccion", "valor": restric}
            self.edges.append((venue_id, "restriccion", rid))

        # Eventos compatibles
        for evento in knowledge.get("eventos_compatibles", []):
            eid = f"evento::{evento.lower().strip()}"
            self.nodes[eid] = {"tipo": "evento", "valor": evento}
            self.edges.append((venue_id, "evento_compatible", eid))

        # Outlinks
        for link in knowledge.get("outlinks", []):
            if not isinstance(link, str) or not link.startswith("http"):
                continue
            lid = f"outlink::{link}"
            self.nodes[lid] = {"tipo": "outlink", "valor": link}
            self.edges.append((venue_id, "referencia", lid))

        # Completitud mínima
        has_essential = all([
            isinstance(knowledge.get("capacidad"), int),
            isinstance(knowledge.get("precio"), dict),
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

