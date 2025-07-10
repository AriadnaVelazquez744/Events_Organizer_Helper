import streamlit as st

def instance_missing_fields():
    # Always reset missing_fields to the full set of possible fields
    st.session_state.missing_fields = {
        "necessary": [
            "presupuesto_total", "guest_count", "venue", "catering"
        ],
        "useful": [
            "style", "decor", "venue.atmosphere", "venue.venue_type",
            "venue.services", "catering.services", "catering.dietary_options",
            "catering.meal_types", "decor.floral_arrangements", "decor.restrictions"
        ]
    }
