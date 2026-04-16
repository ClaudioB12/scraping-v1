import streamlit as st


def render_sidebar() -> dict:
    """
    Panel lateral completo: URL, controles START/STOP, opciones de contenido
    y configuracion avanzada.

    Devuelve
    --------
    dict con:
      url, opciones, config, start_clicked, stop_clicked
    """
    with st.sidebar:

        # ── Logo / titulo ─────────────────────────────────────────────────────
        st.markdown("""
<div style="text-align:center;padding:18px 0 12px 0;">
  <div style="color:#e94560;font-size:1.3rem;font-weight:900;letter-spacing:4px;">
    DATAHARVEST
  </div>
  <div style="color:#3a3f52;font-size:0.65rem;letter-spacing:3px;margin-top:2px;">
    PRO · v2.0
  </div>
</div>
<hr style="border-color:#1e2533;margin:0 0 16px 0;">
""", unsafe_allow_html=True)

        # ── URL objetivo ──────────────────────────────────────────────────────
        st.markdown('<div class="dh-label">URL objetivo</div>', unsafe_allow_html=True)
        url = st.text_input(
            "url",
            placeholder="https://sitio-objetivo.com",
            label_visibility="collapsed",
            key="sb_url",
        )

        # ── Botones START / STOP ──────────────────────────────────────────────
        is_scraping = st.session_state.get("is_scraping", False)

        if not is_scraping:
            start_clicked = st.button(
                "INICIAR RASTREO",
                use_container_width=True,
                type="primary",
                disabled=not bool(url.strip()),
            )
            stop_clicked = False
        else:
            start_clicked = False
            stop_clicked = st.button(
                "DETENER RASTREO",
                use_container_width=True,
                type="secondary",
            )

        st.markdown("<hr style='border-color:#1e2533;margin:16px 0;'>", unsafe_allow_html=True)

        # ── Modalidad ─────────────────────────────────────────────────────────
        st.markdown('<div class="dh-label">Modalidad</div>', unsafe_allow_html=True)
        modo = st.radio(
            "modo",
            ["Automatizada", "Asistida"],
            label_visibility="collapsed",
            horizontal=True,
            key="sb_modo",
        )
        modo_interno = "manual" if modo == "Asistida" else "automatico"

        st.markdown("<hr style='border-color:#1e2533;margin:16px 0;'>", unsafe_allow_html=True)

        # ── Contenido a recolectar ────────────────────────────────────────────
        st.markdown('<div class="dh-label">Contenido</div>', unsafe_allow_html=True)

        if modo_interno == "automatico":
            c1, c2 = st.columns(2)
            with c1:
                txt  = st.checkbox("Texto",        value=True,  key="op_texto")
                lnk  = st.checkbox("Hipervinculos", value=True,  key="op_links")
                img  = st.checkbox("Imagenes",     value=True,  key="op_imgs")
                vid  = st.checkbox("Video",        value=True,  key="op_video")
            with c2:
                tit  = st.checkbox("Titulos",      value=True,  key="op_tit")
                arc  = st.checkbox("Documentos",   value=True,  key="op_arch")
                tbl  = st.checkbox("Tablas",       value=True,  key="op_tablas")
            opciones = {
                "texto": txt, "titulos": tit, "links": lnk,
                "archivos": arc, "imagenes": img, "tablas": tbl, "videos": vid,
            }
        else:
            st.caption("En modo asistido el usuario selecciona los recursos directamente en el navegador.")
            opciones = {k: False for k in ["texto", "titulos", "links", "archivos", "imagenes", "tablas", "videos"]}

        st.markdown("<hr style='border-color:#1e2533;margin:16px 0;'>", unsafe_allow_html=True)

        # ── Configuracion avanzada ────────────────────────────────────────────
        with st.expander("Configuracion avanzada", expanded=False):
            navegador = st.selectbox(
                "Motor de navegacion",
                ["chromium", "firefox", "webkit"],
                index=0,
                key="sb_nav",
            )
            max_paginas = st.slider(
                "Paginas maximas",
                min_value=1, max_value=50, value=10,
                key="sb_maxpag",
                disabled=(modo_interno == "manual"),
            )
            delay = st.slider(
                "Delay entre paginas (seg)",
                min_value=0.5, max_value=5.0, value=2.0, step=0.5,
                key="sb_delay",
            )
            headless = st.checkbox(
                "Ejecucion en segundo plano",
                value=(modo_interno == "automatico"),
                key="sb_headless",
                disabled=(modo_interno == "manual"),
            )
            stealth = st.checkbox("Enmascaramiento anti-deteccion", value=True, key="sb_stealth")
            carpeta_salida = st.text_input("Directorio de almacenamiento", "data", key="sb_carpeta")

            st.markdown('<div class="dh-label" style="margin-top:12px;">Descarga de video</div>', unsafe_allow_html=True)
            descargar_hls   = st.checkbox("HLS/DASH via ffmpeg", value=False, key="sb_hls",
                                          help="Requiere ffmpeg instalado en el sistema.")
            descargar_ytdlp = st.checkbox("Plataformas via yt-dlp", value=False, key="sb_ytdlp",
                                          help="Requiere: pip install yt-dlp")

    config = {
        "modo":            modo_interno,
        "navegador":       navegador,
        "headless":        headless if modo_interno == "automatico" else False,
        "stealth":         stealth,
        "carpeta_salida":  carpeta_salida,
        "scroll_pagina":   True,
        "simular_humano":  True,
        "max_paginas":     max_paginas if modo_interno == "automatico" else 1,
        "delay":           delay,
        "descargar_hls":   descargar_hls,
        "descargar_ytdlp": descargar_ytdlp,
    }

    return {
        "url":           url.strip(),
        "opciones":      opciones,
        "config":        config,
        "start_clicked": start_clicked,
        "stop_clicked":  stop_clicked,
    }
