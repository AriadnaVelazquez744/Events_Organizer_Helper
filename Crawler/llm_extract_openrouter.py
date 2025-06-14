
# extractors/llm_extract_openrouter.py
import openai
import json
import re
import requests
import time
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"  # puedes usar también "llama3-70b-8192"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

client = openai.OpenAI(
   api_key = os.getenv("OPENROUTER_API_KEY"),
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

def llm_extract_openrouter(
    html: str,
    url: str = "",
    prompt_template: str = "",
    model: str = "meta-llama/llama-3.3-70b-instruct:free"
) -> dict:
    print("[LLM EXTRACT] Limpieza HTML...")
    soup = clean_html_soup(html)
    relevant_text = soup.get_text(separator=" ", strip=True)

    prompt = prompt_template.format(text=relevant_text, url=url)
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    try:
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
        rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
        rate_limit_limit = response.headers.get("X-RateLimit-Limit")
        retry_after = response.headers.get("Retry-After")
    
        print(f"Límite: {rate_limit_limit} | Restantes: {rate_limit_remaining} | {retry_after}")
        result = response.json()
        print(response)
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # response = client.chat.completions.create(
        #     model=model,
        #     messages=[{"role": "user", "content": prompt}],
        # )


        # content = response.choices[0].message.content
        print(f"[LLM RESPONSE] {content}")
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()
            
        parsed = extract_json_from_response(content)
            
        return parsed
        # return json.loads(content)
    
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
        
def extract_json_from_response(text: str) -> dict:
    """
    Extrae el contenido entre los primeros delimitadores ``` y lo convierte en JSON válido.
    Si no hay delimitadores, intenta extraer desde el primer { hasta el último }.
    """

    try:
        # Extraer entre los primeros bloques de ```
        if "```" in text:
            parts = text.split("```")
            json_candidate = parts[1] if len(parts) > 1 else parts[0]
        else:
            # Fallback: desde la primera llave abierta hasta la última cerrada
            match = re.search(r"\{[\s\S]*\}", text)
            if not match:
                raise ValueError("No se encontró un bloque JSON válido.")
            json_candidate = match.group(0)

        # Limpieza básica
        json_candidate = json_candidate.strip()
        json_candidate = re.sub(r",\s*([\]}])", r"\1", json_candidate)
        json_candidate = json_candidate.replace("“", "\"").replace("”", "\"").replace("’", "'")

        return json.loads(json_candidate)

    except Exception as e:
        print(f"[ERROR extract_json_from_response] {e}")
        return {
            "title": "ERROR",
            "capacity": None,
            "location": None,
            "price": None,
            "atmosphere": None,
            "venue_type": None,
            "services": [],
            "restrictions": [],
            "supported_events": [],
            "outlinks": []
        }
