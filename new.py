import streamlit as st
import string

from pyhocon import ConfigFactory, HOCONConverter


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
        # del st.session_state.var_errors[key]  # Remove associated error

        st.rerun()  # Forces immediate UI update


# Initialize a dictionary in session state to store user-defined variables
if "user_vars" not in st.session_state:
    st.session_state.user_vars = {}
    st.session_state.existing_files = []
    st.session_state.formatted_text = ""
    st.session_state.sub_dict = {}

st.title("Define Your Variables")
st.write("- Use **${key}** to substitute for value.")
st.write("- If there are duplicated keys, the bottom one will override the top one.")

input_keys = list(st.session_state.user_vars.keys())  # Store keys to avoid modifying while iterating

to_remove = None  # Store keyf to remove

# Precompute available options before iterating over inputs
existing_vars = set(node["var"] for node in st.session_state.user_vars.values())

for key in input_keys:
    # st.session_state.var_errors[key] = ''
    cols = st.columns([4, 1])
    with cols[0]:
        # Node name input
        # prev_var = st.session_state.user_vars[key]["var"]
        # new_var = st.text_input("Key", value=prev_var, key=f"var_{key}", help='Key or variable name')
        st.session_state.user_vars[key]["var"] = st.text_input("Key", value=st.session_state.user_vars[key]["var"], key=f"var_{key}", help='Key or variable name')

        # # Enforce uniqueness
        # if new_var != prev_var:
        #     if new_var in existing_vars:
        #         st.session_state.var_errors[key] = f"❌ '{new_var}' is already in used. Choose a different key."
        #     else:
        #         st.session_state.var_errors[key] = ""  # Clear error if valid
        #         existing_vars.discard(prev_var)  # Remove old value
        #         existing_vars.add(new_var)  # Add new value
        #         st.session_state.user_vars[key]["var"] = new_var
        #         st.rerun()

        # Display inline error if node name is duplicate
        # if st.session_state.var_errors.get(key):
        #     st.error(st.session_state.var_errors[key])

        st.session_state.user_vars[key]["sub_value"] = st.text_area(
            label="Value",
            value=st.session_state.user_vars[key]["sub_value"],
            key=f"sub_{key}",
            help="Value for substition"
        )

    with cols[1]:
        if st.button("❌", key=f"remove_{key}"):
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

                st.write(config)
                st.write(st.session_state.user_vars.keys())

            except Exception as e:
                st.error(f"An error occurred while loading the file: {e}")

            for key_var, sub_value in config.items():
                add_var()
                st.session_state.user_vars[list(st.session_state.user_vars.keys())[-1]]['var'] = key_var
                st.session_state.user_vars[list(st.session_state.user_vars.keys())[-1]]['sub_value'] = sub_value

            st.session_state.existing_files.append(file_id)
            st.rerun()

# Remove input field immediately if button was pressed
if to_remove is not None:
    remove_var(to_remove)

# Create dict for substitution
st.session_state.sub_dict = {v['var']: v['sub_value'] for v in st.session_state.user_vars.values() if v['var']}

# Convert dictionary to HOCON config
config = ConfigFactory.from_dict(st.session_state.sub_dict)

# Convert to HOCON format and write to file
hocon_str = HOCONConverter.convert(config, "hocon")

filename = st.text_input("Enter filename", "key_value.hocon")

#disabled = any(list(st.session_state.var_errors.values()))

st.download_button(
    label="💾 Download Key/Value as HOCON File",
    data=hocon_str,
    file_name=filename if filename else "key_value.hocon",
    mime="text/plain",
    # disabled=disabled
)

# if disabled:
#     st.error('🛠️ Please fix the error before downloading.')

st.header("Enter Template Text")
template = st.text_area(
    "Template",
    help="Use keys defined above as ${key}"
)

# Use string.Template for safe substitution
template_obj = string.Template(template)
st.session_state.formatted_text = template_obj.safe_substitute(st.session_state.sub_dict)  # Leaves unknown placeholders unchanged

st.write("Formatted Output:")
st.write(st.session_state.formatted_text)
st.write(st.session_state.sub_dict)
