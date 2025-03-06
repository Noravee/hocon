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


@st.dialog("Warning")
def confirm():
    st.warning("⚠️ This will delete existing network and cannot be undone.")
    st.warning("Do you want to proceed?")
    if st.button("Confirm"):
        create_network()
        st.rerun()

def create_network():

    # Initialize session state variables
    st.session_state.show_sidebar = True  # Show sidebar when button is clicked
    st.session_state.llm_model = list(LLM_MODEL_DICT.values())[0]
    st.session_state.temperature = 0.5
    st.session_state.inputs = {0: {
        "name": "",
        "class": "",
        "function": {},
        "instructions": "",
        "command": "",
        "tools": [],
        "llm_config": {"model_name": st.session_state.llm_model, "temperature": st.session_state.temperature}
    }}  # Store name, instructions, command, and tools per node
    st.session_state.errors = {}  # Store validation errors
    st.session_state.function_names = {0: ""}
    st.session_state.hierarchical = False
    st.rerun()

def create_tab_content():
    st.title("Create Agent Network")

    if st.button("Create new"):
        if st.session_state.show_sidebar:
            confirm()
        else:
            create_network()
