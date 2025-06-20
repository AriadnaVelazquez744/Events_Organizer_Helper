import streamlit as st
from views.utils.llm_interface import LLMInterface
from main import Comunication
import json
import os

def process_user_input_and_query():
    """
    Receives a natural language string from the user, processes it with the LLM, and sends the structured result to the planner system.
    Uses Streamlit's session_state for session and user management.
    Updates the chat/messages in session_state accordingly.
    """
    current_query = st.session_state.current_query
    requirements = st.session_state.user_requirements
    # Process input with LLM to extract structured criteria
    llm = LLMInterface()
    structured_criteria = llm.process_user_input(current_query)

    # Try to parse the LLM output as JSON
    try:
        request = json.loads(structured_criteria)
    except Exception as e:
         f"❌ Error procesando tu solicitud: {str(e)}. Por favor, intenta de nuevo."
    
    if (requirements != ""):
        structured_criteria = llm.unify_jsons(requirements, request)
        request = json.loads(structured_criteria)

    missing_necessary, missing_suggested = find_missing_fields(structured_criteria)

    # if (missing_necessary != "" or missing_suggested != ""):
    #     response = llm.ask_for_more_details(missing_necessary, missing_suggested, structured_criteria)
    #     return response
    # else: 
    #     # Send structured request to the planner system
    response = Comunication.send_query(request, st.session_state.session_id, st.session_state.user_id)

    NLP_response = llm.json_to_natural_language(response)
    return NLP_response


def find_missing_fields(json_text):
    """
    From two lists (necessary_fields, suggested_fields) and a plain text with a JSON-like structure,
    returns two lists: the missing necessary fields and the missing suggested fields from the parsed JSON.
    """
    necessary_fields = ["presupuesto_total", "guest_count_general", "venue", "catering"]
    suggested_fields = [ "general_style", "atmosphere", "venue_type", "venue_services", "catering_services", "dietary_options", "meal_types", "decor", "floral_arrangements", "restrictions_decor"]
    try:
        data = json.loads(json_text)
    except Exception:
        # Try to fix common JSON issues (e.g., single quotes)
        try:
            fixed = json_text.replace("'", '"')
            data = json.loads(fixed)
        except Exception:
            return necessary_fields, suggested_fields  # If parsing fails, all are missing

    def check_field(field, data):
        # Support nested fields with dot notation
        parts = field.split('.')
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        return True

    missing_necessary = [f for f in necessary_fields if not check_field(f, data)]
    missing_suggested = [f for f in suggested_fields if not check_field(f, data)]
    return missing_necessary, missing_suggested
