import re

from pyhocon import ConfigFactory
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

def get_key(d, value):
    return next((k for k, v in d.items() if v == value))

def get_value(d, key):
    # Step 1: If the key exists in the dictionary, return its value
    if key in d:
        # return d[key]
        return key

    # Step 2: If the key doesn't exist, check if it's in the values
    if key in d.values():
        # return key
        return get_key(d, key)

    # Step 3: If nothing matches, return the first value in the dictionary
    # return next(iter(d.values()))
    return next(iter(d.keys()))

def replace_value_with_key(text, mapping):
    """Replace values in text with corresponding keys in ${key} format."""
    for key, value in mapping.items():
        pattern = re.escape(value)  # Escape special characters in the value
        text = re.sub(rf'\b{pattern}\b', f'${{{key}}}', text)  # Replace whole words only
    return text

@st.dialog("Warning")
def confirm():
    st.warning("⚠️ This will delete existing network and cannot be undone.")
    st.warning("Do you want to proceed?")
    if st.button("Confirm"):
        create_network()
        st.rerun()

@st.dialog("Warning")
def confirm_load(uploaded_file):
    st.warning("⚠️ This will delete existing network and cannot be undone.")
    st.warning("Do you want to proceed?")
    if st.button("Confirm"):
        load_network(uploaded_file)
        st.rerun()

def create_network():

    # Initialize session state variables
    st.session_state.show_sidebar = True  # Show sidebar when button is clicked
    # st.session_state.llm_model = list(LLM_MODEL_DICT.values())[0]
    st.session_state.llm_model = list(LLM_MODEL_DICT.keys())[0]
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
    st.session_state.existing_functions = {}
    st.session_state.network_file_name = "network.hocon"

def load_network(uploaded_file):

    create_network()

    try:
        # Attempt to load as a HOCON or CONF file
        if uploaded_file.name.endswith(".hocon") or uploaded_file.name.endswith(".conf") or uploaded_file.name.endswith(".json"):
            config = ConfigFactory.parse_string(uploaded_file.getvalue().decode("utf-8"))
        else:
            st.error("Unsupported file format!")

    except Exception as e:
        st.error(f"An error occurred while loading the file: {e}")

    default_llm_config = config.get('llm_config', {})
    if default_llm_config:
        default_llm_model = default_llm_config.get('model_name', list(LLM_MODEL_DICT.keys())[0])
        st.session_state.llm_model = get_value(LLM_MODEL_DICT, default_llm_model)
        st.session_state.temperature = default_llm_config.get('temperature', 0.5)

    network = config.get('tools', [])
    if network and isinstance(network, list):
        for agent_index, agent in enumerate(network):
            # Ensure the key exists before accessing it
            st.session_state.inputs.setdefault(agent_index, {
                "name": "",
                "class": "",
                "function": {},
                "instructions": "",
                "command": "",
                "tools": [],
                "llm_config": {"model_name": st.session_state.llm_model, "temperature": st.session_state.temperature}
            })
            agent_entry = st.session_state.inputs[agent_index]
            agent_entry['name'] = replace_value_with_key(agent['name'], st.session_state.sub_dict)
            module_class = agent.get('class', '')
            agent_entry['class'] = replace_value_with_key(module_class, st.session_state.sub_dict)
            instructions = agent.get('instructions', '')
            agent_entry['instructions'] = replace_value_with_key(instructions, st.session_state.sub_dict)
            command = agent.get('command', '')
            agent_entry['command'] = replace_value_with_key(command, st.session_state.sub_dict)
            tools = agent.get('tools', [])
            agent_entry['tools'] = tools
            llm_config = agent.get('llm_config', {'model_name': st.session_state.llm_model, 'temperature': st.session_state.temperature})
            llm_model = llm_config.get('model_name', default_llm_model)
            agent_entry['llm_config']['model_name'] = get_value(LLM_MODEL_DICT, llm_model)
            agent_entry['llm_config']['temperature'] = llm_config.get('temperature', st.session_state.temperature)

            func = agent.get('function', {})
            if func and isinstance(func, dict):
                if func not in list(st.session_state.existing_functions.values()):
                    st.session_state.existing_functions[agent_index] = func
                    func_index = max(st.session_state.functions, default=-1) + 1
                    st.session_state.functions.setdefault(func_index, {
                        "name": "",
                        "description": "",
                        "parameters": {"type": "object", "properties": {}, "required": []},
                        "module": "",
                        "class": ""
                    })
                    func_entry = st.session_state.functions[func_index]
                    func_entry['name'] = f'func_{func_index}'
                    st.session_state.function_names[agent_index] = func_entry['name']
                    # st.session_state.function_results[func_entry['name']] = {}
                    func_desc = func.get('description', '')
                    func_entry['description'] = replace_value_with_key(func_desc, st.session_state.sub_dict)
                    if module_class:
                        module_class_list = module_class.split('.')
                        func_entry['module'] = replace_value_with_key(module_class_list[0], st.session_state.sub_dict) if len(module_class_list) > 1 else ''
                        func_entry['class'] = replace_value_with_key(module_class_list[1], st.session_state.sub_dict) if len(module_class_list) > 1 else ''
                    parameters = func.get('parameters', {})
                    func_entry['parameters']['required'] = parameters.get('required', [])
                    properties = parameters.get('properties', {})
                    st.session_state.add_func_param[f'func_{func_index}'] = len(properties)
                    for param_index, (p_name, p_val) in enumerate(properties.items()):
                        func_entry['parameters']['properties'].setdefault(param_index, {
                            "name": "",
                            #"type": [],
                            "type": "",
                            "description": ""
                        })
                        func_entry['parameters']['properties'][param_index]['name'] = replace_value_with_key(p_name, st.session_state.sub_dict)
                        func_entry['parameters']['properties'][param_index]['type'] = p_val.get('type', '')
                        func_entry['parameters']['properties'][param_index]['description'] = replace_value_with_key(p_val.get('description', ''), st.session_state.sub_dict)
                else:
                    st.session_state.function_names[agent_index] = st.session_state.function_names[get_key(st.session_state.existing_functions, func)]
            else:
                st.session_state.function_names[agent_index] = ''


def create_tab_content():
    st.title("Create Agent Network")

    if st.button("Create new"):
        if st.session_state.show_sidebar:
            confirm()
        else:
            create_network()
            st.rerun()

    st.title("Load Agent Network")

    uploaded_file = st.file_uploader(
                        label="Upload Agent Network from File",
                        type=['hocon', 'conf'],
                        key='network_loader',
                        )
    if uploaded_file:
        file_id = uploaded_file.file_id
        if file_id not in st.session_state.existing_files:
            st.session_state.existing_files.append(file_id)
            if st.session_state.show_sidebar:
                confirm_load(uploaded_file)
            else:
                load_network(uploaded_file)
                st.rerun()
