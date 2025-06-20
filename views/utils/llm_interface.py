from typing import Dict, Any, Optional
import openai
import os
import json
from dotenv import load_dotenv

class LLMInterface:
    def __init__(self):
        """Initialize the LLM interface and OpenRouter client."""
        load_dotenv()
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "No se encontró la API key. Asegúrate de que el archivo .env existe y contiene OPENROUTER_API_KEY."
            )
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    
    def process_user_input(self, user_input: str, context: Optional[str] = None) -> str:
        """
        Process initial user input (plain text, possibly JSON-like) and extract structured information using the LLM.
        """
        
        prompt = f"""
        Eres un asistente experto en planificación de eventos. Tu tarea es analizar la siguiente entrada del usuario y extraer toda la información relevante, organizándola en una estructura JSON clara y anidada, siguiendo exactamente el formato de ejemplo proporcionado a continuación.

        - Usa como plantilla la siguiente estructura de criterios (puedes omitir campos para los que no haya información, pero incluye todos los subcampos relevantes si hay datos).
        - Completa tantos campos y subcampos como sea posible usando la información del usuario.
        - No inventes datos, pero sí infiere información si está implícita.
        - El resultado debe ser un único objeto JSON válido, sin comentarios ni texto adicional.
        - Si algún campo no tiene información, simplemente omítelo del resultado.

        Ejemplo de estructura (usa este formato para tu respuesta):

        {{
            "criterios": {{
                "presupuesto_total": {{
                    "type": "number",
                    "example": 50000,
                    "description": "Total budget for the event"
                }},
                "guest_count_general": {{
                    "type": "number",
                    "example": 100,
                    "description": "Number of guests"
                }},
                "general_style": {{
                    "type": "string",
                    "example": "luxury",
                    "description": "Event style (e.g., luxury, classic, etc.)"
                }},
                "venue": {{
                    "obligatorios_venue": {{
                        "type": "array of strings",
                        "example": ["venue_budget", "atmosphere", "venue_type"]
                    }},
                    "venue_budget": {{
                        "type": "number",
                        "example": "5000$",
                        "description": "part of the general budget destine to the venue"
                    }},
                    "venue_type": {{
                        "type": "string",
                        "example": "mansion",
                        "description": "Type of venue (e.g., mansion, ballroom, garden, etc.)"
                    }},
                    "location": {{
                        "type": "string",
                        "example": "Chicago, IL 60654"
                    }},
                    "venue_price": {{
                        "type": "object",
                        "example": {{
                            "space_rental": 20000,
                            "per_person": 210,
                            "other": []
                        }}
                    }},
                    "atmosphere": {{
                        "type": "string or array",
                        "example": ["Indoor", "Outdoor"]
                    }},
                    "venue_services": {{
                        "type": "array of strings",
                        "example": [
                            "Bar services",
                            "Catering services",
                            "Clean up",
                            "Dance floor"
                        ]
                    }},
                    "venue_restrictions": {{
                        "type": "string or array",
                        "example": "No outside alcohol allowed"
                    }},
                    "supported_events": {{
                        "type": "array of strings",
                        "example": [
                            "Wedding ceremony",
                            "Wedding reception"
                        ]
                    }},
                    "other_venue": {{
                        "type": "object",
                        "example": {{
                            "custom_field": "custom_value"
                        }}
                    }}
                }},
                "catering": {{
                    "obligatorios_catering": {{
                        "type": "array of strings",
                        "example": ["catering_budget", "meal_types", "dietary_options"]
                    }},
                    "catering_budget": {{
                        "type": "number",
                        "example": "5000$",
                        "description": "part of the general budget destine to the catering"
                    }},
                    "catering_services": {{
                        "type": "array of strings",
                        "example": [
                            "Bartenders",
                            "Cleanup and breakdown",
                            "Consultations and tastings"
                        ]
                    }},
                    "catering_ubication": {{
                        "type": "string",
                        "example": "Chicagoland region"
                    }},
                    "venue_price": {{
                        "type": "object",
                        "example": {{
                            "food": "$50 per person",
                            "bar_services": "$12 per person"
                        }}
                    }},
                    "cuisines": {{
                        "type": "array of strings",
                        "example": [
                            "Pan-Asian",
                            "Pan-European",
                            "Southern"
                        ]
                    }},
                    "dietary_options": {{
                        "type": "array of strings",
                        "example": [
                            "Dairy-free",
                            "Gluten-free",
                            "Nut-free",
                            "Vegan",
                            "Vegetarian"
                        ]
                    }},
                    "meal_types": {{
                        "type": "array of strings",
                        "example": [
                            "Buffet",
                            "Dessert service",
                            "Family-style meal",
                            "plated"
                        ]
                    }},
                    "beverage_services": {{
                        "type": "array of strings",
                        "example": [
                            "Bartending",
                            "Beverage servingware rentals"
                        ]
                    }},
                    "drink_types": {{
                        "type": "array of strings",
                        "example": [
                            "Beer",
                            "Wine",
                            "Non-alcoholic"
                        ]
                    }},
                    "catering_restrictions": {{
                        "type": "array of strings",
                        "example": [
                            "Not a gluten-free kitchen"
                        ]
                    }},
                    "other_catering": {{
                        "type": "object",
                        "example": {{
                            "custom_field": "custom_value"
                        }}
                    }}
                }},
                "decor": {{
                    "obligatorios_decor": {{
                        "type": "array of strings",
                        "example": ["decor_budget", "service_levels", "floral_arrangements"]
                    }},
                    "decore_budget": {{
                        "type": "number",
                        "example": "5000$",
                        "description": "part of the general budget destine to the decor"
                    }},
                    "decor_service_levels": {{
                        "type": "array of strings",
                        "example": [
                            "A La Carte",
                            "Full-Service Floral Design"
                        ]
                    }},
                    "pre_wedding_services": {{
                        "type": "array of strings",
                        "example": [
                            "Consultations",
                            "Event design",
                            "Mock-ups"
                        ]
                    }},
                    "post_wedding_services": {{
                        "type": "array of strings",
                        "example": [
                            "Cleanup",
                            "Flower preservation"
                        ]
                    }},
                    "day_of_services": {{
                        "type": "array of strings",
                        "example": [
                            "Container rentals",
                            "Decor rentals",
                            "Delivery"
                        ]
                    }},
                    "arrangement_styles": {{
                        "type": "array of strings",
                        "example": [
                            "Flower-forward with fresh blooms"
                        ]
                    }},
                    "floral_arrangements": {{
                        "type": "array of strings",
                        "example": [
                            "Bouquets",
                            "Centerpieces",
                            "Ceremony decor"
                        ]
                    }},
                    "restrictions_decor": {{
                        "type": "array of strings or string",
                        "example": [
                            "$2,000 minimum on all flower orders during May-October"
                        ]
                    }},
                    "decor_price": {{
                        "type": "object or string",
                        "example": {{
                            "bouquets": "start at $250",
                            "centerpieces": "start at $100",
                            "minimum_spend": "$3,000 total"
                        }}
                    }},
                    "decor_ubication": {{
                        "type": "string",
                        "example": "Milford, Connecticut"
                    }},
                    "other_decor": {{
                        "type": "object",
                        "example": {{
                            "custom_field": "custom_value"
                        }}
                    }}
                }}
            }}
        }}

        Entrada del usuario:
        {user_input}

        Contexto previo:
        {context if context else 'N/A'}

        Devuelve solo el objeto JSON resultante, sin ningún texto adicional.
        """
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error en process_user_input: {str(e)}")
            return "{}"


    def ask_for_more_details(self, necessary_data: list, useful_data: list, context: Optional[str] = None) -> str:
        """
        Ask the user for more details about missing fields, using plain text context (possibly JSON-like).
        """
        prompt = f"""
        Eres un asistente experto en planificación de eventos.

        Para continuar con la organización de tu evento y ofrecerte la mejor experiencia, necesito que me ayudes completando la siguiente información:

        - **Campos imprescindibles (necesarios para avanzar):**
        {', '.join(necessary_data)}

        - **Campos recomendados (opcionales, pero útiles para personalizar tu experiencia):**
        {', '.join(useful_data)}

        Contexto actual:
        {context if context else 'N/A'}

        Por favor, responde proporcionando la información de los campos imprescindibles. Si puedes, añade también los recomendados para que la planificación sea aún más precisa. Si tienes dudas sobre algún campo, házmelo saber y te lo explico con gusto.

        Redacta una pregunta clara, amable y motivadora para solicitar estos detalles al usuario.
        """
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error en ask_for_more_details: {str(e)}")
            return "No se pudo generar la solicitud de detalles."


    def unify_jsons(self, json1_text: str, json2_text: str) -> str:
        """
        Unify two JSON-like plain text summaries into a single plain text summary using the LLM.
        """
        prompt = f"""
        Eres un asistente experto en planificación de eventos. Tienes dos objetos en texto tipo JSON con información relevante:

        JSON 1:
        {json1_text}

        JSON 2:
        {json2_text}

        Tu tarea es fusionar ambos objetos en un único objeto JSON, siguiendo estas reglas:
        - Mantén exactamente la misma estructura de los objetos originales.
        - Si un campo existe en ambos, el valor de JSON 2 debe sobrescribir el de JSON 1.
        - Incluye todos los campos presentes en cualquiera de los dos objetos, sin inventar información nueva.
        - El resultado debe ser un único objeto JSON válido, sin texto adicional, sin explicaciones ni comentarios.

        Devuelve solo el objeto JSON resultante, sin ningún texto adicional.
        """
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error en unify_jsons_as_text: {str(e)}")
            return "No se pudo unificar los resúmenes."

    def json_to_natural_language(self, json_text: str) -> str:
        """
        Convert a JSON-like plain text summary into a natural language summary using the LLM.
        """
        prompt = f"""
                Eres un asistente de planificación de eventos. Dado el siguiente resumen en texto tipo JSON, elabora una descripción clara y amigable para el usuario:

                Resumen:
                {json_text}

                Devuelve solo el texto final sin ningún formato adicional.
                """
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error en json_to_natural_language: {str(e)}")
            return "No se pudo generar el resumen en lenguaje natural." 