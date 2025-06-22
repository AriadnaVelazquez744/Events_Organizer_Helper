import streamlit as st

def instance_missing_fields():
     if "missing_fields" not in st.session_state:
        st.session_state.missing_fields = {
            "necessary": [
                "presupuesto", "guest_count", "venue", "catering"
            ],
            "useful": [
                "style", "decor", "venue.atmosphere", "venue.type",
                "venue.services", "catering.services", "catering.dietary_options",
                "catering.meal_types", "decor.floral_arrangements", "decor.restrictions"
            ]
        }
