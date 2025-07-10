import json
import streamlit as st
from typing import Any, Dict, Optional
from difflib import get_close_matches
from interface.prompts import TRANSFORM_INITIAL_QUERY_EN, TRANSFORM_FROM_JSON_TO_NL_EN, ASK_FOR_MORE_DATA_EN
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

def check_obligatorios_consistency(result):
    """
    Ensures all filled fields in venue, catering, and decor are present in their respective 'obligatorios' arrays.
    Adds any missing fields and prints a warning if any were missing.
    """
    from interface.models import ObligatoriesVenue, ObligatoriesCatering, ObligatoriesDecor
    for section, enum_cls in [
        ("venue", ObligatoriesVenue),
        ("catering", ObligatoriesCatering),
        ("decor", ObligatoriesDecor),
    ]:
        if section in result and isinstance(result[section], dict):
            obj = result[section]
            allowed = set(e.value for e in enum_cls)
            filled = set(k for k, v in obj.items() if k in allowed and v not in (None, [], ""))
            obligatorios = set(obj.get("obligatorios", []))
            missing = filled - obligatorios
            if missing:
                print(f"[WARNING] In '{section}', the following filled fields were missing from 'obligatorios' and will be added: {missing}")
                # Add missing fields to obligatorios
                obj["obligatorios"] = sorted(list(obligatorios | missing))

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
    check_obligatorios_consistency(result)
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

            print(f"key: {key}, full_key: {full_key}")
            if is_not_empty:
                remove_from_missing(key, missing)  # For top-level fields
                remove_from_missing(full_key, missing) # For nested fields like 'venue.type'

            if key in target and target.get(key) is not None:
                print(f"key: {key} in {target}")
                # Rule 2: Key exists, merge based on type
                if isinstance(target[key], list) and isinstance(value, list):
                    # Combine lists and remove duplicates
                    target[key] = sorted(list(set(target[key] + value)))
                elif isinstance(target[key], dict) and isinstance(value, dict):
                    # Recurse for nested dictionaries
                    merge_recursive(target[key], value, missing, full_key)
                    # After recursion, remove missing for all nested keys that are set
                    for sub_k, sub_v in value.items():
                        sub_full_key = f"{full_key}.{sub_k}"
                        if sub_v is not None and sub_v != '' and sub_v != [] and sub_v != {}:
                            remove_from_missing(sub_full_key, missing)
                elif is_not_empty:
                    # Replace single value if the new value is not empty
                    target[key] = value
                    remove_from_missing(full_key, missing)
            elif is_not_empty:
                # Rule 1: Key doesn't exist, add if not null/empty
                target[key] = value
                if isinstance(value, dict):
                    # Remove missing for all nested keys that are set
                    for sub_k, sub_v in value.items():
                        sub_full_key = f"{full_key}.{sub_k}"
                        if sub_v is not None and sub_v != '' and sub_v != [] and sub_v != {}:
                            remove_from_missing(sub_full_key, missing)
                else:
                    remove_from_missing(full_key, missing)
        return target

    merged = merge_recursive((old or {}).copy(), new or {}, missing_fields)
    st.session_state.missing_fields = missing_fields

    # Return the merged dictionary directly without Pydantic validation
    # to preserve the original string format and structure
    return merged

def get_more_requirements_message(missing_fields, context, llm_client=None):
    """
    Generates a requirements message for the user if there are missing necessary fields.
    Uses the ASK_FOR_MORE_DATA_EN prompt and calls the LLM.
    """
    prompt = ASK_FOR_MORE_DATA_EN(missing_fields, context)
    if llm_client:
        return call_llm(prompt, llm_client)
    else:
        return "Please provide more details for the required fields."

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

    print(f"new_json: {new_json}")
    print(f"merged_json: {merged_json}")
    print(f"missing_fields: {st.session_state.missing_fields}")
    print(f"prev_context: {prev_context}")
    # import sys; sys.exit(0)

    # Check for missing necessary fields ---
    missing_fields = st.session_state.missing_fields
    if missing_fields.get("necessary"):  # If there are required fields missing
        # Generate a requirements message using the LLM and return it directly
        requirements_message = get_more_requirements_message(
            missing_fields,
            merged_json,  # Pass the merged context for more accurate prompt
            llm_client
        )
        return requirements_message, merged_json

    checking = f"new_json: {new_json} \n\n prev_context: {prev_context} \n\n merged_json: {merged_json} \n\n missing_fields: {st.session_state.missing_fields}"
    return checking, merged_json

    # 3. Pass to backend (send_query expects merged_json)
    from main import Comunication  # Import here to avoid circular import
    response_json = Comunication.send_query(merged_json, session_id, user_id)
    print(response_json)
    
    response_json = st.session_state.response_planner
    # 4. JSON -> NL
    nl_message = call_llm_json_to_nl(response_json, llm_client)
    return nl_message, merged_json