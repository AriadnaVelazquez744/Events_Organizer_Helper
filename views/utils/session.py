import streamlit as st
from .llm_interface import LLMInterface
from .models import Criterios, ResponseModel
from main import Comunication
import json
from pydantic import ValidationError

def initialize_session_state():
    """Initializes the session state for the chat."""
    if 'criterios' not in st.session_state:
        st.session_state.criterios = Criterios()
    if 'criterios_prev' not in st.session_state:
        st.session_state.criterios_prev = Criterios()
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = "default_user" # O genera uno único
    if "session_id" not in st.session_state:
        st.session_state.session_id = "default_session" # O genera uno único

def reset_criterios_for_new_session():
    """Resets both criterios and criterios_prev for a new session."""
    st.session_state.criterios = Criterios()
    st.session_state.criterios_prev = Criterios()

def process_user_input_and_query():
    """
    Orchestrates the conversation flow:
    1. Stores current criteria as previous before processing new input.
    2. Processes user input to extract criteria.
    3. Validates and merges it with previous criteria.
    4. Checks for missing fields.
    5. Asks for more info or processes the complete query.
    """
    user_input = st.session_state.get("user_input", "")
    if not user_input:
        return "Por favor, introduce tu consulta."

    llm = LLMInterface()
    
    # 1. Store current criteria as previous before processing new input
    if 'criterios' in st.session_state:
        st.session_state.criterios_prev = st.session_state.criterios.model_copy()
        print(f"🔄 Stored previous criteria: {st.session_state.criterios_prev.model_dump_json(indent=2)}")
    
    # Get current criteria from session state
    current_criterios = st.session_state.criterios

    try:
        # 2. Process user input to get new criteria
        context = current_criterios.model_dump_json(indent=2, exclude_unset=True)
        response_json = llm.process_user_input(user_input, context=context)
        
        # Check if the response contains an error
        try:
            response_data = json.loads(response_json)
            if "error" in response_data:
                error_msg = response_data.get("error", "Unknown error")
                print(f"❌ LLM Error detected: {error_msg}")
                return f"Lo siento, estoy teniendo problemas técnicos en este momento. Error: {error_msg}. Por favor, intenta de nuevo en unos momentos."
        except json.JSONDecodeError:
            # If it's not valid JSON, continue with normal processing
            pass
        
        # 3. Validate the new data
        new_data = ResponseModel.model_validate_json(response_json)
        print(f"🆕 New criteria from LLM: {new_data.criterios.model_dump_json(indent=2)}")
        
        # Debug: Check the actual values after validation
        print(f"🔍 Debug - After validation:")
        print(f"  presupuesto: {new_data.criterios.presupuesto}")
        print(f"  guest_count: {new_data.criterios.guest_count}")
        print(f"  venue.type: {new_data.criterios.venue.type if new_data.criterios.venue else None}")
        print(f"  venue.atmosphere: {new_data.criterios.venue.atmosphere if new_data.criterios.venue else None}")
        
        # 4. Use the validated data directly without unification
        updated_data = new_data.criterios
        print(f"✅ Using validated criteria directly: {updated_data.model_dump_json(indent=2)}")
        
        # Update the session state with the validated data
        st.session_state.criterios = updated_data
        
        # 5. Check for missing fields
        missing_fields = llm.check_missing_fields(updated_data)

        if missing_fields["obligatorios"]:
            # 6. Ask for more info
            follow_up_question = llm.ask_for_more_details(
                missing_fields, 
                context=updated_data.model_dump_json(indent=2, exclude_unset=True)
            )
            return follow_up_question
        else:
            # 7. Process the complete query
            final_request = updated_data.model_dump()
            
            # This part seems to call your backend system
            # Ensure `Comunication.send_query` can handle this dictionary
            response_from_system = Comunication.send_query(
                final_request, 
                st.session_state.session_id, 
                st.session_state.user_id
            )
            
            # Convert the final response to natural language for the user
            nlp_response = llm.json_to_natural_language(response_from_system)
            return nlp_response

    except ValidationError as e:
        # Handle cases where the LLM returns invalid JSON
        error_details = []
        for error in e.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            error_msg = f"Field '{field_path}': {error['msg']}"
            if "input" in error:
                error_msg += f" (received: {error['input']})"
            error_details.append(error_msg)
        
        error_message = "Estoy teniendo problemas para entender la respuesta. Detalles del error:\n" + "\n".join(error_details)
        print(f"❌ Validation error: {error_message}")
        return error_message
    except json.JSONDecodeError:
        # Handle cases where the response is not even JSON
        return "La respuesta no parece ser un JSON válido. ¿Podrías intentarlo de nuevo?"
    except Exception as e:
        return f"Ha ocurrido un error inesperado: {str(e)}"
