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
        self.beliefs = {
            "criterios": None,
            "venue": None,
            "catering": None,
            "decor": None,
            "presupuesto_asignado": None,
            "presupuesto_usado": 0.0,
            "conflictos": 0,
            "estado": "inicial",
            "ultima_actualizacion": None,
            "completado": {
                "venue": False,
                "catering": False,
                "decor": False
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor del estado."""
        return self.beliefs.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Establece un valor en el estado y actualiza la metadata."""
        # Actualizar el valor principal
        self.beliefs[key] = value
        self.beliefs["ultima_actualizacion"] = datetime.now().isoformat()
        
        # Si se está actualizando una categoría principal, actualizar el estado de completado
        if key in ["venue", "catering", "decor"]:
            self.beliefs["completado"][key] = value is not None

    def update(self, key: str, subkey: str, value: Any) -> None:
        """Actualiza un subvalor en el estado."""
        if key not in self.beliefs:
            self.beliefs[key] = {}
        elif not isinstance(self.beliefs[key], dict):
            self.beliefs[key] = {}
            
        self.beliefs[key][subkey] = value
        self.beliefs["ultima_actualizacion"] = datetime.now().isoformat()
        
        # Si se está actualizando el estado de completado, asegurarse de que el valor principal también se actualice
        if key == "completado" and subkey in ["venue", "catering", "decor"]:
            if not value and self.beliefs[subkey] is not None:
                self.beliefs[subkey] = None
            elif value and self.beliefs[subkey] is None:
                self.beliefs[subkey] = {}

    def append_conflicto(self, conflicto: Conflict) -> None:
        """Añade un conflicto al estado."""
        self.beliefs["conflictos"] += 1
        self.beliefs["estado"] = "conflicto"

    def has_conflicto(self, tipo: str) -> bool:
        """Verifica si existe un conflicto de un tipo específico."""
        return any(c.tipo == tipo for c in self.beliefs["conflictos"])

    def get_conflictos_por_elemento(self, elemento: str) -> List[Conflict]:
        """Obtiene todos los conflictos relacionados con un elemento específico."""
        return [c for c in self.beliefs["conflictos"] if elemento in c.elementos_afectados]

    def clear_conflictos(self) -> None:
        """Limpia todos los conflictos."""
        self.beliefs["conflictos"] = 0
        self.beliefs["estado"] = "limpio"

    def resumen(self) -> Dict[str, Any]:
        """Genera un resumen del estado actual."""
        return {
            "completado": self.beliefs["completado"],
            "conflictos": self.beliefs["conflictos"],
            "presupuesto_usado": self.get_presupuesto_total_usado(),
            "estado": self.beliefs["estado"],
            "ultima_actualizacion": self.beliefs["ultima_actualizacion"]
        }

    def get_presupuesto_total_usado(self) -> float:
        """Calcula el presupuesto total usado."""
        return self.beliefs["presupuesto_usado"]

    def is_completo(self) -> bool:
        """Verifica si todos los elementos necesarios están completos."""
        return all(self.beliefs[k] is not None for k in ["venue", "catering", "decor"])

    def get_elementos_pendientes(self) -> List[str]:
        """Obtiene la lista de elementos que faltan por completar."""
        return [k for k in ["venue", "catering", "decor"] if self.beliefs[k] is None]

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el estado a un diccionario para serialización."""
        return {
            "beliefs": self.beliefs,
            "metadata": {
                "ultima_actualizacion": self.beliefs["ultima_actualizacion"],
                "version": "1.0",
                "estado": self.beliefs["estado"]
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BeliefState':
        """Crea una instancia de BeliefState desde un diccionario."""
        instance = cls()
        instance.beliefs = data["beliefs"]
        return instance
