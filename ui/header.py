import streamlit as st


def render_header():
    st.markdown("""
<div class="dh-header">
    <div class="dh-badge">v2.0 PRO</div>
    <h1>DATAHARVEST PRO</h1>
    <p>Sistema profesional de recoleccion y analisis de contenido web</p>
</div>
""", unsafe_allow_html=True)
