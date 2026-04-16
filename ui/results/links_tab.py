import streamlit as st

from ._utils import safe_dataframe


def render_tab_links(links: list):
    df = safe_dataframe(links)
    st.download_button(
        "Exportar referencias (CSV)",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="referencias.csv",
    )
    st.dataframe(df, use_container_width=True)
