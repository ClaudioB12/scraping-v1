import streamlit as st


def render_tab_documentos(res: dict, carpeta_salida: str):
    st.info(f"Archivos localizados. Directorio de salida: **{carpeta_salida}**")

    if res.get("archivos_descargados"):
        st.subheader("Archivos almacenados")
        for ad in res["archivos_descargados"]:
            st.markdown(f"- **{ad}**")

    if res.get("archivos"):
        st.subheader("Referencias detectadas")
        for arch in res["archivos"]:
            st.markdown(
                f"- **[{arch.get('tipo', 'FILE')}]** "
                f"<a href='{arch.get('url', '#')}' download target='_blank'>"
                f"Descargar — {arch.get('nombre', 'Recurso')}</a>",
                unsafe_allow_html=True,
            )
