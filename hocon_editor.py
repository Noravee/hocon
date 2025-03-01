from pyhocon import ConfigFactory, HOCONConverter
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

OPENAI_MODEL_DICT = {
    "gpt-4.5-preview": "gpt-4.5-preview-2025-02-27",
    "gpt-4o": "gpt-4o-2024-08-06",
    "chatgpt-4o-latest": "Latest used in ChatGPT",
    "gpt-4o-mini": "gpt-4o-mini-2024-07-18",
    "o1": "o1-2024-12-17",
    "o1-mini": "o1-mini-2024-09-12",
    "o3-mini": "o3-mini-2025-01-31",
    "o1-preview": "o1-preview-2024-09-12" 
}


with st.sidebar:
    # Initialize session state variables
    if "inputs" not in st.session_state:
        st.session_state.inputs = {0: {"name": "", "instructions": "", "command": "", "tools": []}}  # Store name, instructions, command, and tools per node
        st.session_state.errors = {}  # Store validation errors

    # Function to add a new input box
    def add_input():
        new_key = max(st.session_state.inputs.keys(), default=-1) + 1
        st.session_state.inputs[new_key] = {"name": "", "instructions": "", "command": "", "tools": []}
        st.session_state.errors[new_key] = ""  # Initialize error tracking

    # Function to remove a specific input box
    def remove_input(key):
        if len(st.session_state.inputs) > 1:
            deleted_node = st.session_state.inputs[key]["name"]
            del st.session_state.inputs[key]
            del st.session_state.errors[key]  # Remove associated error

            # Remove deleted node from all connection lists
            for k in st.session_state.inputs:
                st.session_state.inputs[k]['tools'] = [
                    conn for conn in st.session_state.inputs[k]['tools'] if conn != deleted_node
                ]
            st.rerun()  # Forces immediate UI update

    st.title("Agents Input Fields")

    input_keys = list(st.session_state.inputs.keys())  # Store keys to avoid modifying while iterating

    to_remove = None  # Store key to remove
    filters_changed = False  # Track if we need to rerun Streamlit

    # Precompute available options before iterating over inputs
    available_options = [node["name"] for node in st.session_state.inputs.values() if node["name"]]
    existing_names = set(node["name"] for node in st.session_state.inputs.values())

    for key in input_keys:
        cols = st.columns([4, 1])
        with cols[0]:
            # Node name input
            prev_name = st.session_state.inputs[key]["name"]
            new_name = st.text_input("Name", value=prev_name, key=f"input_{key}", help='Name of agent or tool')

            # Enforce uniqueness
            if new_name != prev_name:
                if new_name in existing_names:
                    st.session_state.errors[key] = f"❌ '{new_name}' is already used. Choose a different name."
                else:
                    st.session_state.errors[key] = ""  # Clear error if valid
                    existing_names.discard(prev_name)  # Remove old value
                    existing_names.add(new_name)  # Add new value
                    st.session_state.inputs[key]["name"] = new_name
                    st.rerun()

            # Display inline error if node name is duplicate
            if st.session_state.errors.get(key):
                st.error(st.session_state.errors[key])

        with cols[1]:
            if st.button("❌", key=f"remove_{key}"):
                to_remove = key  # Mark for removal

        # Expander for each input (contains "instructions" and "Connections")
        with st.expander(f"Details for '{st.session_state.inputs[key]['name'] or 'Node'}'"):
            st.session_state.inputs[key]["instructions"] = st.text_area(
                "Instructions", value=st.session_state.inputs[key]["instructions"],
                key=f"instructions_{key}",
                help='text that sets up the agent in detail for its task'
            )
            st.session_state.inputs[key]["command"] = st.text_area(
                "Command", value=st.session_state.inputs[key]["command"],
                key=f"command_{key}",
                help='text that sets the agent in motion after it receives all its inputs'
            )

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

    # Remove input field immediately if button was pressed
    if to_remove is not None:
        remove_input(to_remove)

    # Trigger rerun if filters changed
    if filters_changed:
        st.rerun()

    # Buttons for adding inputs and submitting values
    col1, col2 = st.columns([1, 2])
    with col1:
        st.button("➕ Add Input", on_click=add_input)
    with col2:
        hierarchical = st.toggle("Hierarchical")

    # Display global error message
    if "error_message" in st.session_state and st.session_state.error_message:
        st.error(st.session_state.error_message)
        del st.session_state.error_message  # Remove error after displaying

llm_tab, network_tab, save_tab = st.tabs(["LLM", "Network", "Save HOCON file"])

with llm_tab:
    llm_model = st.selectbox(label='Model',
                             options=list(OPENAI_MODEL_DICT.keys()),
                             help='name of the model to use (i.e. “gpt-4o”, “claude-3-haiku”)')
    temperature = st.slider(label='Temperature', min_value=0.0, max_value=1.0, help='(optional) level of randomnessto use for LLM results')

with network_tab:

    nodes = []
    edges = []

    if "inputs" in st.session_state and st.session_state.inputs:
        for k, v in st.session_state.inputs.items():
            name = v['name']
            if name != '':
                nodes.append(Node(id=name, label=name, size=30))
                if v['tools']:
                    for i in v['tools']:
                        edges.append(Edge(source=name, target=i))

    config = Config(width=750,
                    height=750,
                    directed=True,
                    physics=True,
                    hierarchical=hierarchical,
                    )

    return_value = agraph(nodes=nodes,
                        edges=edges,
                        config=config)

with save_tab:
    data = {
        "llm_config": {
            "model_name": OPENAI_MODEL_DICT[llm_model],
            "temperatur": temperature,
        },
        "tools": [i for i in st.session_state.inputs.values() if i['name'] != '']
    }

    # Convert dictionary to HOCON config
    config = ConfigFactory.from_dict(data)

    # Convert to HOCON format and write to file
    hocon_str = HOCONConverter.convert(config, "hocon")

    filename = st.text_input("Enter filename", "config.hocon")

    st.download_button(
        label="💾 Save HOCON",
        data=hocon_str,
        file_name=filename if filename else "config.hocon",
        mime="text/plain"
    )
