from typing import Dict, Any, Optional
import openai
import os
import json
from dotenv import load_dotenv
from pydantic import ValidationError
from .models import ResponseModel, Criterios
from .prompts import TRANSFORM_INITIAL_QUERY_EN, ASK_FOR_MORE_DATA_EN, TRANSFORM_FROM_JSON_TO_NL_EN

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
        
        # Generate JSON schema from the Pydantic model
        schema = ResponseModel.model_json_schema()
        print(f"📋 Generated schema: {json.dumps(schema, indent=2)}")
        
        prompt = TRANSFORM_INITIAL_QUERY_EN(schema, user_input, context)
        
        try:
            response_text = self._make_llm_call(prompt)

            print(f"🤖 LLM Response: {response_text}")
            
            # Check if the response contains an error
            if "error" in response_text.lower() or "rate limit" in response_text.lower():
                error_msg = f"LLM service error: {response_text}"
                print(f"❌ LLM Error: {error_msg}")
                return json.dumps({"error": error_msg})
            
            # Clean the response to ensure it's a valid JSON string
            clean_response = self._clean_json_response(response_text)
            print(f"🧹 Cleaned response: {clean_response}")
            
            # Validate the response against the Pydantic model
            validated_data = ResponseModel.model_validate_json(clean_response)
            print(f"✅ Validation successful: {validated_data.model_dump_json(indent=2)}")
            
            return validated_data.model_dump_json(indent=2)

        except ValidationError as e:
            # Handle validation errors, maybe ask the user for clarification
            # For now, we'll just return an error message
            error_details = []
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_msg = f"Field '{field_path}': {error['msg']}"
                if "input" in error:
                    error_msg += f" (received: {error['input']})"
                error_details.append(error_msg)
            
            error_message = f"La respuesta del LLM no es válida. Detalles:\n" + "\n".join(error_details)
            print(f"❌ Validation error: {error_message}")
            return json.dumps({"error": error_message, "details": e.errors()})
        except Exception as e:
            error_msg = f"Ocurrió un error inesperado: {e}"
            print(f"❌ Unexpected error: {error_msg}")
            return json.dumps({"error": error_msg})

    def _clean_json_response(self, response_text: str) -> str:
        """
        Cleans the LLM's response to extract a valid JSON object.
        It removes markdown code blocks and trims whitespace.
        """
        # Find the start and end of the JSON object
        start_index = response_text.find('{')
        end_index = response_text.rfind('}')
        
        if start_index != -1 and end_index != -1:
            return response_text[start_index:end_index+1]
        
        # Fallback if no JSON object is found
        return "{}"

    def _make_llm_call(self, prompt: str) -> str:
        # This is a placeholder for your actual LLM call.
        # You would use self.client.chat.completions.create(...) here
        
        # For demonstration, I'll return a sample JSON based on the user input.
        # In a real scenario, this comes from the LLM.
        print("--- PROMPT ---")
        print(prompt)
        print("--- END PROMPT ---")

        # Simulate an LLM call
        completion = self.client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct:free",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        
        response = completion.choices[0].message.content
        print(response)
        return response or ""
        
    def check_missing_fields(self, criteria: Criterios) -> Dict[str, list]:
        """
        Checks for missing mandatory and useful fields in the criteria based on fields.txt logic.
        Returns a dictionary with missing fields.
        """
        necessary_fields = [
            "presupuesto", "guest_count", "venue", "catering"
        ]
        useful_fields = [
            "style", "decor", "venue.atmosphere", "venue.type", 
            "venue.services", "catering.services", "catering.dietary_options",
            "catering.meal_types", "decor.floral_arrangements", "decor.restrictions"
        ]

        missing_fields = {
            "obligatorios": [],
            "utiles": []
        }

        def check_field(path: str, model: Criterios):
            parts = path.split('.')
            value = model
            for part in parts:
                if value is None:
                    return True # Is missing
                value = getattr(value, part, None)
            return value is None

        for field_path in necessary_fields:
            if check_field(field_path, criteria):
                missing_fields["obligatorios"].append(field_path)
        
        for field_path in useful_fields:
            if check_field(field_path, criteria):
                missing_fields["utiles"].append(field_path)
            
        return missing_fields
    
    def ask_for_more_details(self, missing_fields: Dict[str, list], context: Optional[str] = None) -> str:
        """
        Ask the user for more details about missing fields, using plain text context (possibly JSON-like).
        """
        prompt = ASK_FOR_MORE_DATA_EN(missing_fields, context)
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
        prompt = TRANSFORM_FROM_JSON_TO_NL_EN(json_text)
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error en json_to_natural_language: {str(e)}")
            return "No se pudo generar el resumen en lenguaje natural." 