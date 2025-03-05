import streamlit as st

LLM_MODEL_DICT = {
    "gpt-4.5-preview": "gpt-4.5-preview-2025-02-27",
    "gpt-4o": "gpt-4o-2024-08-06",
    "gpt-4o-mini": "gpt-4o-mini-2024-07-18",
    "o1": "o1-2024-12-17",
    "o1-mini": "o1-mini-2024-09-12",
    "o3-mini": "o3-mini-2025-01-31",
    "o1-preview": "o1-preview-2024-09-12",
    "Claude 3.7 Sonnet": "claude-3-7-sonnet-20250219",
    "Claude 3.5 Haiku": "claude-3-5-haiku-20241022",
    "Claude 3.5 Sonnet v2": "claude-3-5-sonnet-20241022",
    "Claude 3.5 Sonnet": "claude-3-5-sonnet-20240620",
    "Claude 3 Opus": "claude-3-opus-20240229",
    "Claude 3 Sonnet": "claude-3-sonnet-20240229",
    "Claude 3 Haiku": "claude-3-haiku-20240307"
}

def llm_tab_content():

    if "llm_model" in st.session_state:
        st.title('Default LLM')
        st.write('The following model will be used when model for each agent is not specified.')

        default_llm_model = st.selectbox(label="Model",
                                options=list(LLM_MODEL_DICT.keys()),
                                index=list(LLM_MODEL_DICT.values()).index(st.session_state.llm_model),
                                help='Large langauge model'
                                )
        default_temperature = st.slider("Temperature", 0.0, 1.0, st.session_state.temperature, help='High for creativity, low for precision.')

        if LLM_MODEL_DICT[default_llm_model] != st.session_state.llm_model or default_temperature != st.session_state.temperature:
            st.session_state.llm_model = LLM_MODEL_DICT[default_llm_model]
            st.session_state.temperature = default_temperature
            st.rerun()

    else:
        st.write('Please create or load agent network on the "Create/Load" first.')
