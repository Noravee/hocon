import streamlit as st
from create_load_tab import create_tab_content
from function_tab import function_tab_content
from llm_tab import llm_tab_content
from network_tab import network_tab_content
from sidebar import sidebar_content
from substitution_tab import substitution_tab_content


st.set_page_config(page_title="HOCON editor", layout="centered")

# Initialize session state for sidebar visibility
if "show_sidebar" not in st.session_state:
    st.session_state.show_sidebar = False  # Sidebar starts hidden

sidebar_content()

create, llm, network, function, substitution = st.tabs(['Create/Load', 'Default LLM', 'Network', 'Functions', 'Substitution'])

with create:
    create_tab_content()

with llm:
    llm_tab_content()

with network:
    network_tab_content()

with function:
    function_tab_content()

with substitution:
    substitution_tab_content()
