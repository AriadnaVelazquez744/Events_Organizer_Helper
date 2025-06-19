from dataclasses import dataclass
from datetime import datetime
import json
import math
from typing import Dict, List, Tuple, Optional, Any
import os

@dataclass
class DecorPattern:
    style: str
    service_levels: List[str]
    pre_wedding_services: List[str]
    post_wedding_services: List[str]
    day_of_services: List[str]
    arrangement_styles: List[str]
    floral_arrangements: List[str]
    decorations: List[str]
    paper_goods: List[str]
    rentals: List[str]
    restrictions: List[str]
    price_range: Tuple[float, float]
    guest_count_range: Tuple[int, int]
    success_rate: float
    last_used: str
    usage_count: int

class DecorRAG:
    def __init__(self, knowledge_file: str = "decor_graph.json"):
        self.knowledge_file = knowledge_file
        self.patterns: Dict[str, DecorPattern] = {}
        self._load_knowledge()

    def _load_knowledge(self):
        """Carga el conocimiento desde el archivo."""
        if os.path.exists(self.knowledge_file):
            try:
                with open(self.knowledge_file, 'r') as f:
                    data = json.load(f)
                    for key, pattern_data in data.items():
                        self.patterns[key] = DecorPattern(
                            style=pattern_data["style"],
                            service_levels=pattern_data["service_levels"],
                            pre_wedding_services=pattern_data["pre_wedding_services"],
                            post_wedding_services=pattern_data["post_wedding_services"],
                            day_of_services=pattern_data["day_of_services"],
                            arrangement_styles=pattern_data["arrangement_styles"],
                            floral_arrangements=pattern_data["floral_arrangements"],
                            decorations=pattern_data.get("decorations", []),
                            paper_goods=pattern_data.get("paper_goods", []),
                            rentals=pattern_data.get("rentals", []),
                            restrictions=pattern_data["restrictions"],
                            price_range=tuple(pattern_data["price_range"]),
                            guest_count_range=tuple(pattern_data["guest_count_range"]),
                            success_rate=pattern_data["success_rate"],
                            last_used=pattern_data["last_used"],
                            usage_count=pattern_data["usage_count"]
                        )
            except Exception as e:
                print(f"[DecorRAG] Error cargando conocimiento: {str(e)}")
                self.patterns = {}

    def _save_knowledge(self):
        """Guarda el conocimiento en el archivo."""
        try:
            data = {
                key: {
                    "style": pattern.style,
                    "service_levels": pattern.service_levels,
                    "pre_wedding_services": pattern.pre_wedding_services,
                    "post_wedding_services": pattern.post_wedding_services,
                    "day_of_services": pattern.day_of_services,
                    "arrangement_styles": pattern.arrangement_styles,
                    "floral_arrangements": pattern.floral_arrangements,
                    "decorations": pattern.decorations,
                    "paper_goods": pattern.paper_goods,
                    "rentals": pattern.rentals,
                    "restrictions": pattern.restrictions,
                    "price_range": list(pattern.price_range),
                    "guest_count_range": list(pattern.guest_count_range),
                    "success_rate": pattern.success_rate,
                    "last_used": pattern.last_used,
                    "usage_count": pattern.usage_count
                }
                for key, pattern in self.patterns.items()
            }
            with open(self.knowledge_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[DecorRAG] Error guardando conocimiento: {str(e)}")

    def get_decor_recommendation(self, budget: float, guest_count: int, style: str = "classic") -> Dict:
        """Obtiene recomendaciones de decoración basadas en el presupuesto y requisitos."""
        # Mapeo de estilos a servicios recomendados
        style_services = {
            "classic": {
                "service_levels": ["Full-Service Floral Design", "Complete Wedding Design"],
                "pre_wedding_services": ["Consultation", "Design Planning", "Mock-up Creation"],
                "post_wedding_services": ["Clean-up", "Storage Solutions"],
                "day_of_services": ["Setup", "Breakdown", "On-site Management"],
                "arrangement_styles": ["Classic", "Traditional", "Elegant"],
                "floral_arrangements": ["Bouquets", "Centerpieces", "Ceremony decor", "Aisle markers"],
                "decorations": ["Candles", "Linens", "Vases"],
                "paper_goods": ["Invitations", "Place Cards", "Menus"],
                "rentals": ["Chairs", "Tables", "Arches"]
            },
            "modern": {
                "service_levels": ["Contemporary Design", "Modern Floral Artistry"],
                "pre_wedding_services": ["Virtual Consultation", "Digital Design", "3D Mock-ups"],
                "post_wedding_services": ["Eco-friendly Cleanup", "Sustainable Storage"],
                "day_of_services": ["Professional Setup", "Coordination", "Emergency Kit"],
                "arrangement_styles": ["Modern", "Minimalist", "Geometric"],
                "floral_arrangements": ["Architectural Pieces", "Suspended Installations", "Modern Centerpieces"],
                "decorations": ["Geometric shapes", "LED lighting", "Metallic accents"],
                "paper_goods": ["Digital invites", "Minimalist stationery"],
                "rentals": ["Ghost chairs", "Acrylic tables", "Modern backdrops"]
            },
            "rustic": {
                "service_levels": ["Rustic Design", "Natural Floral Design"],
                "pre_wedding_services": ["Venue Visit", "Natural Material Sourcing", "Handcrafted Elements"],
                "post_wedding_services": ["Natural Cleanup", "Composting Services"],
                "day_of_services": ["Natural Setup", "Rustic Coordination"],
                "arrangement_styles": ["Rustic", "Wild", "Natural"],
                "floral_arrangements": ["Wildflower Arrangements", "Wooden Elements", "Natural Centerpieces"],
                "decorations": ["Mason jars", "Burlap runners", "Twine and fairy lights"],
                "paper_goods": ["Kraft paper invitations", "Hand-stamped menus"],
                "rentals": ["Farmhouse tables", "Wooden benches", "Whiskey barrels"]
            },
            "luxury": {
                "service_levels": ["Luxury Design", "Premium Floral Design"],
                "pre_wedding_services": ["VIP Consultation", "Luxury Design Planning", "Premium Mock-ups"],
                "post_wedding_services": ["Premium Cleanup", "Luxury Storage"],
                "day_of_services": ["Premium Setup", "Luxury Coordination", "VIP Service"],
                "arrangement_styles": ["Luxury", "Opulent", "Grand"],
                "floral_arrangements": ["Premium Centerpieces", "Luxury Installations", "Grand Displays"],
                "decorations": ["Crystal chandeliers", "Silk drapes", "Gold accents"],
                "paper_goods": ["Embossed invitations", "Calligraphy place cards"],
                "rentals": ["Velvet seating", "Mirrored tables", "Elaborate arches"]
            }
        }

        # Obtener servicios recomendados basados en el estilo
        style_lower = style.lower()
        style_data = style_services.get(style_lower, style_services["classic"])
        
        print(f"[DecorRAG] Estilo solicitado: '{style}' (normalizado a '{style_lower}')")
        print(f"[DecorRAG] Usando servicios para estilo: {style_lower}")
        
        recommended_services = {
            "service_levels": style_data["service_levels"],
            "pre_wedding_services": style_data["pre_wedding_services"],
            "post_wedding_services": style_data["post_wedding_services"],
            "day_of_services": style_data["day_of_services"],
            "arrangement_styles": style_data["arrangement_styles"],
            "floral_arrangements": style_data["floral_arrangements"],
            "decorations": style_data["decorations"],
            "paper_goods": style_data["paper_goods"],
            "rentals": style_data["rentals"]
        }

        # Calcular costo estimado por persona
        cost_per_person = budget / guest_count

        # Ajustar recomendaciones basadas en el presupuesto
        if cost_per_person < 50:
            # Reducir servicios para presupuestos bajos
            for key in recommended_services:
                if isinstance(recommended_services[key], list):
                    recommended_services[key] = recommended_services[key][:2]
        elif cost_per_person < 100:
            # Servicios moderados
            for key in recommended_services:
                if isinstance(recommended_services[key], list):
                    recommended_services[key] = recommended_services[key][:3]

        # Calcular costo estimado total
        base_cost = cost_per_person * guest_count
        service_cost_multiplier = 1.0 + (len(recommended_services["service_levels"]) * 0.05)  # 5% extra por cada nivel de servicio
        estimated_cost = base_cost * service_cost_multiplier

        return {
            "style": style,
            **recommended_services,
            "estimated_cost": estimated_cost,
            "cost_per_person": cost_per_person
        }

    def update_success_pattern(self, pattern_data: Dict, success: bool):
        """Actualiza los patrones de éxito basados en los resultados."""
        key = f"{pattern_data['style']}_{pattern_data['guest_count']}"
        
        if key not in self.patterns:
            self.patterns[key] = DecorPattern(
                style=pattern_data["style"],
                service_levels=pattern_data.get("service_levels", []),
                pre_wedding_services=pattern_data.get("pre_wedding_services", []),
                post_wedding_services=pattern_data.get("post_wedding_services", []),
                day_of_services=pattern_data.get("day_of_services", []),
                arrangement_styles=pattern_data.get("arrangement_styles", []),
                floral_arrangements=pattern_data.get("floral_arrangements", []),
                decorations=pattern_data.get("decorations", []),
                paper_goods=pattern_data.get("paper_goods", []),
                rentals=pattern_data.get("rentals", []),
                restrictions=pattern_data.get("restrictions", []),
                price_range=(0, float('inf')),
                guest_count_range=(0, float('inf')),
                success_rate=1.0 if success else 0.0,
                last_used=datetime.now().isoformat(),
                usage_count=1
            )
        else:
            pattern = self.patterns[key]
            pattern.success_rate = (pattern.success_rate * pattern.usage_count + (1.0 if success else 0.0)) / (pattern.usage_count + 1)
            pattern.usage_count += 1
            pattern.last_used = datetime.now().isoformat()
            
            # Actualizar rangos de precio y guest_count
            if pattern_data.get("estimated_cost"):
                current_min, current_max = pattern.price_range
                new_price = pattern_data["estimated_cost"]
                pattern.price_range = (min(current_min, new_price), max(current_max, new_price))
            
            if pattern_data.get("guest_count"):
                current_min, current_max = pattern.guest_count_range
                new_count = pattern_data["guest_count"]
                pattern.guest_count_range = (min(current_min, new_count), max(current_max, new_count))

        self._save_knowledge()

    def get_similar_cases(self, decor_data: Dict) -> List[Tuple[DecorPattern, float]]:
        """Encuentra casos similares basados en los datos proporcionados."""
        similar_cases = []
        
        for pattern in self.patterns.values():
            similarity = self._calculate_similarity(pattern, decor_data)
            if similarity > 0.5:  # Solo incluir casos con similitud significativa
                similar_cases.append((pattern, similarity))
        
        return sorted(similar_cases, key=lambda x: x[1], reverse=True)

    def _calculate_similarity(self, pattern: DecorPattern, decor_data: Dict) -> float:
        """Calcula la similitud entre un patrón y los datos de decoración."""
        similarity = 0.0
        total_factors = 0

        # Similitud de estilo
        if pattern.style == decor_data.get("style"):
            similarity += 1.0
        total_factors += 1

        # Similitud de niveles de servicio
        if "service_levels" in decor_data:
            pattern_services = set(pattern.service_levels)
            data_services = set(decor_data["service_levels"])
            if pattern_services and data_services:
                similarity += len(pattern_services & data_services) / len(pattern_services | data_services)
            total_factors += 1

        # Similitud de servicios pre-boda
        if "pre_wedding_services" in decor_data:
            pattern_pre = set(pattern.pre_wedding_services)
            data_pre = set(decor_data["pre_wedding_services"])
            if pattern_pre and data_pre:
                similarity += len(pattern_pre & data_pre) / len(pattern_pre | data_pre)
            total_factors += 1

        # Similitud de servicios post-boda
        if "post_wedding_services" in decor_data:
            pattern_post = set(pattern.post_wedding_services)
            data_post = set(decor_data["post_wedding_services"])
            if pattern_post and data_post:
                similarity += len(pattern_post & data_post) / len(pattern_post | data_post)
            total_factors += 1

        # Similitud de servicios del día
        if "day_of_services" in decor_data:
            pattern_day = set(pattern.day_of_services)
            data_day = set(decor_data["day_of_services"])
            if pattern_day and data_day:
                similarity += len(pattern_day & data_day) / len(pattern_day | data_day)
            total_factors += 1

        # Similitud de estilos de arreglo
        if "arrangement_styles" in decor_data:
            pattern_styles = set(pattern.arrangement_styles)
            data_styles = set(decor_data["arrangement_styles"])
            if pattern_styles and data_styles:
                similarity += len(pattern_styles & data_styles) / len(pattern_styles | data_styles)
            total_factors += 1

        # Similitud de arreglos florales
        if "floral_arrangements" in decor_data:
            pattern_floral = set(pattern.floral_arrangements)
            data_floral = set(decor_data["floral_arrangements"])
            if pattern_floral and data_floral:
                similarity += len(pattern_floral & data_floral) / len(pattern_floral | data_floral)
            total_factors += 1

        # Similitud de decoraciones
        if "decorations" in decor_data:
            pattern_decorations = set(pattern.decorations)
            data_decorations = set(decor_data["decorations"])
            if pattern_decorations and data_decorations:
                similarity += len(pattern_decorations & data_decorations) / len(pattern_decorations | data_decorations)
            total_factors += 1

        # Similitud de artículos de papel
        if "paper_goods" in decor_data:
            pattern_paper = set(pattern.paper_goods)
            data_paper = set(decor_data["paper_goods"])
            if pattern_paper and data_paper:
                similarity += len(pattern_paper & data_paper) / len(pattern_paper | data_paper)
            total_factors += 1

        # Similitud de alquileres
        if "rentals" in decor_data:
            pattern_rentals = set(pattern.rentals)
            data_rentals = set(decor_data["rentals"])
            if pattern_rentals and data_rentals:
                similarity += len(pattern_rentals & data_rentals) / len(pattern_rentals | data_rentals)
            total_factors += 1

        # Similitud de rangos de precio
        if "estimated_cost" in decor_data and pattern.price_range[1] != float('inf'):
            if pattern.price_range[0] <= decor_data["estimated_cost"] <= pattern.price_range[1]:
                similarity += 1.0
            total_factors += 1

        # Similitud de rangos de invitados
        if "guest_count" in decor_data and pattern.guest_count_range[1] != float('inf'):
            if pattern.guest_count_range[0] <= decor_data["guest_count"] <= pattern.guest_count_range[1]:
                similarity += 1.0
            total_factors += 1

        # Similitud de restricciones
        if "restrictions" in decor_data:
            pattern_restrictions = set(pattern.restrictions)
            data_restrictions = set(decor_data["restrictions"])
            if pattern_restrictions and data_restrictions:
                similarity += len(pattern_restrictions & data_restrictions) / len(pattern_restrictions | data_restrictions)
            total_factors += 1

        # Si no hay factores, la similitud es 0.
        if total_factors == 0:
            return 0.0

        return similarity / total_factors

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
        
        for pattern in self.patterns.values():
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