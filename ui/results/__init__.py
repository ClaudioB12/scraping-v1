import streamlit as st
from .documents_tab import render_tab_documentos
from .video_tab      import render_tab_video
from .images_tab     import render_tab_imagenes
from .tables_tab     import render_tab_tablas
from .text_tab       import render_tab_texto
from .links_tab      import render_tab_links


def render_results(res: dict, carpeta_salida: str):
    st.markdown("---")
    st.markdown('<div class="dh-label">Resultados de la recoleccion</div>', unsafe_allow_html=True)

    if res.get("mensaje"):
        st.success(res["mensaje"])
        st.balloons()
        return

    tabs_disponibles = []
    if res.get("archivos") or res.get("archivos_descargados"): tabs_disponibles.append("Documentos")
    if res.get("videos"):   tabs_disponibles.append("Video")
    if res.get("imagenes"): tabs_disponibles.append("Imagenes")
    if res.get("tablas"):   tabs_disponibles.append("Tablas")
    if res.get("texto"):    tabs_disponibles.append("Texto")
    if res.get("links"):    tabs_disponibles.append("Hipervinculos")

    if not tabs_disponibles:
        st.warning("No se identifico contenido relevante con los criterios de seleccion aplicados.")
        return

    tabs     = st.tabs(tabs_disponibles)
    tab_iter = iter(tabs)

    if res.get("archivos") or res.get("archivos_descargados"):
        with next(tab_iter):
            render_tab_documentos(res, carpeta_salida)
    if res.get("videos"):
        with next(tab_iter):
            render_tab_video(res["videos"])
    if res.get("imagenes"):
        with next(tab_iter):
            render_tab_imagenes(res["imagenes"])
    if res.get("tablas"):
        with next(tab_iter):
            render_tab_tablas(res["tablas"])
    if res.get("texto"):
        with next(tab_iter):
            render_tab_texto(res["texto"])
    if res.get("links"):
        with next(tab_iter):
            render_tab_links(res["links"])
