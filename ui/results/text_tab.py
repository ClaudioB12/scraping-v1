import streamlit as st

from ._utils import safe_dataframe


def render_tab_texto(texto: list):
    df = safe_dataframe(texto)
    st.download_button(
        "Exportar contenido (CSV)",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="contenido_texto.csv",
    )
    st.dataframe(df, use_container_width=True)
