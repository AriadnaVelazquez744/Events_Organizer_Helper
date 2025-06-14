# beliefs_schema.py
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Conflict:
    tipo: str
    descripcion: str
    elementos_afectados: List[str]
    severidad: str = "warning"  # warning, error, critical
    timestamp: str = datetime.now().isoformat()

class BeliefState:
    def __init__(self):
        self.state = {
            "criterios": {},
            "venue": None,
            "catering": None,
            "decor": None,
            "presupuesto_asignado": {},
            "conflictos": [],
            "evaluaciones": {},
            "pendiente": [],
            "metadata": {
                "ultima_actualizacion": datetime.now().isoformat(),
                "version": "1.0",
                "estado": "inicial"
            }
        }

    def get(self, key: str) -> Any:
        """Obtiene un valor del estado."""
        return self.state.get(key)

    def set(self, key: str, value: Any) -> None:
        """Establece un valor en el estado y actualiza la metadata."""
        if key in self.state:
            self.state[key] = value
            self.state["metadata"]["ultima_actualizacion"] = datetime.now().isoformat()
        else:
            raise KeyError(f"Clave de belief inválida: {key}")

    def update(self, key: str, subkey: str, value: Any) -> None:
        """Actualiza un subvalor en el estado."""
        if key not in self.state or not isinstance(self.state[key], dict):
            self.state[key] = {}
        self.state[key][subkey] = value
        self.state["metadata"]["ultima_actualizacion"] = datetime.now().isoformat()

    def append_conflicto(self, conflicto: Conflict) -> None:
        """Añade un conflicto al estado."""
        self.state["conflictos"].append(conflicto)
        self.state["metadata"]["estado"] = "conflicto"

    def has_conflicto(self, tipo: str) -> bool:
        """Verifica si existe un conflicto de un tipo específico."""
        return any(c.tipo == tipo for c in self.state["conflictos"])

    def get_conflictos_por_elemento(self, elemento: str) -> List[Conflict]:
        """Obtiene todos los conflictos relacionados con un elemento específico."""
        return [c for c in self.state["conflictos"] if elemento in c.elementos_afectados]

    def clear_conflictos(self) -> None:
        """Limpia todos los conflictos."""
        self.state["conflictos"] = []
        self.state["metadata"]["estado"] = "limpio"

    def resumen(self) -> Dict[str, Any]:
        """Genera un resumen del estado actual."""
        return {
            "completado": {
                "venue": self.state["venue"] is not None,
                "catering": self.state["catering"] is not None,
                "decor": self.state["decor"] is not None
            },
            "conflictos": len(self.state["conflictos"]),
            "presupuesto_usado": self.get_presupuesto_total_usado(),
            "estado": self.state["metadata"]["estado"],
            "ultima_actualizacion": self.state["metadata"]["ultima_actualizacion"]
        }

    def get_presupuesto_total_usado(self) -> float:
        """Calcula el presupuesto total usado."""
        return sum(self.state["presupuesto_asignado"].values())

    def is_completo(self) -> bool:
        """Verifica si todos los elementos necesarios están completos."""
        return all(self.state[k] is not None for k in ["venue", "catering", "decor"])

    def get_elementos_pendientes(self) -> List[str]:
        """Obtiene la lista de elementos que faltan por completar."""
        return [k for k in ["venue", "catering", "decor"] if self.state[k] is None]

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el estado a un diccionario para serialización."""
        return {
            "state": self.state,
            "metadata": self.state["metadata"]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BeliefState':
        """Crea una instancia de BeliefState desde un diccionario."""
        instance = cls()
        instance.state = data["state"]
        return instance
