from dataclasses import dataclass
from datetime import datetime
import json
import math
from typing import Dict, List, Tuple, Optional, Any
import os

@dataclass
class DecorPattern:
    style: str
    decorations: List[str]
    paper_goods: List[str]
    rentals: List[str]
    price_range: Tuple[float, float]
    guest_count_range: Tuple[int, int]
    success_rate: float
    last_used: str
    usage_count: int

class DecorRAG:
    def __init__(self):
        self.patterns_file = "decor_patterns.json"
        self.patterns = self._load_patterns()
        
    def _load_patterns(self) -> Dict[str, Any]:
        """Carga los patrones de éxito desde el archivo."""
        if os.path.exists(self.patterns_file):
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "success_patterns": [],
            "budget_recommendations": [],
            "style_recommendations": []
        }
        
    def _save_patterns(self):
        """Guarda los patrones de éxito en el archivo."""
        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, indent=2, ensure_ascii=False)

    def get_decor_recommendation(self, budget: float, guest_count: int, style: str = "classic") -> Dict[str, Any]:
        """Genera recomendaciones basadas en el presupuesto y estilo."""
        # Calcular presupuesto por invitado
        budget_per_guest = budget / guest_count if guest_count > 0 else 0
        
        # Recomendaciones base por estilo
        style_recommendations = {
            "classic": {
                "decorations": [
                    "Centros de mesa clásicos",
                    "Arcos decorativos",
                    "Candelabros",
                    "Manteles elegantes"
                ],
                "paper_goods": [
                    "Invitaciones formales",
                    "Menús elegantes",
                    "Place cards"
                ],
                "rentals": [
                    "Sillas Chiavari",
                    "Mesas redondas",
                    "Cristalería fina"
                ]
            },
            "rustic": {
                "decorations": [
                    "Centros de mesa naturales",
                    "Arreglos de madera",
                    "Luz de velas",
                    "Elementos vintage"
                ],
                "paper_goods": [
                    "Invitaciones kraft",
                    "Menús rústicos",
                    "Tags de madera"
                ],
                "rentals": [
                    "Mesas de madera",
                    "Sillas de campo",
                    "Vajilla rústica"
                ]
            },
            "modern": {
                "decorations": [
                    "Centros geométricos",
                    "Iluminación LED",
                    "Elementos metálicos",
                    "Diseños minimalistas"
                ],
                "paper_goods": [
                    "Invitaciones minimalistas",
                    "Menús modernos",
                    "Tarjetas acrílicas"
                ],
                "rentals": [
                    "Mesas de cristal",
                    "Sillas modernas",
                    "Vajilla contemporánea"
                ]
            }
        }

        # Ajustar recomendaciones según el presupuesto
        base_recommendations = style_recommendations.get(style, style_recommendations["classic"])
        
        # Calcular costos estimados
        estimated_cost = {
            "decorations": min(budget * 0.4, 5000),  # 40% del presupuesto, máximo $5000
            "paper_goods": min(budget * 0.1, 1000),  # 10% del presupuesto, máximo $1000
            "rentals": min(budget * 0.3, 3000)       # 30% del presupuesto, máximo $3000
        }

        return {
            "decorations": base_recommendations["decorations"],
            "paper_goods": base_recommendations["paper_goods"],
            "rentals": base_recommendations["rentals"],
            "estimated_cost": estimated_cost
        }

    def update_success_pattern(self, pattern: Dict[str, Any], success: bool):
        """Actualiza los patrones de éxito basados en resultados previos."""
        if success:
            self.patterns["success_patterns"].append({
                "pattern": pattern,
                "timestamp": "2024-03-19T00:00:00Z"  # Esto debería ser dinámico
            })
            self._save_patterns()

    def suggest_conflict_resolution(self, conflict_type: str, context: Dict[str, Any]) -> List[str]:
        """Sugiere estrategias para resolver conflictos comunes."""
        strategies = {
            "budget_conflict": [
                "Priorizar elementos esenciales y reducir extras",
                "Buscar alternativas más económicas para elementos decorativos",
                "Considerar opciones de alquiler en lugar de compra"
            ],
            "style_conflict": [
                "Encontrar un punto medio entre estilos",
                "Mantener consistencia en un estilo principal",
                "Usar elementos neutros que complementen diferentes estilos"
            ],
            "vendor_conflict": [
                "Buscar proveedores con más flexibilidad",
                "Negociar términos y condiciones",
                "Considerar proveedores alternativos"
            ]
        }
        
        return strategies.get(conflict_type, ["Revisar y ajustar los requisitos"])

    def find_similar_cases(self, style: str, guest_count: int, 
                          budget: float) -> List[Dict]:
        """Encuentra casos similares basados en estilo, cantidad de invitados y presupuesto."""
        similar_cases = []
        
        for pattern in self.decor_patterns:
            # Calcula similitud en estilo
            style_similarity = 1.0 if pattern.style == style else 0.0
            
            # Calcula similitud en cantidad de invitados
            guest_similarity = 1.0 - min(
                abs(guest_count - (pattern.guest_count_range[0] + pattern.guest_count_range[1]) / 2) / 
                max(guest_count, (pattern.guest_count_range[0] + pattern.guest_count_range[1]) / 2),
                1.0
            )
            
            # Calcula similitud en presupuesto
            budget_similarity = 1.0 - min(
                abs(budget - (pattern.price_range[0] + pattern.price_range[1]) / 2) / 
                max(budget, (pattern.price_range[0] + pattern.price_range[1]) / 2),
                1.0
            )
            
            # Calcula similitud total (promedio ponderado)
            total_similarity = (style_similarity * 0.4 + 
                              guest_similarity * 0.3 + 
                              budget_similarity * 0.3)
            
            if total_similarity > 0.5:  # Solo incluir casos con similitud significativa
                similar_cases.append({
                    "pattern": pattern,
                    "similarity": total_similarity
                })
        
        # Ordenar por similitud
        similar_cases.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_cases 