from dataclasses import dataclass
from datetime import datetime
import json
import math
from typing import Dict, List, Tuple, Optional

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
    def __init__(self, knowledge_file: str = "decor_knowledge.json"):
        self.knowledge_file = knowledge_file
        self.decor_patterns: List[DecorPattern] = []
        self._load_knowledge()

    def _load_knowledge(self):
        """Carga la base de conocimiento desde el archivo."""
        try:
            with open(self.knowledge_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and "decor_patterns" in data:
                    for pattern_data in data["decor_patterns"]:
                        if isinstance(pattern_data, dict):
                            try:
                                # Convertir rangos de precio y cantidad de invitados a tuplas
                                price_range = tuple(pattern_data.get("price_range", [0.0, 0.0]))
                                guest_count_range = tuple(pattern_data.get("guest_count_range", [0, 0]))
                                
                                pattern = DecorPattern(
                                    style=pattern_data.get("style", "classic"),
                                    decorations=pattern_data.get("decorations", []),
                                    paper_goods=pattern_data.get("paper_goods", []),
                                    rentals=pattern_data.get("rentals", []),
                                    price_range=price_range,
                                    guest_count_range=guest_count_range,
                                    success_rate=float(pattern_data.get("success_rate", 0.0)),
                                    last_used=pattern_data.get("last_used", datetime.now().isoformat()),
                                    usage_count=int(pattern_data.get("usage_count", 0))
                                )
                                self.decor_patterns.append(pattern)
                            except Exception as e:
                                print(f"Error procesando patrón: {e}")
        except FileNotFoundError:
            # Inicializa con patrones base si no existe el archivo
            self.decor_patterns = [
                DecorPattern(
                    style="classic",
                    decorations=["flores", "velas", "centros", "arreglos", "candelabros"],
                    paper_goods=["invitaciones", "menús", "tarjetas", "etiquetas"],
                    rentals=["mesas", "sillas", "manteles", "cubiertos", "cristalería"],
                    price_range=(50.0, 100.0),
                    guest_count_range=(50, 200),
                    success_rate=0.8,
                    last_used=datetime.now().isoformat(),
                    usage_count=0
                ),
                DecorPattern(
                    style="premium",
                    decorations=["flores premium", "velas aromáticas", "centros artesanales", 
                               "arreglos exclusivos", "candelabros vintage", "iluminación especial"],
                    paper_goods=["invitaciones personalizadas", "menús gourmet", "tarjetas premium",
                               "etiquetas doradas", "programas de evento"],
                    rentals=["mesas premium", "sillas de diseño", "manteles de lujo", 
                            "cubiertos premium", "cristalería fina", "vajilla exclusiva"],
                    price_range=(100.0, 200.0),
                    guest_count_range=(30, 150),
                    success_rate=0.9,
                    last_used=datetime.now().isoformat(),
                    usage_count=0
                )
            ]
            self._save_knowledge()

    def _save_knowledge(self):
        """Guarda la base de conocimiento en el archivo."""
        data = {
            "decor_patterns": [
                {
                    "style": pattern.style,
                    "decorations": pattern.decorations,
                    "paper_goods": pattern.paper_goods,
                    "rentals": pattern.rentals,
                    "price_range": list(pattern.price_range),
                    "guest_count_range": list(pattern.guest_count_range),
                    "success_rate": pattern.success_rate,
                    "last_used": pattern.last_used,
                    "usage_count": pattern.usage_count
                }
                for pattern in self.decor_patterns
            ]
        }
        with open(self.knowledge_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_decor_recommendation(self, budget: float, guest_count: int, 
                               style: str = "classic") -> Dict:
        """Genera una recomendación de decoración basada en los criterios proporcionados."""
        # Filtra patrones por estilo y requisitos
        valid_patterns = [
            p for p in self.decor_patterns
            if p.style == style and
            p.guest_count_range[0] <= guest_count <= p.guest_count_range[1]
        ]

        if not valid_patterns:
            return self._generate_custom_recommendation(budget, guest_count, style)

        # Ordena por tasa de éxito y uso
        valid_patterns.sort(key=lambda p: (p.success_rate, p.usage_count), reverse=True)
        best_pattern = valid_patterns[0]

        # Calcula el costo estimado
        base_cost = (best_pattern.price_range[0] + best_pattern.price_range[1]) / 2
        estimated_cost = base_cost * guest_count

        # Ajusta el costo si excede el presupuesto
        if estimated_cost > budget:
            # Reduce elementos para ajustar al presupuesto
            decorations = best_pattern.decorations[:3]
            paper_goods = best_pattern.paper_goods[:2]
            rentals = best_pattern.rentals[:3]
            estimated_cost = budget
        else:
            decorations = best_pattern.decorations
            paper_goods = best_pattern.paper_goods
            rentals = best_pattern.rentals

        return {
            "style": style,
            "decorations": decorations,
            "paper_goods": paper_goods,
            "rentals": rentals,
            "estimated_cost": estimated_cost,
            "guest_count": guest_count
        }

    def _generate_custom_recommendation(self, budget: float, guest_count: int, 
                                      style: str) -> Dict:
        """Genera una recomendación personalizada cuando no hay patrones válidos."""
        # Elementos base según el estilo
        if style == "premium":
            decorations = ["flores premium", "velas aromáticas", "centros artesanales"]
            paper_goods = ["invitaciones personalizadas", "menús gourmet"]
            rentals = ["mesas premium", "sillas de diseño", "manteles de lujo"]
            base_cost = 150.0
        else:  # classic
            decorations = ["flores", "velas", "centros"]
            paper_goods = ["invitaciones", "menús"]
            rentals = ["mesas", "sillas", "manteles"]
            base_cost = 75.0

        # Calcula el costo estimado
        estimated_cost = base_cost * guest_count

        # Ajusta el costo si excede el presupuesto
        if estimated_cost > budget:
            # Reduce elementos para ajustar al presupuesto
            decorations = decorations[:2]
            paper_goods = paper_goods[:1]
            rentals = rentals[:2]
            estimated_cost = budget

        return {
            "style": style,
            "decorations": decorations,
            "paper_goods": paper_goods,
            "rentals": rentals,
            "estimated_cost": estimated_cost,
            "guest_count": guest_count
        }

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

    def update_success_pattern(self, pattern_data: Dict, success: bool):
        """Actualiza un patrón basado en su éxito."""
        # Busca un patrón existente que coincida
        matching_pattern = None
        for pattern in self.decor_patterns:
            if (pattern.style == pattern_data["style"] and
                pattern.guest_count_range[0] <= pattern_data["guest_count"] <= pattern.guest_count_range[1]):
                matching_pattern = pattern
                break

        if matching_pattern:
            # Actualiza el patrón existente
            matching_pattern.usage_count += 1
            matching_pattern.last_used = datetime.now().isoformat()
            
            # Actualiza la tasa de éxito
            if success:
                matching_pattern.success_rate = (matching_pattern.success_rate * 
                                              (matching_pattern.usage_count - 1) + 1.0) / matching_pattern.usage_count
            else:
                matching_pattern.success_rate = (matching_pattern.success_rate * 
                                              (matching_pattern.usage_count - 1)) / matching_pattern.usage_count
        else:
            # Crea un nuevo patrón
            new_pattern = DecorPattern(
                style=pattern_data["style"],
                decorations=pattern_data["decorations"],
                paper_goods=pattern_data["paper_goods"],
                rentals=pattern_data["rentals"],
                price_range=(pattern_data["estimated_cost"] * 0.8, pattern_data["estimated_cost"] * 1.2),
                guest_count_range=(pattern_data["guest_count"] * 0.8, pattern_data["guest_count"] * 1.2),
                success_rate=1.0 if success else 0.0,
                last_used=datetime.now().isoformat(),
                usage_count=1
            )
            self.decor_patterns.append(new_pattern)

        self._save_knowledge() 