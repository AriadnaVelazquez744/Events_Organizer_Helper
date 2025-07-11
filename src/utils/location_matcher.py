# src/utils/location_matcher.py

# Mapeo completo de estados de USA y sus acrónimos
US_STATES_MAPPING = {
    # Estados con sus acrónimos oficiales
    "alabama": ["al"],
    "alaska": ["ak"],
    "arizona": ["az"],
    "arkansas": ["ar"],
    "california": ["ca"],
    "colorado": ["co"],
    "connecticut": ["ct"],
    "delaware": ["de"],
    "florida": ["fl"],
    "georgia": ["ga"],
    "hawaii": ["hi"],
    "idaho": ["id"],
    "illinois": ["il"],
    "indiana": ["in"],
    "iowa": ["ia"],
    "kansas": ["ks"],
    "kentucky": ["ky"],
    "louisiana": ["la"],
    "maine": ["me"],
    "maryland": ["md"],
    "massachusetts": ["ma"],
    "michigan": ["mi"],
    "minnesota": ["mn"],
    "mississippi": ["ms"],
    "missouri": ["mo"],
    "montana": ["mt"],
    "nebraska": ["ne"],
    "nevada": ["nv"],
    "new hampshire": ["nh"],
    "new jersey": ["nj"],
    "new mexico": ["nm"],
    "new york": ["ny"],
    "north carolina": ["nc"],
    "north dakota": ["nd"],
    "ohio": ["oh"],
    "oklahoma": ["ok"],
    "oregon": ["or"],
    "pennsylvania": ["pa"],
    "rhode island": ["ri"],
    "south carolina": ["sc"],
    "south dakota": ["sd"],
    "tennessee": ["tn"],
    "texas": ["tx"],
    "utah": ["ut"],
    "vermont": ["vt"],
    "virginia": ["va"],
    "washington": ["wa"],
    "west virginia": ["wv"],
    "wisconsin": ["wi"],
    "wyoming": ["wy"],
    
    # Distrito de Columbia
    "district of columbia": ["dc", "washington dc"],
    "washington dc": ["dc", "district of columbia"],
    
    # Territorios
    "american samoa": ["as"],
    "guam": ["gu"],
    "northern mariana islands": ["mp"],
    "puerto rico": ["pr"],
    "u.s. virgin islands": ["vi"],
    "virgin islands": ["vi", "u.s. virgin islands"],
}

def normalize_location(location: str) -> str:
    """
    Normaliza una ubicación convirtiendo a minúsculas y eliminando espacios extra
    """
    if not location:
        return ""
    return location.lower().strip()

def expand_location_variants(location: str) -> list:
    """
    Expande una ubicación a todas sus variantes posibles (nombre completo, acrónimos, etc.)
    """
    if not location:
        return []
    
    normalized = normalize_location(location)
    variants = [normalized]
    
    # Buscar en el mapeo de estados
    for state_name, abbreviations in US_STATES_MAPPING.items():
        if normalized == state_name:
            # Si es el nombre completo, agregar todos los acrónimos
            variants.extend(abbreviations)
        elif normalized in abbreviations:
            # Si es un acrónimo, agregar el nombre completo y otros acrónimos
            variants.append(state_name)
            variants.extend([abbr for abbr in abbreviations if abbr != normalized])
    
    return list(set(variants))  # Eliminar duplicados

def location_matches(target_location: str, venue_location: str) -> bool:
    """
    Verifica si una ubicación objetivo coincide con la ubicación de un venue
    """
    if not target_location or not venue_location:
        return False
    
    # Normalizar ambas ubicaciones
    target_normalized = normalize_location(target_location)
    venue_normalized = normalize_location(venue_location)
    
    # Coincidencia directa
    if target_normalized == venue_normalized:
        print(f"[LocationMatcher] ✅ Coincidencia directa: '{target_location}' = '{venue_location}'")
        return True
    
    # Obtener todas las variantes del objetivo
    target_variants = expand_location_variants(target_location)
    
    # Dividir la ubicación del venue en palabras para búsqueda más precisa
    venue_words = venue_normalized.split()
    
    # Verificar si alguna variante del objetivo coincide con alguna palabra del venue
    for variant in target_variants:
        if variant in venue_words:
            print(f"[LocationMatcher] ✅ Coincidencia por palabra: '{target_location}' (variante '{variant}') en '{venue_location}'")
            return True
    
    # Verificar si alguna palabra del venue es una variante válida
    venue_variants = expand_location_variants(venue_location)
    for venue_word in venue_words:
        if venue_word in venue_variants:
            print(f"[LocationMatcher] ✅ Coincidencia por palabra del venue: '{venue_location}' (palabra '{venue_word}') con '{target_location}'")
            return True
    
    # Verificar coincidencias exactas en el texto completo (para casos como "Alaska" en "Beautiful Alaska venue")
    for variant in target_variants:
        # Buscar la variante como palabra completa, no como subcadena
        import re
        pattern = r'\b' + re.escape(variant) + r'\b'
        if re.search(pattern, venue_normalized):
            print(f"[LocationMatcher] ✅ Coincidencia por regex: '{target_location}' (variante '{variant}') en '{venue_location}'")
            return True
    
    print(f"[LocationMatcher] ❌ No hay coincidencia: '{target_location}' vs '{venue_location}'")
    return False

def get_location_display_name(location: str) -> str:
    """
    Obtiene el nombre de visualización estándar para una ubicación
    """
    if not location:
        return ""
    
    normalized = normalize_location(location)
    
    # Buscar el nombre completo en el mapeo
    for state_name, abbreviations in US_STATES_MAPPING.items():
        if normalized == state_name or normalized in abbreviations:
            return state_name.title()
    
    # Si no se encuentra, devolver la ubicación original con formato
    return location.title()

def is_valid_us_location(location: str) -> bool:
    """
    Verifica si una ubicación es válida en USA
    """
    if not location:
        return False
    
    normalized = normalize_location(location)
    
    # Verificar si está en el mapeo de estados
    for state_name, abbreviations in US_STATES_MAPPING.items():
        if normalized == state_name or normalized in abbreviations:
            return True
    
    return False 