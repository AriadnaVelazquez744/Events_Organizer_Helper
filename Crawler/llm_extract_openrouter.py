
# extractors/llm_extract_openrouter.py
import openai
import json
from bs4 import BeautifulSoup

client = openai.OpenAI(
   api_key = "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",
   base_url = "https://openrouter.ai/api/v1"
)

def clean_html_soup(html: str):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "form", "footer", "svg", "noscript"]):
        tag.decompose()
    return soup

def extract_relevant_text(soup: BeautifulSoup):
    parts = []
    if soup.title:
        parts.append(soup.title.get_text(strip=True))

    for tag in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'section']):
        text = tag.get_text(strip=True)
        if len(text) > 20:
            parts.append(text)
        # if sum(len(p) for p in parts) > max_length:
        #     break

    return "\n".join(parts)

def llm_extract_openrouter(html: str, url: str = "") -> dict:
    soup = clean_html_soup(html)
    relevant_text = soup.get_text

    prompt = f"""
Extrae del siguiente texto los datos de un lugar para eventos si el texto solo menciona un lugar:

- Nombre del lugar
- Capacidad (número de personas)
- Extrae la información de precios dividiendo en:

- "alquiler_espacio": precio fijo por alquilar el lugar (por evento o por día), cualquier cosa que empiece por "starting at ..."
- "por_persona": precio por persona, si aplica
- "otros": cualquier precio adicional mencionado

Incluye también notas o condiciones especiales (por ejemplo, si es solo para ciertas fechas).

Devuelve un subJSON con esta estructura:

  "precio": 
    "alquiler_espacio": 3500,
    "por_persona": 41,
    "otros": [],
    "notas": "..."
  

- Si es interior, exterior o ambos(cuando sea ambos devuelve los dos valores )
- Tipo de local (hotel, playa, granja, etc.)
- Servicios incluidos
- Restricciones del lugar
- Tipos de eventos compatibles
- URLs en el texto que parezcan corresponder a otros lugares similares

Si el texto menciona varios lugares solo busca y extrae URLs en todo el texto aunque no aparezcan donde se menciona un lugar

Devuelve un JSON con estas claves exactas:
"title", "capacidad", "precio", "ambiente", "tipo_local", "servicios", "restricciones", "eventos_compatibles", "outlinks"


Texto:
{relevant_text}
"""

    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[{"role": "user", "content": prompt}],
            response_format="json"
        )
        content = response.choices[0].message.content
        
        print(f"[LLM RESPONSE] {content}")
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()
            
        return json.loads(content)
    
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return {
            "title": "ERROR",
            "capacidad": None,
            "precio": None,
            "ambiente": None,
            "tipo_local": None,
            "servicios": [],
            "restricciones": [],
            "eventos_compatibles": [],
            "outlinks": []
        }