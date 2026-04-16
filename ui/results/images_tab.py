import pandas as pd
import streamlit as st


def render_tab_imagenes(imagenes: list):
    df = pd.DataFrame(imagenes)
    st.download_button(
        "Exportar registro (CSV)",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="imagenes.csv",
    )
    st.dataframe(df, use_container_width=True)
