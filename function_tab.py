from pyhocon import ConfigFactory, HOCONConverter
import streamlit as st

TYPES = ['string', 'number', 'integer', 'object', 'array', 'boolean', 'null']

def function_tab_content():

    # Initialize session state variables
    if "functions" not in st.session_state:
        st.session_state.functions = {}
        st.session_state.function_errors = {}  # Store validation errors
        st.session_state.function_results = {}
        st.session_state.function_file_name = "function.hocon"

    # Function to add a new input box
    def add_input():
        new_key = max(st.session_state.functions.keys(), default=-1) + 1
        st.session_state.functions[new_key] = {"name": "", "description": "", "parameters": {"type": "object", "properties": {}, "required": []}, "module": "", "class": ""}
        st.session_state.function_errors[new_key] = ""  # Initialize error tracking

    # Function to add a new parameter
    def add_param(function_key_index: int):
        new_key = max(st.session_state.functions[function_key_index]['parameters']['properties'].keys(), default=-1) + 1
        # st.session_state.functions[function_key_index]['parameters']['properties'][new_key] = {"name": "", "type": [], "description": ""}
        st.session_state.functions[function_key_index]['parameters']['properties'][new_key] = {"name": "", "type": "", "description": ""}

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
            prev_func_name = st.session_state.functions[key]["name"]
            new_func_name = st.text_input(
                label="Function name",
                value=st.session_state.functions[key]["name"],
                key=f"func_name_{key}",
                help="This is used as a reference to agents only, and is not included in the HOCON file."
            )
            if new_func_name != prev_func_name:
                st.session_state.functions[key]["name"] = new_func_name
                st.rerun()

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

                    def safe_index(lst, item):
                        return lst.index(item) if item in lst else None
                    # new_types = st.multiselect(
                    #     label="Parameter type",
                    #     options=TYPES,
                    #     default=st.session_state.functions[key]["parameters"]["properties"][param_key]["type"],
                    #     key=f"input_{key}_param_type_{param_key}",
                    # )
                    new_types = st.selectbox(
                        label="Parameter type",
                        options=TYPES,
                        index=safe_index(TYPES, st.session_state.functions[key]["parameters"]["properties"][param_key]["type"]),
                        key=f"input_{key}_param_type_{param_key}",
                    )
                    if new_types != st.session_state.functions[key]["parameters"]["properties"][param_key]["type"]:
                        st.session_state.functions[key]["parameters"]["properties"][param_key]["type"] = new_types
                        st.session_state[expander_key] = True
                        st.rerun()

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
            filtered_options = [conn for conn in st.session_state.functions[key]['parameters']['required'] if conn in param_options]
            if filtered_options != st.session_state.functions[key]['parameters']['required']:
                st.session_state.functions[key]['parameters']['required'] = filtered_options
                require_change = True  # Mark as changed
            required = st.multiselect(
                label='Required parameter',
                options=param_options,
                default=st.session_state.functions[key]['parameters']['required'],
                key=f'required_{key}',
                help='Required parameters'
            )

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
    col1, col2 = st.columns([1, 2], vertical_alignment='center')
    with col1:
        st.button("➕ Add function", on_click=add_input, key="add_function")

    with col2:
        uploaded_file = st.file_uploader(
                        label="Upload from File",
                        type=['hocon', 'conf'],
                        key='func_loader',
                        )

        if uploaded_file:
            file_id = uploaded_file.file_id
            if file_id not in st.session_state.existing_files:

                try:
                    # Attempt to load as a HOCON or CONF file
                    if uploaded_file.name.endswith(".hocon") or uploaded_file.name.endswith(".conf") or uploaded_file.name.endswith(".json"):
                        config = ConfigFactory.parse_string(uploaded_file.getvalue().decode("utf-8"))
                    else:
                        st.error("Unsupported file format!")

                except Exception as e:
                    st.error(f"An error occurred while loading the file: {e}")

                for func_name, func_dict in config.items():
                    add_input()
                    new_key = max(st.session_state.functions.keys())  # Faster than list()[-1]

                    function_data = func_dict.get('function', {})
                    parameters = function_data.get('parameters', {})
                    properties = parameters.get('properties', {})

                    st.session_state.functions[new_key]['name'] = func_name
                    st.session_state.functions[new_key]['description'] = function_data.get('description', '')

                    class_path = func_dict.get('class', '').split('.')
                    st.session_state.functions[new_key]['module'] = class_path[0] if len(class_path) > 1 else ''
                    st.session_state.functions[new_key]['class'] = class_path[1] if len(class_path) > 1 else ''

                    st.session_state.functions[new_key]['parameters']['required'] = parameters.get('required', [])

                    for param_index, (p_name, p_val) in enumerate(properties.items()):
                        add_param(new_key)
                        param_entry = st.session_state.functions[new_key]['parameters']['properties'][param_index]
                        param_entry['name'] = p_name
                        param_entry['type'] = p_val.get('type', '')
                        param_entry['description'] = p_val.get('description', '')

                st.session_state.existing_files.append(file_id)
                st.rerun()

    results = {
        v['name']: {
            'function': {
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
            },
            'class': "" if not v["module"] and not v["class"] else f"{v['module']}.{v['class']}"
        }
        for v in st.session_state.functions.values() if v['name']
    }

    if results != st.session_state.function_results:
        st.session_state.function_results = results
        st.rerun()

    # Convert dictionary to HOCON config
    config = ConfigFactory.from_dict(st.session_state.function_results)

    # Convert to HOCON format and write to file
    hocon_str = HOCONConverter.convert(config, "hocon")

    filename = st.text_input("Enter filename", st.session_state.function_file_name)
    if filename != st.session_state.function_file_name:
        st.session_state.function_file_name = filename

    st.download_button(
        label="💾 Download function spec as HOCON File",
        data=hocon_str,
        file_name=st.session_state.function_file_name,
        mime="text/plain",
    )
