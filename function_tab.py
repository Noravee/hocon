import streamlit as st

TYPES = ['string', 'number', 'integer', 'object', 'array', 'boolean', 'null']


def function_tab_content():
    if "llm_model" in st.session_state:
        parameters = {"type": "object", "properties": {}, "required": []}

        # Function to add a new input box
        def add_input():
            new_key = max(st.session_state.functions.keys(), default=-1) + 1
            st.session_state.functions[new_key] = {"description": "", "parameters": parameters, "module": "", "class": ""}
            st.session_state.function_errors[new_key] = ""  # Initialize error tracking

        # Function to add a new parameter
        def add_param(function_key_index: int):
            new_key = max(st.session_state.functions[function_key_index]['parameters']['properties'].keys(), default=-1) + 1
            st.session_state.functions[function_key_index]['parameters']['properties'][new_key] = {"name": "", "type": [], "description": ""}

        # Function to remove a specific input box
        def remove_input(input_key: int):
            if len(st.session_state.functions) >= 1:
                del st.session_state.functions[input_key]
                del st.session_state.function_errors[input_key]  # Remove associated error
                st.rerun()  # Forces immediate UI update

        # Function to remove a specific parameter
        def remove_param(function_key_index: int, param_key_index: int):
            if len(st.session_state.functions[function_key_index]['parameters']['properties']) >= 1:
                del st.session_state.functions[function_key_index]['parameters']['properties'][param_key_index]
                st.rerun()  # Forces immediate UI update


        st.title("Functions Input Fields")

        input_keys = list(st.session_state.functions.keys())  # Store keys to avoid modifying while iterating

        to_remove = None  # Store key to remove
        require_change = False
        existing_pairs = {(item["module"], item["class"]) for item in st.session_state.functions.values()}

        for key in input_keys:
            cols = st.columns([1000, 1])
            with cols[0]:
                prev_desc = st.session_state.functions[key]["description"]
                # Function description input
                new_desc = st.text_area(
                    "Function description",
                    value=st.session_state.functions[key]["description"],
                    key=f"description_{key}",
                    help="Description of function or role of the agent",
                )
                if new_desc != prev_desc:
                    st.session_state.functions[key]["description"] = new_desc
                    st.rerun()

            with cols[1]:
                if st.button("❌", key=f"remove_function_{key}"):
                    to_remove = key  # Mark for removal

            # Parameter section
            param_keys = list(st.session_state.functions[key]["parameters"]["properties"].keys())
            to_remove_param = None

            for param_key in param_keys:
                param_cols = st.columns([4, 1])

                # Track expander state manually
                expander_key = f"expander_{key}_{param_key}"
                if expander_key not in st.session_state:
                    st.session_state[expander_key] = False  # Default to collapsed

                with param_cols[0]:
                    param_name = st.session_state.functions[key]["parameters"]["properties"][param_key]["name"]
                    with st.expander(f"Parameter: {param_name if param_name else ''}", expanded=st.session_state[expander_key]) as expander:
                        new_param_name = st.text_input(
                            label="Parameter name",
                            key=f"input_{key}_param_name_{param_key}",
                            value=st.session_state.functions[key]["parameters"]["properties"][param_key]["name"],
                        )
                        # Update session state only if name changes
                        if new_param_name != param_name:
                            st.session_state.functions[key]["parameters"]["properties"][param_key]["name"] = new_param_name
                            st.session_state[expander_key] = True  # Force open when renaming
                            st.rerun()
                        st.session_state.functions[key]["parameters"]["properties"][param_key]["type"] = st.multiselect(
                            label="Parameter type",
                            options=TYPES,
                            key=f"input_{key}_param_type_{param_key}",
                        )
                        prev_prop_desc = st.session_state.functions[key]["parameters"]["properties"][param_key]["description"]
                        new_prop_desc = st.text_area(
                            label="Parameter description",
                            key=f"input_{key}_param_desc_{param_key}",
                            value=st.session_state.functions[key]["parameters"]["properties"][param_key]["description"],
                        )
                        if new_prop_desc != prev_prop_desc:
                            st.session_state.functions[key]["parameters"]["properties"][param_key]["description"] = new_prop_desc
                            st.session_state[expander_key] = True  # Force open when renaming
                            st.rerun()

                # Allow manual collapsing
                if not expander:  # If user collapses manually
                    st.session_state[expander_key] = False

                with param_cols[1]:
                    if st.button("❌", key=f"remove_param_{key}_{param_key}"):
                        to_remove_param = param_key  # Mark for removal

                # Remove param field if button was pressed
                if to_remove_param is not None:
                    remove_param(key, to_remove_param)

            # Button for adding parameters
            st.button(
                "➕ Add param",
                on_click=lambda k=key: add_param(k),
                key=f"add_param_{key}",
            )

            st.session_state.function_errors[key] = ''

            module_cols = st.columns([4, 1])
            # Expander for module and class selection
            with module_cols[0]:
                param_options = [
                    param["name"]
                    for param in st.session_state.functions[key]["parameters"]["properties"].values()
                    if param["name"] != ""
                    ]
                required = st.multiselect(
                    label='Required parameter',
                    options=param_options,
                    default=st.session_state.functions[key]['parameters']['required'],
                    key=f'required_{key}',
                    help='Required parameters'
                )
                # st.session_state.functions[key]['parameters']['required'] = required

                if required != st.session_state.functions[key]['parameters']['required']:
                    st.session_state.functions[key]['parameters']['required'] = required
                    require_change = True

                prev_module = st.session_state.functions[key]["module"]
                prev_class = st.session_state.functions[key]["class"]

                new_module = st.text_input(
                    "Module",
                    value=prev_module,
                    key=f"module_{key}",
                    help="Module of the function",
                )
                new_class = st.text_input(
                    "Class",
                    value=prev_class,
                    key=f"class_{key}",
                    help="Class of the function",
                )

                # Check uniqueness of (module, class) pair
                new_pair = (new_module, new_class)
                prev_pair = (prev_module, prev_class)

                if new_pair != prev_pair:
                    if new_pair in existing_pairs:
                        st.session_state.function_errors[key] = f"❌ '{new_module}.{new_class}' is already used. Choose a different module or class."
                    else:
                        st.session_state.function_errors[key] = ""  # Clear error if valid
                        existing_pairs.discard(prev_pair)  # Remove old value
                        existing_pairs.add(new_pair)  # Add new value
                        st.session_state.functions[key]["module"] = new_module
                        st.session_state.functions[key]["class"] = new_class
                        st.rerun()  # Force UI refresh only after all updates

                # Display inline error
                if st.session_state.function_errors.get(key):
                    st.error(st.session_state.function_errors[key])

            st.divider()

        # Remove input field if button was pressed
        if to_remove is not None:
            remove_input(to_remove)

        # Trigger rerun if required param changed
        if require_change:
            st.rerun()

        # Buttons for adding inputs
        col1, _ = st.columns([1, 2])
        with col1:
            st.button("➕ Add function", on_click=add_input, key="add_function")

        results = {
            f"{v['module']}.{v['class']}": {
                "description": v["description"],
                "parameters": {
                    "type": v["parameters"]["type"],
                    "properties": {
                        param["name"]: {"type": param["type"], "description": param["description"]}
                        for param in v["parameters"]["properties"].values()
                        if param["name"]  # Ensuring 'name' is not empty
                    } if v["parameters"]["properties"] else {},  # Allow empty 'properties'
                    "required": v["parameters"].get("required", [])
                },
            }
            for v in st.session_state.functions.values()
            if v["module"] and v["class"]  # Ensuring both 'module' and 'class' are not empty
        }

        if results != st.session_state.function_results:
            st.session_state.function_results = results
            st.rerun()

    else:
        st.write('Please create or load agent network on the "Create/Load" first.')
