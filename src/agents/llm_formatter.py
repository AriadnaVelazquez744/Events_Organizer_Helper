import openai
import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Verificar la API key
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError(
        "No se encontró la API key. Asegúrate de que:\n"
        "1. El archivo .env existe en la raíz del proyecto\n"
        "2. Contiene la variable OPENROUTER_API_KEY\n"
        "3. El valor de la API key es correcto"
    )

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

def generar_resumen_natural(resumen: Dict[str, Any]) -> str:
    """Genera un resumen en lenguaje natural del estado actual del plan."""
    prompt = f"""
Eres un planificador de bodas profesional. Dado el siguiente resumen en JSON, elabora una descripción amigable y detallada para el cliente:

Resumen:
{json.dumps(resumen, indent=2, ensure_ascii=False)}

Considera los siguientes aspectos en tu respuesta:
1. Estado general del plan
2. Elementos completados y pendientes
3. Presupuesto utilizado
4. Conflictos o advertencias si existen
5. Próximos pasos recomendados

Devuelve solo el texto final sin ningún formato adicional.
"""

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct:free",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error en generar_resumen_natural: {str(e)}")
        return "No se pudo generar el resumen en lenguaje natural."

def formatear_correccion(correccion: Dict[str, Any]) -> str:
    """Formatea una solicitud de corrección en lenguaje natural."""
    prompt = f"""
Eres un planificador de bodas profesional. Dado el siguiente resumen de corrección, elabora una descripción clara de los cambios solicitados:

Corrección:
{json.dumps(correccion, indent=2, ensure_ascii=False)}

Considera los siguientes aspectos en tu respuesta:
1. Cambios específicos solicitados
2. Impacto en el plan actual
3. Elementos que necesitan ser recalculados
4. Consideraciones importantes

Devuelve solo el texto final sin ningún formato adicional.
"""

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct:free",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error en formatear_correccion: {str(e)}")
        return "No se pudo formatear la corrección."

def formatear_conflicto(conflicto: Dict[str, Any]) -> str:
    """Formatea un conflicto en lenguaje natural."""
    prompt = f"""
Eres un planificador de bodas profesional. Dado el siguiente conflicto, elabora una explicación clara y una sugerencia de solución:

Conflicto:
{json.dumps(conflicto, indent=2, ensure_ascii=False)}

Considera los siguientes aspectos en tu respuesta:
1. Naturaleza del conflicto
2. Elementos afectados
3. Posibles soluciones
4. Recomendaciones

Devuelve solo el texto final sin ningún formato adicional.
"""

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct:free",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error en formatear_conflicto: {str(e)}")
        return "No se pudo formatear el conflicto."

def formatear_presupuesto(presupuesto: Dict[str, Any]) -> str:
    """Formatea la distribución del presupuesto en lenguaje natural."""
    prompt = f"""
Eres un planificador de bodas profesional. Dado el siguiente resumen de presupuesto, elabora una explicación clara de la distribución:

Presupuesto:
{json.dumps(presupuesto, indent=2, ensure_ascii=False)}

Considera los siguientes aspectos en tu respuesta:
1. Distribución por categoría
2. Porcentajes del total
3. Justificación de la distribución
4. Recomendaciones de ajuste si es necesario

Devuelve solo el texto final sin ningún formato adicional.
"""

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct:free",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error en formatear_presupuesto: {str(e)}")
        return "No se pudo formatear el presupuesto."
