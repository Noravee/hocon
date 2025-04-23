import streamlit as st

from pyhocon import ConfigFactory, HOCONConverter


def substitution_tab_content():

    # Function to add a new input box
    def add_var():
        new_key = max(st.session_state.user_vars.keys(), default=-1) + 1
        st.session_state.user_vars[new_key] = {
            "var": "",
            "sub_value": "",
        }

    # Function to remove a specific input box
    def remove_var(key):
        if len(st.session_state.user_vars) >= 1:
            del st.session_state.user_vars[key]
            update_sub_dict()
            st.rerun()  # Forces immediate UI update

    def update_sub_dict():
        st.session_state.sub_dict = {
            v['var']: v['sub_value']
            for v in st.session_state.user_vars.values()
            if v['var'] and v['sub_value']
        }

    # Initialize a dictionary in session state to store user-defined variables
    if "user_vars" not in st.session_state:
        st.session_state.user_vars = {}
        st.session_state.existing_files = []
        st.session_state.sub_dict = {}
        st.session_state.key_value_file_name = "key_value.hocon"

    st.title("Define Your Variables")
    st.markdown("- Use **\\${key}** or **\\$key** to substitute for value.")
    st.write("- If there are duplicated keys, the bottom one will override the top one.")

    input_keys = list(st.session_state.user_vars.keys())  # Store keys to avoid modifying while iterating

    to_remove = None  # Store keyf to remove

    for key in input_keys:
        cols = st.columns([4, 1])
        with cols[0]:
            prev_key = st.session_state.user_vars[key]["var"]
            new_key = st.text_input("Key", value=st.session_state.user_vars[key]["var"], key=f"var_{key}", help='Key or variable name')
            if new_key != prev_key:
                st.session_state.user_vars[key]["var"] = new_key
                update_sub_dict()
                st.rerun()

            prev_value = st.session_state.user_vars[key]["sub_value"]
            new_value = st.text_area(
                label="Value",
                value=st.session_state.user_vars[key]["sub_value"],
                key=f"sub_{key}",
                help="Value for substition"
            )
            if new_value != prev_value:
                st.session_state.user_vars[key]["sub_value"] = new_value
                update_sub_dict()
                st.rerun()

        with cols[1]:
            if st.button("❌", key=f"remove_var_{key}"):
                to_remove = key  # Mark for removal

        st.divider()

    # Buttons for adding inputs and submitting values
    left, right = st.columns([1, 2], vertical_alignment='center')
    with left:
        st.button("➕ Add Key/Value", on_click=add_var)
    with right:
        uploaded_file = st.file_uploader(
                        label="Upload from File",
                        type=['hocon', 'conf'],
                        key='var_loader',
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

                for key_var, sub_value in config.items():
                    add_var()
                    st.session_state.user_vars[list(st.session_state.user_vars.keys())[-1]]['var'] = key_var
                    st.session_state.user_vars[list(st.session_state.user_vars.keys())[-1]]['sub_value'] = sub_value
                update_sub_dict()
                st.session_state.existing_files.append(file_id)
                st.rerun()

    # Remove input field immediately if button was pressed
    if to_remove is not None:
        remove_var(to_remove)

    # Create dict for substitution
    # st.session_state.sub_dict = {v['var']: v['sub_value'] for v in st.session_state.user_vars.values() if v['var'] and v['sub_value']}

    # Convert dictionary to HOCON config
    config = ConfigFactory.from_dict(st.session_state.sub_dict)

    # Convert to HOCON format and write to file
    hocon_str = HOCONConverter.convert(config, "hocon")

    filename = st.text_input("Enter filename", st.session_state.key_value_file_name)
    if filename != st.session_state.key_value_file_name:
        st.session_state.key_value_file_name = filename

    st.download_button(
        label="💾 Download Key/Value as HOCON File",
        data=hocon_str,
        file_name=st.session_state.key_value_file_name,
        mime="text/plain",
    )
