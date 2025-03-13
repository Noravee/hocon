from pyhocon import ConfigFactory, HOCONConverter
import streamlit as st
import string

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


def sidebar_content():
    if st.session_state.show_sidebar:
        with st.sidebar:
            # Function to add a new input box
            def add_input():
                new_key = max(st.session_state.inputs.keys(), default=-1) + 1
                st.session_state.inputs[new_key] = {
                    "name": "",
                    "class": "",
                    "function": {},
                    "instructions": "",
                    "command": "",
                    "tools": [],
                    "llm_config": {"model_name": st.session_state.llm_model, "temperature": st.session_state.temperature}
                }
                st.session_state.function_names[new_key] = ""
                st.session_state.errors[new_key] = ""  # Initialize error tracking

            # Function to remove a specific input box
            def remove_input(key):
                if len(st.session_state.inputs) > 1:
                    deleted_node = st.session_state.inputs[key]["name"]
                    del st.session_state.inputs[key]
                    del st.session_state.function_names[key]
                    del st.session_state.errors[key]  # Remove associated error

                    # Remove deleted node from all connection lists
                    for index in st.session_state.inputs:
                        st.session_state.inputs[index]['tools'] = [
                            conn for conn in st.session_state.inputs[index]['tools'] if conn != deleted_node
                        ]
                    st.rerun()  # Forces immediate UI update

            def replace_strings_in_nested_dict(d, replacements):
                """Recursively replace string values in a nested dictionary."""
                if isinstance(d, dict):
                    return {k: replace_strings_in_nested_dict(v, replacements) for k, v in d.items()}
                elif isinstance(d, list):  # Handle lists of dictionaries or strings
                    return [replace_strings_in_nested_dict(item, replacements) for item in d]
                elif isinstance(d, str):  # Replace string values
                    return string.Template(d).safe_substitute(replacements)
                return d  # Return unchanged for other types

            def remove_empty_values(d):
                """Recursively remove empty values ('', [], or {}) starting from the deepest level."""
                if isinstance(d, dict):
                    # First process inner dictionaries
                    cleaned_dict = {k: remove_empty_values(v) for k, v in d.items()}
                    # Then remove keys that became empty
                    return {k: v for k, v in cleaned_dict.items() if v not in ('', [], {})}

                elif isinstance(d, list):  
                    # Process lists but keep them intact
                    return [remove_empty_values(item) for item in d]

                return d  # Return unchanged for other types

            st.title("Agents Input Fields")

            input_keys = list(st.session_state.inputs.keys())  # Store keys to avoid modifying while iterating

            to_remove = None  # Store key to remove
            filters_changed = False  # Track if we need to rerun Streamlit

            # Precompute available options before iterating over inputs
            available_options = [node["name"] for node in st.session_state.inputs.values() if node["name"]]
            existing_names = set(node["name"] for node in st.session_state.inputs.values())

            for key in input_keys:
                st.session_state.errors[key] = ''
                cols = st.columns([4, 1])
                with cols[0]:
                    # Node name input
                    prev_name = st.session_state.inputs[key]["name"]
                    if key == 0:
                        new_name = st.text_input("Name of frontman", value=prev_name, key=f"input_{key}", help='Name of an agent that is the default point of contact to users')
                    else:
                        new_name = st.text_input("Name", value=prev_name, key=f"input_{key}", help='Name of agent or tool')

                    # Enforce uniqueness
                    if new_name != prev_name:
                        if new_name in existing_names:
                            st.session_state.errors[key] = f"❌ '{new_name}' is already in used. Choose a different name."
                        else:
                            st.session_state.errors[key] = ""  # Clear error if valid
                            existing_names.discard(prev_name)  # Remove old value
                            existing_names.add(new_name)  # Add new value
                            st.session_state.inputs[key]["name"] = new_name
                            st.rerun()

                    # Display inline error if node name is duplicate
                    if st.session_state.errors.get(key):
                        st.error(st.session_state.errors[key])

                # Filter available options, excluding the current node
                options = [node for node in available_options if node and node != new_name]

                # Ensure connections contain only valid nodes
                filtered_connections = [conn for conn in st.session_state.inputs[key]['tools'] if conn in options]
                if filtered_connections != st.session_state.inputs[key]['tools']:
                    st.session_state.inputs[key]['tools'] = filtered_connections
                    filters_changed = True  # Mark as changed

                # Render Multiselect for connections
                selected_connections = st.multiselect(
                    "Points to",
                    options=options,
                    default=st.session_state.inputs[key]['tools'],
                    key=f"connections_{key}",
                    help='Agents or tools that this node calls'
                )

                # Detect selection changes and update state
                if selected_connections != st.session_state.inputs[key]['tools']:
                    st.session_state.inputs[key]['tools'] = selected_connections
                    filters_changed = True  # Mark as changed

                with cols[1]:
                    if key != 0:
                        if st.button("❌", key=f"remove_{key}"):
                            to_remove = key  # Mark for removal

                # Track expander state manually
                expander_key = f"expander_{key}"
                if expander_key not in st.session_state:
                    st.session_state[expander_key] = False  # Default to collapsed

                # Expander for each input (contains "instructions", "command", and "function")
                with st.expander(f"Details for '{st.session_state.inputs[key]['name'] or 'Node'}'", expanded=st.session_state[expander_key]) as expander:
                    prev_instr = st.session_state.inputs[key]["instructions"]
                    new_instr = st.text_area(
                        "Instructions", value=st.session_state.inputs[key]["instructions"],
                        key=f"instructions_{key}",
                        help='Detail of task for the agent'
                    )
                    if new_instr != prev_instr:
                        st.session_state.inputs[key]["instructions"] = new_instr
                        st.session_state[expander_key] = True  # Force open when renaming
                        st.rerun()
                    prev_command = st.session_state.inputs[key]["command"]
                    new_command = st.text_area(
                        "Command", value=st.session_state.inputs[key]["command"],
                        key=f"command_{key}",
                        help='User-like message intended for an agent after receiving all the inputs'
                    )
                    if new_command != prev_command:
                        st.session_state.inputs[key]["command"] = new_command
                        st.session_state[expander_key] = True  # Force open when renaming
                        st.rerun()

                    def safe_index(lst, item):
                        return lst.index(item) + 1 if item in lst else None

                    func_name_list = list(st.session_state.function_results)
                    prev_f_name = st.session_state.function_names[key]
                    f_name = st.selectbox(
                                label="function",
                                options=[None] + func_name_list,
                                index=safe_index(func_name_list, st.session_state.function_names[key]),
                                key=f"function_{key}",
                                help="Function called by the agent"
                            )

                    if f_name != prev_f_name:
                        st.session_state.function_names[key] = f_name
                        if st.session_state.function_results:
                            if st.session_state.function_names[key] is None:
                                st.session_state.inputs[key]["function"] = {}
                                st.session_state.inputs[key]["class"] = ''
                            else:
                                st.session_state.inputs[key]["function"] = st.session_state.function_results[st.session_state.function_names[key]]['function']
                                st.session_state.inputs[key]["class"] = st.session_state.function_results[st.session_state.function_names[key]]['class']
                        # st.session_state[expander_key] = True  # Force open when renaming
                        st.rerun()

                # Expander for each input (contains "llm_config")
                with st.expander(f"LLM for '{st.session_state.inputs[key]['name'] or 'Node'}'"):
                    llm_model = st.selectbox(label="Model",
                                options=list(LLM_MODEL_DICT.keys()),
                                # index=list(LLM_MODEL_DICT.values()).index(st.session_state.inputs[key]['llm_config']['model_name']),
                                index=list(LLM_MODEL_DICT.keys()).index(st.session_state.inputs[key]['llm_config']['model_name']),
                                key=f"model_name_{key}",
                                help='Large langauge model'
                                )
                    temperature = st.slider("Temperature", 0.0, 1.0, st.session_state.inputs[key]['llm_config']['temperature'],
                                            key=f"temperature_{key}",
                                            help='High for creativity, low for precision.')

                    # if LLM_MODEL_DICT[llm_model] != st.session_state.inputs[key]['llm_config']['model_name'] or temperature != st.session_state.inputs[key]['llm_config']['temperature']:
                    if llm_model != st.session_state.inputs[key]['llm_config']['model_name'] or temperature != st.session_state.inputs[key]['llm_config']['temperature']:
                        # st.session_state.inputs[key]['llm_config']['model_name'] = LLM_MODEL_DICT[llm_model]
                        st.session_state.inputs[key]['llm_config']['model_name'] = llm_model
                        st.session_state.inputs[key]['llm_config']['temperature'] = temperature
                        st.rerun()

                st.divider()

            # Allow manual collapsing
            if not expander:  # If user collapses manually
                st.session_state[expander_key] = False

            # Buttons for adding inputs and submitting values
            left, right = st.columns([1, 1])
            with left:
                st.button("➕ Add Input", on_click=add_input)
            with right:
                if st.button("❌ Remove Last Input", key="remove_last"):
                    to_remove = input_keys[-1]

            # Remove input field immediately if button was pressed
            if to_remove is not None:
                remove_input(to_remove)

            # Trigger rerun if filters changed
            if filters_changed:
                st.rerun()

            new_tools = replace_strings_in_nested_dict(st.session_state.inputs, st.session_state.sub_dict)

            data = {
                "llm_config": {
                    "model_name": st.session_state.llm_model,
                    "temperature": st.session_state.temperature,
                },
                "tools": [i for i in new_tools.values() if i['name'] != '']
            }

            data = remove_empty_values(data)

            # Convert dictionary to HOCON config
            config = ConfigFactory.from_dict(data)

            # Convert to HOCON format and write to file
            hocon_str = HOCONConverter.convert(config, "hocon")

            filename = st.text_input("Enter agent network name", st.session_state.network_file_name)
            if filename != st.session_state.network_file_name:
                st.session_state.network_file_name = filename
                st.rerun()

            disabled = any(list(st.session_state.errors.values()) + list(st.session_state.function_errors.values()))

            st.download_button(
                label="💾 Download HOCON File",
                data=hocon_str,
                file_name=st.session_state.network_file_name,
                mime="text/plain",
                disabled=disabled
            )

            if disabled:
                st.error('🛠️ Please fix the error before downloading.')
