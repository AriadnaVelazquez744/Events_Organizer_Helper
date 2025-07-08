import json
import streamlit as st
from typing import Any, Dict, Optional
from difflib import get_close_matches
from interface.prompts import TRANSFORM_INITIAL_QUERY_EN, TRANSFORM_FROM_JSON_TO_NL_EN
from interface.models import Criterios
from pydantic import ValidationError
# from interface.api.openrouter_client import ChatMessage
from interface.api.fireworks_client import ChatMessage

# You must replace this with your actual LLM client import and call
# from interface.api.openrouter_client import SyncOpenRouterClient
# llm_client = SyncOpenRouterClient(...)
# from interface.api.fireworks_client import SyncFireworksClient
# llm_client = SyncFireworksClient(...)

# Helper to call the LLM using the OpenRouter client
def call_llm(prompt: str, llm_client):
    messages = [ChatMessage(role="user", content=prompt)]
    response = llm_client.chat_completion(messages=messages)
    return response.choices[0].message.content

def call_llm_extract_json(user_input: str, prev_context: Optional[dict] = None, llm_client=None) -> dict:
    """
    Calls the LLM to extract a JSON structure from user NL input, using the Criterios schema.
    Returns a dict (parsed JSON).
    """
    criterios_schema = Criterios.model_json_schema()
    prompt = TRANSFORM_INITIAL_QUERY_EN(criterios_schema, user_input, prev_context)
    if llm_client:
        llm_response = call_llm(prompt, llm_client)
    else:
        llm_response = "{}"
    try:
        result = json.loads(llm_response)
    except Exception:
        import re
        match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
        else:
            raise ValueError("LLM did not return valid JSON")
    return result

def call_llm_json_to_nl(json_obj: dict, llm_client=None) -> str:
    """
    Calls the LLM to turn a JSON object into a user-friendly NL summary.
    """
    json_text = json.dumps(json_obj, indent=2, ensure_ascii=False)
    prompt = TRANSFORM_FROM_JSON_TO_NL_EN(json_text)
    if llm_client:
        llm_response = call_llm(prompt, llm_client)
    else:
        llm_response = "Here is your event summary."
    return llm_response.strip()

def merge_contexts(old: dict, new: dict, model=Criterios) -> dict:
    """
    Merge two context dicts, prioritizing new values, and updating a
    log of missing fields stored in st.session_state.missing_fields.

    - For lists: add new options (union, no duplicates).
    - For single values: replace with new.
    - If a new value is provided for a field that was missing, it's removed
      from the missing_fields log.
    - New keys are only added if their value is not None or empty.
    """
    missing_fields = st.session_state.get("missing_fields", {"necessary": [], "useful": []})

    def remove_from_missing(field_name: str, missing: dict):
        """Helper to remove a field from necessary or useful lists."""
        if 'necessary' in missing and field_name in missing['necessary']:
            missing['necessary'].remove(field_name)
        if 'useful' in missing and field_name in missing['useful']:
            missing['useful'].remove(field_name)

    def merge_recursive(target: dict, source: dict, missing: dict, parent_key: str = ""):
        """Recursively merge source into target and update missing fields."""
        for key, value in source.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            is_not_empty = value is not None and value != '' and value != [] and value != {}

            if is_not_empty:
                remove_from_missing(key, missing)  # For top-level fields
                remove_from_missing(full_key, missing) # For nested fields like 'venue.type'

            if key in target and target.get(key) is not None:
                # Rule 2: Key exists, merge based on type
                if isinstance(target[key], list) and isinstance(value, list):
                    # Combine lists and remove duplicates
                    target[key] = sorted(list(set(target[key] + value)))
                elif isinstance(target[key], dict) and isinstance(value, dict):
                    # Recurse for nested dictionaries
                    merge_recursive(target[key], value, missing, full_key)
                elif is_not_empty:
                    # Replace single value if the new value is not empty
                    target[key] = value
            elif is_not_empty:
                # Rule 1: Key doesn't exist, add if not null/empty
                target[key] = value
        return target

    merged = merge_recursive((old or {}).copy(), new or {}, missing_fields)
    st.session_state.missing_fields = missing_fields

    try:
        # Validate with Pydantic V2, will coerce types and check enums
        validated = model.model_validate(merged)
        return validated.model_dump(exclude_unset=True, by_alias=True)
    except ValidationError:
        return merged  # Return best effort on validation failure

def process_user_input(
    user_input: str,
    prev_context: Optional[dict],
    session_id: str,
    user_id: str,
    llm_client=None
) -> str:
    """
    Full flow: NL input -> LLM (JSON) -> merge -> backend -> LLM (NL) -> return answer.
    This is the only function chat_page.py should call.
    """
    print("aqui")
    # 1. NL -> JSON
    new_json = call_llm_extract_json(user_input, prev_context, llm_client)
    print("aqui2")
    # 2. Merge with previous context, updating missing_fields
    merged_json = merge_contexts(prev_context or {}, new_json)
    # 3. Pass to backend (send_query expects merged_json)
    from main import Comunication  # Import here to avoid circular import
    response_json = Comunication.send_query(merged_json, session_id, user_id)
    print(response_json)
    
    response_json = st.session_state.response_planner
    # 4. JSON -> NL
    nl_message = call_llm_json_to_nl(response_json, llm_client)
    return nl_message