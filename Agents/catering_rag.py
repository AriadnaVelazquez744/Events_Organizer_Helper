from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import os
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import math

@dataclass
class MenuPattern:
    style: str
    courses: List[str]
    dietary_options: List[str]
    price_range: Tuple[float, float]
    guest_count_range: Tuple[int, int]
    success_rate: float
    last_used: str
    usage_count: int

@dataclass
class DietaryRestriction:
    name: str
    alternatives: List[str]
    cost_impact: float

class CateringRAG:
    def __init__(self, knowledge_file: str = "catering_graph.json"):
        self.knowledge_file = knowledge_file
        self.menu_patterns: List[MenuPattern] = []
        self.dietary_restrictions: Dict[str, DietaryRestriction] = {
            "vegetariano": DietaryRestriction(
                name="vegetariano",
                alternatives=["vegano", "sin_gluten"],
                cost_impact=1.1
            ),
            "vegano": DietaryRestriction(
                name="vegano",
                alternatives=["vegetariano", "sin_gluten"],
                cost_impact=1.2
            ),
            "sin_gluten": DietaryRestriction(
                name="sin_gluten",
                alternatives=["vegetariano", "vegano"],
                cost_impact=1.15
            )
        }
        self.vectorizer = TfidfVectorizer()
        self._load_knowledge()

    def _load_knowledge(self):
        """Carga la base de conocimiento desde el archivo."""
        try:
            with open(self.knowledge_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and "menu_patterns" in data:
                    patterns_data = data["menu_patterns"]
                    self.menu_patterns = []
                    for pattern_data in patterns_data:
                        if isinstance(pattern_data, dict):
                            try:
                                # Asegurarse de que los rangos sean listas antes de convertirlos a tuplas
                                price_range = tuple(float(x) for x in pattern_data.get("price_range", [50.0, 100.0]))
                                guest_count_range = tuple(int(x) for x in pattern_data.get("guest_count_range", [50, 200]))
                                
                                pattern = MenuPattern(
                                    style=pattern_data.get("style", "standard"),
                                    courses=pattern_data.get("courses", ["entrada", "plato_principal", "postre"]),
                                    dietary_options=pattern_data.get("dietary_options", ["regular"]),
                                    price_range=price_range,
                                    guest_count_range=guest_count_range,
                                    success_rate=float(pattern_data.get("success_rate", 0.8)),
                                    last_used=pattern_data.get("last_used", datetime.now().isoformat()),
                                    usage_count=int(pattern_data.get("usage_count", 0))
                                )
                                self.menu_patterns.append(pattern)
                            except (ValueError, TypeError) as e:
                                print(f"Error al procesar patrón: {e}")
                                continue
        except FileNotFoundError:
            # Inicializa con patrones base si no existe el archivo
            self.menu_patterns = [
                MenuPattern(
                    style="standard",
                    courses=["entrada", "plato_principal", "postre"],
                    dietary_options=["regular", "vegetariano"],
                    price_range=(50.0, 100.0),
                    guest_count_range=(50, 200),
                    success_rate=0.8,
                    last_used=datetime.now().isoformat(),
                    usage_count=0
                ),
                MenuPattern(
                    style="premium",
                    courses=["entrada", "sopa", "plato_principal", "ensalada", "postre"],
                    dietary_options=["regular", "vegetariano", "vegano"],
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
            "menu_patterns": [
                {
                    "style": pattern.style,
                    "courses": pattern.courses,
                    "dietary_options": pattern.dietary_options,
                    "price_range": list(pattern.price_range),  # Convertir tupla a lista para JSON
                    "guest_count_range": list(pattern.guest_count_range),  # Convertir tupla a lista para JSON
                    "success_rate": pattern.success_rate,
                    "last_used": pattern.last_used,
                    "usage_count": pattern.usage_count
                }
                for pattern in self.menu_patterns
            ]
        }
        with open(self.knowledge_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_menu_recommendation(self, budget: float, guest_count: int, 
                              dietary_requirements: List[str], style: str = "standard") -> Dict:
        """Obtiene recomendaciones de menú basadas en el presupuesto y requisitos."""
        # Normalizar requisitos dietéticos a inglés
        dietary_mapping = {
            "vegan": "vegan",
            "vegetariano": "vegetarian",
            "sin_gluten": "gluten-free",
            "gluten-free": "gluten-free",
            "sin_lactosa": "lactose-free",
            "lactose-free": "lactose-free",
            "kosher": "kosher",
            "halal": "halal"
        }
        
        normalized_dietary = [dietary_mapping.get(req.lower(), req.lower()) for req in dietary_requirements]
        
        # Mapeo de estilos a cursos recomendados
        style_courses = {
            "standard": ["appetizer", "main_course", "dessert"],
            "premium": ["welcome_drink", "appetizer", "soup", "main_course", "dessert", "coffee_service"],
            "casual": ["appetizer", "main_course", "dessert"],
            "formal": ["welcome_drink", "appetizer", "soup", "main_course", "side_dish", "dessert", "coffee_service"],
            "buffet": ["appetizer", "main_course", "side_dish", "dessert"]
        }
        
        # Obtener cursos recomendados basados en el estilo
        recommended_courses = style_courses.get(style.lower(), style_courses["standard"])
        
        # Calcular costo estimado por persona
        cost_per_person = budget / guest_count
        
        # Ajustar cursos basados en el presupuesto
        if cost_per_person < 50:
            recommended_courses = ["appetizer", "main_course", "dessert"]
        elif cost_per_person < 100:
            recommended_courses = ["welcome_drink", "appetizer", "main_course", "dessert"]
        else:
            recommended_courses = style_courses.get(style.lower(), style_courses["premium"])
        
        # Generar alternativas dietéticas
        dietary_alternatives = self.suggest_dietary_alternatives(normalized_dietary)
        
        # Calcular costo estimado total
        base_cost = cost_per_person * guest_count
        dietary_cost_multiplier = 1.0 + (len(normalized_dietary) * 0.1)  # 10% extra por cada requisito dietético
        estimated_cost = base_cost * dietary_cost_multiplier
        
        return {
            "style": style,
            "courses": recommended_courses,
            "dietary_options": normalized_dietary,
            "dietary_alternatives": dietary_alternatives,
            "estimated_cost": estimated_cost,
            "cost_per_person": cost_per_person
        }

    def _calculate_menu_cost(self, pattern: MenuPattern, budget: float, guest_count: int) -> float:
        """Calcula el costo estimado del menú."""
        base_cost = budget * (pattern.price_range[0] / 100.0)
        
        # Ajusta por número de invitados
        guest_factor = guest_count / pattern.guest_count_range[0]
        if guest_factor > 1:
            base_cost *= (1 + math.log(guest_factor))
        
        # Ajusta por restricciones dietéticas
        dietary_factor = 1.0
        for restriction in pattern.dietary_options:
            if restriction in self.dietary_restrictions:
                dietary_factor *= self.dietary_restrictions[restriction].cost_impact
        
        final_cost = base_cost * dietary_factor
        
        # Asegura que el costo no exceda el presupuesto más un 10%
        return min(final_cost, budget * 1.1)

    def _generate_custom_menu(self, budget: float, guest_count: int,
                            dietary_requirements: List[str], style: str) -> Dict:
        """Genera un menú personalizado cuando no hay patrones que coincidan."""
        courses = ["entrada", "plato_principal", "postre"]
        if style == "premium":
            courses = ["entrada", "sopa", "plato_principal", "ensalada", "postre"]
        
        return {
            "style": style,
            "courses": courses,
            "dietary_options": dietary_requirements,
            "estimated_cost": budget
        }

    def suggest_dietary_alternatives(self, restrictions: List[str]) -> Dict[str, Dict]:
        """Sugiere alternativas para cada restricción dietética."""
        alternatives = {}
        
        dietary_alternatives = {
            "vegan": {
                "alternatives": ["vegetarian", "plant-based"],
                "cost_impact": 1.1
            },
            "vegetarian": {
                "alternatives": ["vegan", "pescatarian"],
                "cost_impact": 1.05
            },
            "gluten-free": {
                "alternatives": ["gluten-reduced", "celiac-friendly"],
                "cost_impact": 1.15
            },
            "lactose-free": {
                "alternatives": ["dairy-free", "vegan"],
                "cost_impact": 1.1
            },
            "kosher": {
                "alternatives": ["vegetarian", "vegan"],
                "cost_impact": 1.2
            },
            "halal": {
                "alternatives": ["vegetarian", "seafood"],
                "cost_impact": 1.15
            }
        }
        
        for restriction in restrictions:
            if restriction.lower() in dietary_alternatives:
                alternatives[restriction] = dietary_alternatives[restriction.lower()]
            else:
                alternatives[restriction] = {
                    "alternatives": ["standard"],
                    "cost_impact": 1.0
                }
        
        return alternatives

    def update_success_pattern(self, menu_data: Dict, success: bool):
        """Actualiza los patrones de éxito basados en el resultado."""
        # Busca un patrón existente o crea uno nuevo
        pattern = None
        for p in self.menu_patterns:
            if (p.style == menu_data.get("style") and
                p.courses == menu_data.get("courses", []) and
                p.dietary_options == menu_data.get("dietary_options", [])):
                pattern = p
                break

        if not pattern:
            pattern = MenuPattern(
                style=menu_data.get("style", "standard"),
                courses=menu_data.get("courses", []),
                dietary_options=menu_data.get("dietary_options", ["regular"]),
                price_range=(menu_data.get("estimated_cost", 0) * 0.8, menu_data.get("estimated_cost", 0) * 1.2),
                guest_count_range=(menu_data.get("guest_count", 50), menu_data.get("guest_count", 50) * 2),
                success_rate=1.0 if success else 0.0,
                last_used=datetime.now().isoformat(),
                usage_count=1
            )
            self.menu_patterns.append(pattern)
        else:
            # Actualiza el patrón existente
            pattern.usage_count += 1
            pattern.last_used = datetime.now().isoformat()
            pattern.success_rate = (pattern.success_rate * (pattern.usage_count - 1) + (1.0 if success else 0.0)) / pattern.usage_count

        self._save_knowledge()

    def get_similar_cases(self, menu_data: Dict) -> List[Tuple[MenuPattern, float]]:
        """Encuentra casos similares basados en el menú proporcionado."""
        similar_cases = []
        for pattern in self.menu_patterns:
            similarity = self._calculate_similarity(pattern, menu_data)
            if similarity > 0:
                similar_cases.append((pattern, similarity))
        
        # Ordena por similitud
        similar_cases.sort(key=lambda x: x[1], reverse=True)
        return similar_cases

    def _calculate_similarity(self, pattern: MenuPattern, menu_data: Dict) -> float:
        """Calcula la similitud entre un patrón y un menú."""
        # Similitud de estilo
        style_similarity = 1.0 if pattern.style == menu_data.get("style") else 0.0
        
        # Similitud de cursos
        courses1 = set(pattern.courses)
        courses2 = set(menu_data.get("courses", []))
        course_similarity = len(courses1 & courses2) / len(courses1 | courses2) if courses1 | courses2 else 0.0
        
        # Similitud de opciones dietéticas
        dietary1 = set(pattern.dietary_options)
        dietary2 = set(menu_data.get("dietary_options", []))
        dietary_similarity = len(dietary1 & dietary2) / len(dietary1 | dietary2) if dietary1 | dietary2 else 0.0
        
        # Peso de los componentes
        weights = {
            "style": 0.3,
            "courses": 0.4,
            "dietary": 0.3
        }
        
        # Calcula la similitud total
        total_similarity = (
            style_similarity * weights["style"] +
            course_similarity * weights["courses"] +
            dietary_similarity * weights["dietary"]
        )
        
        return min(max(total_similarity, 0.0), 1.0)  # Asegura que esté en [0,1] 