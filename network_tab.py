import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config


def network_tab_content():
    if 'hierarchical' in st.session_state:
        st.title("Network of Agents")

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
                        hierarchical=st.session_state.hierarchical,
                        )

        st.session_state.hierarchical = st.toggle("Hierarchical view")

        agraph(nodes=nodes,
            edges=edges,
            config=config)

    else:
        st.write('Please create or load agent network on the "Create/Load" first.')
