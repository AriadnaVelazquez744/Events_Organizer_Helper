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
MODEL = "llama-3.3-70b-versatile"  

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

    # Verificar que el prompt template tenga la variable {text}
    if "{text}" not in prompt_template:
        print("[LLM EXTRACT] Error: prompt_template debe contener {text}")
        return {}

    prompt = prompt_template.format(text=relevant_text, url=url)
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    try:
        # response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
        # rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
        # rate_limit_limit = response.headers.get("X-RateLimit-Limit")
        # retry_after = response.headers.get("Retry-After")
    
        # print(f"Límite: {rate_limit_limit} | Restantes: {rate_limit_remaining} | {retry_after}")
        # result = response.json()
        # print(response)
        # result = response.json()
        # content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )


        content = response.choices[0].message.content
        print(f"[LLM RESPONSE] {content}")
        
        # Limpiar respuesta si está en formato markdown
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()
            
        # Intentar extraer JSON de la respuesta
        try:
            parsed = extract_json_from_response(content)
            if parsed and isinstance(parsed, dict):
                return parsed
            else:
                    # Si extract_json_from_response falla, intentar parsear directamente
                return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"[LLM EXTRACT] Error parsing JSON: {str(e)}")
            print(f"[LLM EXTRACT] Content: {content[:500]}...")
            return {}
        except Exception as e:
            print(f"[LLM EXTRACT] Error general: {str(e)}")
            return {}
    
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return {}
        
def extract_json_from_response(text: str) -> dict:
    """
    Extrae el contenido entre los primeros delimitadores ``` y lo convierte en JSON válido.
    Si no hay delimitadores, intenta extraer desde el primer { hasta el último }.
    """

    try:
        # Limpiar el texto
        text = text.strip()
        
        # Extraer entre los primeros bloques de ```
        if "```" in text:
            parts = text.split("```")
            json_candidate = parts[1] if len(parts) > 1 else parts[0]
        else:
            # Fallback: desde la primera llave abierta hasta la última cerrada
            match = re.search(r"\{[\s\S]*\}", text)
            if not match:
                print("[EXTRACT JSON] No se encontró un bloque JSON válido")
                return {}
            json_candidate = match.group(0)

        # Limpieza básica
        json_candidate = json_candidate.strip()
        
        # Remover líneas que solo contienen espacios y llaves
        lines = json_candidate.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('"') and not line.startswith('{') and not line.startswith('}'):
                continue
            cleaned_lines.append(line)
        
        json_candidate = '\n'.join(cleaned_lines)
        
        # Limpiar comas extra al final
        json_candidate = re.sub(r",\s*([\]}])", r"\1", json_candidate)
        
        # Reemplazar comillas inteligentes
        json_candidate = json_candidate.replace(""", "\"").replace(""", "\"").replace("'", "'")
        
        # Intentar parsear
        result = json.loads(json_candidate)
        
        # Verificar que sea un diccionario
        if isinstance(result, dict):
            return result
        else:
            print(f"[EXTRACT JSON] Resultado no es un diccionario: {type(result)}")
            return {}

    except json.JSONDecodeError as e:
        print(f"[EXTRACT JSON] Error de JSON: {e}")
        print(f"[EXTRACT JSON] JSON candidato: {json_candidate[:200]}...")
        return {}
    except Exception as e:
        print(f"[EXTRACT JSON] Error general: {e}")
        return {}
