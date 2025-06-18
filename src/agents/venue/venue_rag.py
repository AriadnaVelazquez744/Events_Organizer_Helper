from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Dict, Any
import json
import os

@dataclass
class VenuePattern:
    style: str
    title: str
    capacity_range: Tuple[int, int]
    location: str
    price_range: Tuple[float, float]
    atmosphere: List[str]
    venue_type: List[str]
    services: List[str]
    restrictions: List[str]
    supported_events: List[str]
    outlinks: List[str]
    success_rate: float
    last_used: str
    usage_count: int

class VenueRAG:
    def __init__(self, knowledge_file: str = "venue_graph.json"):
        self.knowledge_file = knowledge_file
        self.patterns: Dict[str, VenuePattern] = {}
        self._load_knowledge()

    def _load_knowledge(self):
        if os.path.exists(self.knowledge_file):
            try:
                with open(self.knowledge_file, 'r') as f:
                    data = json.load(f)
                    for key, pattern_data in data.items():
                        self.patterns[key] = VenuePattern(
                            style=pattern_data["style"],
                            title=pattern_data.get("title", ""),
                            capacity_range=tuple(pattern_data["capacity_range"]),
                            location=pattern_data["location"],
                            price_range=tuple(pattern_data["price_range"]),
                            atmosphere=pattern_data.get("atmosphere", []),
                            venue_type=pattern_data.get("venue_type", []),
                            services=pattern_data.get("services", []),
                            restrictions=pattern_data.get("restrictions", []),
                            supported_events=pattern_data.get("supported_events", []),
                            outlinks=pattern_data.get("outlinks", []),
                            success_rate=pattern_data["success_rate"],
                            last_used=pattern_data["last_used"],
                            usage_count=pattern_data["usage_count"]
                        )
            except Exception as e:
                print(f"[VenueRAG] Error cargando conocimiento: {str(e)}")
                self.patterns = {}

    def _save_knowledge(self):
        try:
            data = {
                key: {
                    "style": pattern.style,
                    "title": pattern.title,
                    "capacity_range": list(pattern.capacity_range),
                    "location": pattern.location,
                    "price_range": list(pattern.price_range),
                    "atmosphere": pattern.atmosphere,
                    "venue_type": pattern.venue_type,
                    "services": pattern.services,
                    "restrictions": pattern.restrictions,
                    "supported_events": pattern.supported_events,
                    "outlinks": pattern.outlinks,
                    "success_rate": pattern.success_rate,
                    "last_used": pattern.last_used,
                    "usage_count": pattern.usage_count
                }
                for key, pattern in self.patterns.items()
            }
            with open(self.knowledge_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[VenueRAG] Error guardando conocimiento: {str(e)}")

    def get_venue_recommendation(self, budget: float, guest_count: int, style: str = "classic", location: str = "") -> Dict:
        """Obtiene recomendaciones de venue basadas en el presupuesto y requisitos."""
        # Mapeo de estilos a características recomendadas
        style_characteristics = {
            "classic": {
                "atmosphere": ["Elegant", "Traditional", "Sophisticated", "Indoor", "Formal"],
                "venue_type": ["Ballroom", "Hotel", "Country Club", "Golf and Country Club", "Club"],
                "services": ["Full-Service Venue", "Event Coordination", "Catering", "Bar Service", "Bar services", "Catering services"],
                "supported_events": ["Wedding Ceremony", "Wedding Reception", "Rehearsal Dinner"],
                "restrictions": []
            },
            "modern": {
                "atmosphere": ["Contemporary", "Minimalist", "Urban", "Modern", "Indoor"],
                "venue_type": ["Modern Venue", "Loft", "Gallery", "Rooftop", "Event Space"],
                "services": ["Modern Venue", "Tech Support", "AV Equipment", "Flexible Layout", "Event rentals"],
                "supported_events": ["Wedding Ceremony", "Wedding Reception", "Corporate Events"],
                "restrictions": []
            },
            "rustic": {
                "atmosphere": ["Rustic", "Natural", "Countryside", "Outdoor", "Barn"],
                "venue_type": ["Barn", "Farm", "Vineyard", "Garden", "Outdoor Venue"],
                "services": ["Rustic Venue", "Outdoor Spaces", "Natural Settings", "Parking", "Event rentals"],
                "supported_events": ["Wedding Ceremony", "Wedding Reception", "Outdoor Events"],
                "restrictions": ["Weather Dependent"]
            },
            "luxury": {
                "atmosphere": ["Luxurious", "Opulent", "Exclusive", "Elegant", "Sophisticated"],
                "venue_type": ["Luxury Hotel", "Mansion", "Private Estate", "Resort", "Country Club"],
                "services": ["Luxury Venue", "VIP Services", "Concierge", "Premium Catering", "Event coordinator"],
                "supported_events": ["Wedding Ceremony", "Wedding Reception", "Luxury Events"],
                "restrictions": ["Minimum Guest Count", "Premium Pricing"]
            }
        }
        
        # Obtener características recomendadas basadas en el estilo
        style_lower = style.lower()
        style_data = style_characteristics.get(style_lower, style_characteristics["classic"])
        
        print(f"[VenueRAG] Estilo solicitado: '{style}' (normalizado a '{style_lower}')")
        print(f"[VenueRAG] Usando características para estilo: {style_lower}")
        
        recommended_characteristics = {
            "atmosphere": style_data["atmosphere"],
            "venue_type": style_data["venue_type"],
            "services": style_data["services"],
            "supported_events": style_data["supported_events"],
            "restrictions": style_data["restrictions"]
        }
        
        # Calcular capacidad recomendada: guest_count +/- 20%
        capacity_range = (int(guest_count * 0.8), int(guest_count * 1.2))
        
        # Calcular precio recomendado: budget +/- 20%
        price_range = (budget * 0.8, budget * 1.2)
        
        # Ajustar recomendaciones basadas en el presupuesto
        if budget < 5000:
            # Reducir servicios para presupuestos bajos
            for key in recommended_characteristics:
                if isinstance(recommended_characteristics[key], list):
                    recommended_characteristics[key] = recommended_characteristics[key][:2]
        elif budget < 10000:
            # Servicios moderados
            for key in recommended_characteristics:
                if isinstance(recommended_characteristics[key], list):
                    recommended_characteristics[key] = recommended_characteristics[key][:3]
        
        return {
            "style": style,
            "location": location,
            "capacity_range": capacity_range,
            "price_range": price_range,
            **recommended_characteristics
        }

    def update_success_pattern(self, pattern_data: Dict, success: bool):
        """Actualiza los patrones de éxito basados en los resultados."""
        key = f"{pattern_data['style']}_{pattern_data['location']}_{pattern_data['capacity_range'][0]}_{pattern_data['price_range'][0]}"
        
        if key not in self.patterns:
            self.patterns[key] = VenuePattern(
                style=pattern_data["style"],
                title=pattern_data.get("title", ""),
                capacity_range=tuple(pattern_data["capacity_range"]),
                location=pattern_data["location"],
                price_range=tuple(pattern_data["price_range"]),
                atmosphere=pattern_data.get("atmosphere", []),
                venue_type=pattern_data.get("venue_type", []),
                services=pattern_data.get("services", []),
                restrictions=pattern_data.get("restrictions", []),
                supported_events=pattern_data.get("supported_events", []),
                outlinks=pattern_data.get("outlinks", []),
                success_rate=1.0 if success else 0.0,
                last_used=datetime.now().isoformat(),
                usage_count=1
            )
        else:
            pattern = self.patterns[key]
            pattern.success_rate = (pattern.success_rate * pattern.usage_count + (1.0 if success else 0.0)) / (pattern.usage_count + 1)
            pattern.usage_count += 1
            pattern.last_used = datetime.now().isoformat()
            
            # Actualizar rangos de precio y capacidad
            if pattern_data.get("price_range"):
                current_min, current_max = pattern.price_range
                new_min, new_max = pattern_data["price_range"]
                pattern.price_range = (min(current_min, new_min), max(current_max, new_max))
            
            if pattern_data.get("capacity_range"):
                cmin, cmax = pattern.capacity_range
                nmin, nmax = pattern_data["capacity_range"]
                pattern.capacity_range = (min(cmin, nmin), max(cmax, nmax))

        self._save_knowledge()

    def get_similar_cases(self, venue_data: Dict) -> List[Tuple[VenuePattern, float]]:
        """Encuentra casos similares basados en los datos proporcionados."""
        similar_cases = []
        
        for pattern in self.patterns.values():
            similarity = self._calculate_similarity(pattern, venue_data)
            if similarity > 0.5:  # Solo incluir casos con similitud significativa
                similar_cases.append((pattern, similarity))
        
        return sorted(similar_cases, key=lambda x: x[1], reverse=True)

    def _calculate_similarity(self, pattern: VenuePattern, venue_data: Dict) -> float:
        """Calcula la similitud entre un patrón y los datos de venue."""
        similarity = 0.0
        total_factors = 0

        # Similitud de estilo
        if pattern.style == venue_data.get("style"):
            similarity += 1.0
        total_factors += 1

        # Similitud de ubicación
        if pattern.location == venue_data.get("location"):
            similarity += 1.0
        total_factors += 1

        # Similitud de capacidad
        if "capacity" in venue_data:
            cap = venue_data["capacity"]
            if pattern.capacity_range[0] <= cap <= pattern.capacity_range[1]:
                similarity += 1.0
            total_factors += 1

        # Similitud de precio
        if "price" in venue_data:
            price = venue_data["price"]
            if pattern.price_range[0] <= price <= pattern.price_range[1]:
                similarity += 1.0
            total_factors += 1

        # Similitud de ambiente
        if "atmosphere" in venue_data:
            pattern_atmosphere = set(pattern.atmosphere)
            data_atmosphere = set(venue_data["atmosphere"])
            if pattern_atmosphere and data_atmosphere:
                similarity += len(pattern_atmosphere & data_atmosphere) / len(pattern_atmosphere | data_atmosphere)
            total_factors += 1

        # Similitud de tipo de venue
        if "venue_type" in venue_data:
            pattern_types = set(pattern.venue_type)
            data_types = set(venue_data["venue_type"])
            if pattern_types and data_types:
                similarity += len(pattern_types & data_types) / len(pattern_types | data_types)
            total_factors += 1

        # Similitud de servicios
        if "services" in venue_data:
            pattern_services = set(pattern.services)
            data_services = set(venue_data["services"])
            if pattern_services and data_services:
                similarity += len(pattern_services & data_services) / len(pattern_services | data_services)
            total_factors += 1

        # Similitud de restricciones
        if "restrictions" in venue_data:
            pattern_restrictions = set(pattern.restrictions)
            data_restrictions = set(venue_data["restrictions"])
            if pattern_restrictions and data_restrictions:
                similarity += len(pattern_restrictions & data_restrictions) / len(pattern_restrictions | data_restrictions)
            total_factors += 1

        # Similitud de eventos soportados
        if "supported_events" in venue_data:
            pattern_events = set(pattern.supported_events)
            data_events = set(venue_data["supported_events"])
            if pattern_events and data_events:
                similarity += len(pattern_events & data_events) / len(pattern_events | data_events)
            total_factors += 1

        # Similitud de outlinks
        if "outlinks" in venue_data:
            pattern_outlinks = set(pattern.outlinks)
            data_outlinks = set(venue_data["outlinks"])
            if pattern_outlinks and data_outlinks:
                similarity += len(pattern_outlinks & data_outlinks) / len(pattern_outlinks | data_outlinks)
            total_factors += 1

        # Si no hay factores, la similitud es 0.
        if total_factors == 0:
            return 0.0

        return similarity / total_factors

    def suggest_conflict_resolution(self, conflict_type: str, context: Dict[str, Any]) -> List[str]:
        """Sugiere estrategias para resolver conflictos comunes."""
        strategies = {
            "budget_conflict": [
                "Considerar venues en ubicaciones menos costosas",
                "Reducir el número de invitados",
                "Buscar venues que permitan catering externo",
                "Considerar fechas fuera de temporada"
            ],
            "capacity_conflict": [
                "Buscar venues con capacidad flexible",
                "Considerar múltiples espacios en el mismo venue",
                "Reducir la lista de invitados",
                "Buscar venues con opciones de expansión"
            ],
            "location_conflict": [
                "Expandir la búsqueda a áreas cercanas",
                "Considerar venues con buena conectividad",
                "Buscar opciones de transporte para invitados",
                "Evaluar venues en ubicaciones alternativas"
            ]
        }
        
        return strategies.get(conflict_type, ["Revisar y ajustar los requisitos del venue"])

    def find_similar_cases(self, style: str, guest_count: int, 
                          budget: float, location: str = "") -> List[Dict]:
        """Encuentra casos similares basados en estilo, cantidad de invitados, presupuesto y ubicación."""
        similar_cases = []
        
        for pattern in self.patterns.values():
            # Calcula similitud en estilo
            style_similarity = 1.0 if pattern.style == style else 0.0
            
            # Calcula similitud en ubicación
            location_similarity = 1.0 if pattern.location == location else 0.0
            
            # Calcula similitud en cantidad de invitados
            guest_similarity = 1.0 - min(
                abs(guest_count - (pattern.capacity_range[0] + pattern.capacity_range[1]) / 2) / 
                max(guest_count, (pattern.capacity_range[0] + pattern.capacity_range[1]) / 2),
                1.0
            )
            
            # Calcula similitud en presupuesto
            budget_similarity = 1.0 - min(
                abs(budget - (pattern.price_range[0] + pattern.price_range[1]) / 2) / 
                max(budget, (pattern.price_range[0] + pattern.price_range[1]) / 2),
                1.0
            )
            
            # Calcula similitud total (promedio ponderado)
            total_similarity = (style_similarity * 0.3 + 
                              location_similarity * 0.2 + 
                              guest_similarity * 0.25 + 
                              budget_similarity * 0.25)
            
            if total_similarity > 0.5:  # Solo incluir casos con similitud significativa
                similar_cases.append({
                    "pattern": pattern,
                    "similarity": total_similarity
                })
        
        # Ordenar por similitud
        similar_cases.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_cases 