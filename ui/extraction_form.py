import streamlit as st


def render_form(sidebar_cfg: dict) -> tuple:
    """
    Renderiza el formulario principal (modo, opciones de contenido, URL).

    Parametros
    ----------
    sidebar_cfg : dict
        Config devuelta por render_sidebar(), incluye headless_ph y paginas_ph.

    Devuelve
    --------
    (url: str, opciones: dict, run_cfg: dict)
    """
    headless_ph = sidebar_cfg["headless_ph"]
    paginas_ph  = sidebar_cfg["paginas_ph"]

    col_izq, col_der = st.columns([2, 3])

    with col_izq:
        st.markdown('<div class="dh-label">Modalidad de operacion</div>', unsafe_allow_html=True)
        modo = st.radio(
            "modo",
            options=["Extraccion Automatizada", "Supervision Asistida"],
            help=(
                "Automatizada recolecta de forma autonoma. "
                "Asistida despliega un navegador para seleccion manual."
            ),
            label_visibility="collapsed",
        )
        modo_interno = "manual" if "Asistida" in modo else "automatico"

        st.markdown(
            '<div class="dh-label" style="margin-top:24px;">Configuracion de rastreo</div>',
            unsafe_allow_html=True,
        )

        if modo_interno == "automatico":
            headless    = headless_ph.checkbox("Ejecucion en segundo plano", value=True)
            max_paginas = paginas_ph.slider(
                "Profundidad maxima de rastreo",
                min_value=1, max_value=30, value=10,
                help="Numero de paginas adicionales que el motor explorara siguiendo hipervinculos.",
            )
        else:
            headless_ph.empty()
            paginas_ph.empty()
            headless    = False
            max_paginas = 1
            st.caption("Modo supervisado: el navegador permanece visible en todo momento.")

    with col_der:
        st.markdown('<div class="dh-label">Contenido a recolectar</div>', unsafe_allow_html=True)
        if modo_interno == "automatico":
            opciones = _render_opciones_auto()
        else:
            opciones = _render_opciones_manual()

    # ── URL + boton ──────────────────────────────────────────────────────────
    st.markdown(
        '<div class="dh-label" style="margin-top:8px;">Destino de analisis</div>',
        unsafe_allow_html=True,
    )
    col_url, col_btn = st.columns([6, 1])
    with col_url:
        url_input = st.text_input(
            "URL",
            placeholder="https://sitio-objetivo.com",
            label_visibility="collapsed",
        )
    with col_btn:
        ejecutar = st.button("EJECUTAR", use_container_width=True)

    mensaje_spinner = (
        "Procesando. El motor esta recorriendo el sitio y recopilando datos."
        if modo_interno == "automatico"
        else "Navegador activo. Interactue con la ventana para seleccionar recursos y cierrela al finalizar."
    )

    run_cfg = {
        "modo":            modo_interno,
        "headless":        headless,
        "max_paginas":     max_paginas,
        "scroll_pagina":   True,
        "simular_humano":  True,
        "ejecutar":        ejecutar and bool(url_input.strip()),
        "mensaje_spinner": mensaje_spinner,
    }

    return url_input.strip(), opciones, run_cfg


# ── Helpers privados ─────────────────────────────────────────────────────────

def _render_opciones_auto() -> dict:
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        st.markdown(
            '<div class="opt-cell"><span class="opt-title">Texto</span>'
            '<span class="opt-desc">Parrafos y bloques</span></div>',
            unsafe_allow_html=True,
        )
        texto = st.checkbox("Activar", value=True, key="chk_texto", label_visibility="collapsed")
    with r1c2:
        st.markdown(
            '<div class="opt-cell"><span class="opt-title">Titulos</span>'
            '<span class="opt-desc">Encabezados H1-H6</span></div>',
            unsafe_allow_html=True,
        )
        titulos = st.checkbox("Activar", value=True, key="chk_titulos", label_visibility="collapsed")
    with r1c3:
        st.markdown(
            '<div class="opt-cell"><span class="opt-title">Hipervinculos</span>'
            '<span class="opt-desc">URLs y referencias</span></div>',
            unsafe_allow_html=True,
        )
        links = st.checkbox("Activar", value=True, key="chk_links", label_visibility="collapsed")
    with r1c4:
        st.markdown(
            '<div class="opt-cell"><span class="opt-title">Documentos</span>'
            '<span class="opt-desc">PDF, DOCX, ZIP</span></div>',
            unsafe_allow_html=True,
        )
        archivos = st.checkbox("Activar", value=True, key="chk_arch", label_visibility="collapsed")

    r2c1, r2c2, r2c3, _ = st.columns(4)
    with r2c1:
        st.markdown(
            '<div class="opt-cell"><span class="opt-title">Imagenes</span>'
            '<span class="opt-desc">Recursos graficos</span></div>',
            unsafe_allow_html=True,
        )
        imagenes = st.checkbox("Activar", value=True, key="chk_imgs", label_visibility="collapsed")
    with r2c2:
        st.markdown(
            '<div class="opt-cell"><span class="opt-title">Tablas</span>'
            '<span class="opt-desc">Estructuras HTML</span></div>',
            unsafe_allow_html=True,
        )
        tablas = st.checkbox("Activar", value=True, key="chk_tablas", label_visibility="collapsed")
    with r2c3:
        st.markdown(
            '<div class="opt-cell"><span class="opt-title">Video</span>'
            '<span class="opt-desc">MP4, WebM, HLS</span></div>',
            unsafe_allow_html=True,
        )
        videos = st.checkbox("Activar", value=True, key="chk_videos", label_visibility="collapsed")

    return {
        "texto":    texto,
        "titulos":  titulos,
        "links":    links,
        "archivos": archivos,
        "imagenes": imagenes,
        "tablas":   tablas,
        "videos":   videos,
    }


def _render_opciones_manual() -> dict:
    st.markdown("""
    <div style="background:#1a1f2e;border:1px solid #2e3347;border-left:3px solid #e94560;
                border-radius:8px;padding:18px 20px;color:#8892a4;font-size:0.85rem;line-height:1.6;">
        En la modalidad supervisada el usuario determina que recursos capturar
        interactuando directamente con el navegador desplegado. Los selectores
        de contenido no aplican en este modo.
    </div>
    """, unsafe_allow_html=True)
    return {k: False for k in ["texto", "titulos", "links", "archivos", "imagenes", "tablas", "videos"]}
