from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
from datetime import datetime
import numpy as np
from pathlib import Path

@dataclass
class BudgetDistribution:
    venue: float
    catering: float
    decor: float
    music: float
    other: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "venue": self.venue,
            "catering": self.catering,
            "decor": self.decor,
            "music": self.music,
            "other": self.other
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'BudgetDistribution':
        return cls(
            venue=data.get("venue", 0.0),
            catering=data.get("catering", 0.0),
            decor=data.get("decor", 0.0),
            music=data.get("music", 0.0),
            other=data.get("other", 0.0)
        )

class PlannerRAG:
    def __init__(self, knowledge_base_path: Optional[str] = None):
        self.knowledge_base = {
            "budget_patterns": {
                "standard": BudgetDistribution(0.40, 0.30, 0.15, 0.10, 0.05),
                "premium": BudgetDistribution(0.35, 0.35, 0.20, 0.05, 0.05),
                "budget": BudgetDistribution(0.45, 0.25, 0.15, 0.10, 0.05)
            },
            "conflict_resolutions": {
                "budget_exceeded": {
                    "strategies": [
                        "reduce_guest_count",
                        "adjust_venue_requirements",
                        "modify_menu_options",
                        "simplify_decor"
                    ],
                    "priority": ["venue", "catering", "decor"]
                },
                "capacity_mismatch": {
                    "strategies": [
                        "find_alternative_venue",
                        "adjust_guest_list",
                        "split_event",
                        "modify_layout"
                    ],
                    "priority": ["venue", "catering"]
                },
                "date_conflict": {
                    "strategies": [
                        "find_alternative_date",
                        "check_venue_availability",
                        "adjust_vendor_schedule"
                    ],
                    "priority": ["venue", "catering", "decor"]
                }
            },
            "timeline_patterns": {
                "standard": {
                    "venue_booking": 6,  # meses
                    "catering_booking": 4,
                    "decor_planning": 3,
                    "music_booking": 2
                },
                "rush": {
                    "venue_booking": 3,
                    "catering_booking": 2,
                    "decor_planning": 1,
                    "music_booking": 1
                }
            },
            "success_patterns": {
                "budget_management": [],
                "vendor_selection": [],
                "timeline_management": []
            }
        }
        
        if knowledge_base_path:
            self.load_knowledge_base(knowledge_base_path)

    def load_knowledge_base(self, path: str):
        """Carga la base de conocimiento desde un archivo JSON."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.knowledge_base.update(data)
        except FileNotFoundError:
            print(f"Archivo de base de conocimiento no encontrado: {path}")
        except json.JSONDecodeError:
            print(f"Error al decodificar el archivo JSON: {path}")

    def save_knowledge_base(self, path: str):
        """Guarda la base de conocimiento en un archivo JSON."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar la base de conocimiento: {str(e)}")

    def get_budget_distribution(self, total_budget: float, style: str = "standard") -> Dict[str, float]:
        """Obtiene la distribución de presupuesto recomendada."""
        pattern = self.knowledge_base["budget_patterns"].get(style, self.knowledge_base["budget_patterns"]["standard"])
        distribution = pattern.to_dict()
        
        return {
            category: amount * total_budget
            for category, amount in distribution.items()
        }

    def suggest_conflict_resolution(self, conflict_type: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sugiere estrategias para resolver conflictos."""
        if conflict_type not in self.knowledge_base["conflict_resolutions"]:
            return []

        resolution = self.knowledge_base["conflict_resolutions"][conflict_type]
        strategies = []

        for strategy in resolution["strategies"]:
            strategies.append({
                "strategy": strategy,
                "priority": resolution["priority"],
                "context": context
            })

        return strategies

    def get_timeline_recommendations(self, event_date: datetime, style: str = "standard") -> Dict[str, datetime]:
        """Obtiene recomendaciones de timeline para el evento."""
        pattern = self.knowledge_base["timeline_patterns"].get(style, self.knowledge_base["timeline_patterns"]["standard"])
        
        recommendations = {}
        for task, months in pattern.items():
            deadline = event_date.replace(month=event_date.month - months)
            recommendations[task] = deadline

        return recommendations

    def update_success_pattern(self, pattern_type: str, data: Dict[str, Any]):
        """Actualiza los patrones de éxito con nuevos datos."""
        if pattern_type in self.knowledge_base["success_patterns"]:
            self.knowledge_base["success_patterns"][pattern_type].append({
                "data": data,
                "timestamp": datetime.now().isoformat()
            })

    def get_similar_cases(self, current_case: Dict[str, Any], pattern_type: str) -> List[Dict[str, Any]]:
        """Encuentra casos similares en la base de conocimiento."""
        if pattern_type not in self.knowledge_base["success_patterns"]:
            return []

        similar_cases = []
        for case in self.knowledge_base["success_patterns"][pattern_type]:
            similarity = self._calculate_similarity(current_case, case["data"])
            if similarity > 0.7:  # Umbral de similitud
                similar_cases.append({
                    "case": case["data"],
                    "similarity": similarity
                })

        return sorted(similar_cases, key=lambda x: x["similarity"], reverse=True)

    def _calculate_similarity(self, case1: Dict[str, Any], case2: Dict[str, Any]) -> float:
        """Calcula la similitud entre dos casos."""
        # Implementación básica de similitud
        common_keys = set(case1.keys()) & set(case2.keys())
        if not common_keys:
            return 0.0

        similarities = []
        for key in common_keys:
            if isinstance(case1[key], (int, float)) and isinstance(case2[key], (int, float)):
                # Para valores numéricos, calculamos similitud basada en la diferencia relativa
                max_val = max(abs(case1[key]), abs(case2[key]))
                if max_val == 0:
                    similarities.append(1.0)
                else:
                    diff = abs(case1[key] - case2[key]) / max_val
                    similarities.append(1.0 - diff)
            elif isinstance(case1[key], str) and isinstance(case2[key], str):
                # Para strings, comparamos si son iguales
                similarities.append(1.0 if case1[key] == case2[key] else 0.0)
            elif isinstance(case1[key], list) and isinstance(case2[key], list):
                # Para listas, calculamos la intersección
                common = len(set(case1[key]) & set(case2[key]))
                total = len(set(case1[key]) | set(case2[key]))
                similarities.append(common / total if total > 0 else 0.0)

        return np.mean(similarities) if similarities else 0.0

    def suggest_error_correction(self, task_type: str, error_content: Any) -> List[Dict[str, Any]]:
        """Sugiere estrategias de corrección basadas en el tipo de tarea y el error."""
        strategies = []
        error_str = str(error_content).lower()
        
        # Estrategias específicas por tipo de tarea
        if task_type == "budget_distribution":
            if "timeout" in error_str or "timeout" in error_str:
                strategies.append({
                    "type": "budget_redistribution",
                    "description": "Redistribuir presupuesto con restricciones más flexibles",
                    "parameters": {"flexible_constraints": True, "timeout_handling": True}
                })
            elif "constraint" in error_str or "restriction" in error_str:
                strategies.append({
                    "type": "budget_adjustment",
                    "description": "Ajustar criterios de presupuesto",
                    "parameters": {"adjustment_factor": 0.9, "relax_constraints": True}
                })
            else:
                strategies.append({
                    "type": "budget_retry",
                    "description": "Reintentar distribución de presupuesto",
                    "parameters": {"retry_with_backoff": True}
                })
        
        elif task_type in ["venue_search", "catering_search", "decor_search"]:
            category = task_type.replace("_search", "")
            
            if "no results" in error_str or "empty" in error_str:
                strategies.extend([
                    {
                        "type": f"{category}_relax_constraints",
                        "description": f"Relajar restricciones de {category}",
                        "parameters": {"relax_factor": 0.8, "expand_search": True}
                    },
                    {
                        "type": f"{category}_alternative_search",
                        "description": f"Buscar alternativas de {category}",
                        "parameters": {"use_alternatives": True, "fallback_options": True}
                    }
                ])
            elif "timeout" in error_str:
                strategies.append({
                    "type": f"{category}_timeout_handling",
                    "description": f"Manejar timeout en búsqueda de {category}",
                    "parameters": {"timeout_retry": True, "reduced_scope": True}
                })
            elif "budget" in error_str or "price" in error_str:
                strategies.append({
                    "type": f"{category}_budget_increase",
                    "description": f"Aumentar presupuesto para {category}",
                    "parameters": {"budget_increase": 0.2, "flexible_pricing": True}
                })
            else:
                strategies.append({
                    "type": f"{category}_retry",
                    "description": f"Reintentar búsqueda de {category}",
                    "parameters": {"retry_with_backoff": True, "improved_query": True}
                })
        
        # Estrategias generales para cualquier error
        if not strategies:
            strategies.append({
                "type": "general_retry",
                "description": "Reintentar tarea con parámetros ajustados",
                "parameters": {"retry_count": 1, "backoff_delay": 2}
            })
        
        return strategies

    def get_error_patterns(self) -> Dict[str, List[str]]:
        """Obtiene patrones de errores conocidos y sus soluciones."""
        return {
            "timeout_errors": [
                "increase_timeout",
                "reduce_scope",
                "use_caching",
                "parallel_processing"
            ],
            "constraint_errors": [
                "relax_constraints",
                "adjust_parameters",
                "use_alternatives",
                "increase_budget"
            ],
            "connection_errors": [
                "retry_with_backoff",
                "use_fallback",
                "check_connectivity",
                "reduce_load"
            ],
            "data_errors": [
                "validate_input",
                "use_defaults",
                "clean_data",
                "request_correction"
            ]
        }