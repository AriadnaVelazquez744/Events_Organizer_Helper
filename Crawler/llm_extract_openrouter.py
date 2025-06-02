
# extractors/llm_extract_openrouter.py
import openai
import json
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

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
    model: str = "deepseek/deepseek-chat-v3-0324:free"
) -> dict:
    print("[LLM EXTRACT] Limpieza HTML...")
    soup = clean_html_soup(html)
    relevant_text = soup.get_text(separator=" ", strip=True)

    prompt = prompt_template.format(text=relevant_text, url=url)

    try:
        response = client.chat.completions.create(
            model=model,
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