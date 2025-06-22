import json

def TRANSFORM_INITIAL_QUERY_EN(schema, user_input, context): 

    return f"""
    You are an expert event planning assistant. Your task is to analyze the following user input and extract all relevant information, organizing it into a JSON structure that adheres to the following JSON schema.

    IMPORTANT FORMAT REQUIREMENTS:
    - Use the following criteria structure as a template (you can omit fields for which there is no information, but include all relevant subfields if there is data).
    - Complete as many fields and subfields as possible using the user's information.
    - Do not invent data, but do infer information if it is implicit.
    - The result must be a single valid JSON object, without comments or additional text.
    - If any field has no information, simply omit it from the result.
    
    CRITICAL FORMAT RULES:
    1. For fields that expect arrays (like "atmosphere", "cuisines", "dietary_options"), always use array format: ["value1", "value2"]
    2. For enum fields, only use the exact values specified in the schema:
       - Cuisines: only "Pan-Asian", "Pan-European", "Southern", "Latin American", "American", "BBQ", "Italian", or associate as close as possible
       - Dietary options: only "Dairy-free", "Gluten-free", "Nut-free", "Vegan", "Vegetarian", or associate as close as possible
       - Atmosphere: only "Indoor", "Outdoor", "Rustic Chic", or what is infer from what the user ask.
    3. If a user mentions dietary preferences like "vegan", put it in "dietary_options", not "cuisines"
    4. If a user mentions location type like "outside", put it in "venue.atmosphere" as ["Outdoor"]

    JSON Schema:
    {json.dumps(schema, indent=2)}

    User Input:
    {user_input}

    Previous Context:
    {context if context else 'N/A'}

    Return only the resulting JSON object, without any additional text.
    """

def TRANSFORM_INITIAL_QUERY(schema, user_input, context):
    return f"""
    Eres un asistente experto en planificación de eventos. Tu tarea es analizar la siguiente entrada del usuario y extraer toda la información relevante, organizándola en una estructura JSON que se adhiera al siguiente esquema JSON.

    REQUISITOS DE FORMATO IMPORTANTES:
    - Usa como plantilla la siguiente estructura de criterios (puedes omitir campos para los que no haya información, pero incluye todos los subcampos relevantes si hay datos).
    - Completa tantos campos y subcampos como sea posible usando la información del usuario.
    - No inventes datos, pero sí infiere información si está implícita.
    - El resultado debe ser un único objeto JSON válido, sin comentarios ni texto adicional.
    - Si algún campo no tiene información, simplemente omítelo del resultado.
    
    REGLAS DE FORMATO CRÍTICAS:
    1. Para campos que esperan arrays (como "atmosphere", "cuisines", "dietary_options"), siempre usa formato de array: ["valor1", "valor2"]
    2. Para campos enum, solo usa los valores exactos especificados en el esquema:
       - Cuisines: solo "Pan-Asian", "Pan-European", "Southern", "Latin American", "American", "BBQ", "Italian"
       - Dietary options: solo "Dairy-free", "Gluten-free", "Nut-free", "Vegan", "Vegetarian"
       - Atmosphere: solo "Indoor", "Outdoor", "Rustic Chic"
    3. Si un usuario menciona preferencias dietéticas como "vegan", ponlo en "dietary_options", no en "cuisines"
    4. Si un usuario menciona tipo de ubicación como "outside", ponlo en "venue.atmosphere" como ["Outdoor"]

    Esquema JSON:
    {json.dumps(schema, indent=2)}

    Entrada del usuario:
    {user_input}

    Contexto previo:
    {context if context else 'N/A'}

    Devuelve solo el objeto JSON resultante, sin ningún texto adicional.
    """

def ASK_FOR_MORE_DATA_EN(missing_fields, context):
    return f"""
    You are an expert event planning assistant.

    To continue with your event organization and provide you with the best experience, I need you to help me complete the following information:

    - **Essential fields (required to proceed):**
    {', '.join(missing_fields.get("obligatorios", []))}

    - **Recommended fields (optional, but useful for personalizing your experience):**
    {', '.join(missing_fields.get("utiles", []))}

    Current Context:
    {context if context else 'N/A'}

    Please respond by providing the information for the essential fields. If you can, also add the recommended ones so that the planning is even more accurate. If you have doubts about any field, let me know and I'll explain it to you with pleasure.

    Write a clear, friendly, and motivating question to request these details from the user.
    """

def ASK_FOR_MORE_DATA(missing_fields, context):
    return f"""
    Eres un asistente experto en planificación de eventos.

    Para continuar con la organización de tu evento y ofrecerte la mejor experiencia, necesito que me ayudes completando la siguiente información:

    - **Campos imprescindibles (necesarios para avanzar):**
    {', '.join(missing_fields.get("obligatorios", []))}

    - **Campos recomendados (opcionales, pero útiles para personalizar tu experiencia):**
    {', '.join(missing_fields.get("utiles", []))}

    Contexto actual:
    {context if context else 'N/A'}

    Por favor, responde proporcionando la información de los campos imprescindibles. Si puedes, añade también los recomendados para que la planificación sea aún más precisa. Si tienes dudas sobre algún campo, házmelo saber y te lo explico con gusto.

    Redacta una pregunta clara, amable y motivadora para solicitar estos detalles al usuario.
    """

def TRANSFORM_FROM_JSON_TO_NL_EN(json_text):
    return f"""
    You are an event planning assistant. Given the following summary in JSON-like text, create a clear and user-friendly description:

    Summary:
    {json_text}

    Return only the final text without any additional formatting.
    """

def TRANSFORM_FROM_JSON_TO_NL(json_text):
    return f"""
    Eres un asistente de planificación de eventos. Dado el siguiente resumen en texto tipo JSON, elabora una descripción clara y amigable para el usuario:

    Resumen:
    {json_text}

    Devuelve solo el texto final sin ningún formato adicional.
    """