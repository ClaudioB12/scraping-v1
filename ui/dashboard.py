import time
import streamlit as st


_NIVEL_COLOR = {
    "ok":   "#4ade80",
    "err":  "#f87171",
    "warn": "#fbbf24",
    "info": "#8892a4",
}
_NIVEL_LABEL = {
    "ok":   "OK  ",
    "err":  "ERR ",
    "warn": "WARN",
    "info": "INFO",
}


def render_idle():
    """Pantalla de bienvenida cuando no hay scraping activo."""
    st.markdown("""
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
            min-height:55vh;text-align:center;gap:16px;">
  <div style="color:#2e3347;font-size:4rem;font-weight:900;letter-spacing:6px;">
    DATAHARVEST
  </div>
  <div style="color:#3a3f52;font-size:0.78rem;letter-spacing:4px;text-transform:uppercase;">
    Sistema profesional de recoleccion y analisis de contenido web
  </div>
  <div style="margin-top:24px;color:#3a3f52;font-size:0.82rem;line-height:1.8;">
    Introduce una URL en el panel lateral y pulsa
    <strong style="color:#e94560;">INICIAR RASTREO</strong>
  </div>
</div>
""", unsafe_allow_html=True)


def render_dashboard():
    """
    Dashboard en vivo.
    Lee del dict compartido st.session_state["_shared"], que el hilo
    secundario modifica directamente sin pasar por el proxy de Streamlit.
    """
    shared       = st.session_state.get("_shared", {})
    paginas      = shared.get("paginas", 0)
    max_paginas  = shared.get("max_paginas", 10)
    registros    = shared.get("registros", 0)
    url_actual   = shared.get("url_actual", "Inicializando...")
    logs         = shared.get("logs", [])
    res_parciales = shared.get("res_parciales", {})
    tiempo_inicio = st.session_state.get("tiempo_inicio")

    elapsed = int(time.time() - tiempo_inicio) if tiempo_inicio else 0
    mins, secs = divmod(elapsed, 60)
    tiempo_str = f"{mins:02d}:{secs:02d}"

    # ── Indicador de estado ───────────────────────────────────────────────────
    st.markdown("""
<div class="dh-status-bar">
  <span class="dh-pulse"></span>
  <span style="color:#e94560;font-size:0.72rem;font-weight:700;letter-spacing:2px;">
    RASTREO EN CURSO
  </span>
</div>
""", unsafe_allow_html=True)

    # ── Métricas ──────────────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    m1.metric("Paginas visitadas",   f"{paginas} / {max_paginas}")
    m2.metric("Registros obtenidos", registros)
    m3.metric("Tiempo transcurrido", tiempo_str)

    # ── Barra de progreso ─────────────────────────────────────────────────────
    progreso = min(paginas / max_paginas, 1.0) if max_paginas > 0 else 0
    st.markdown(
        f'<div class="dh-label" style="margin-top:20px;">Progreso — {int(progreso * 100)}%</div>',
        unsafe_allow_html=True,
    )
    st.progress(progreso)
    if url_actual and url_actual != "Inicializando...":
        st.caption(f"Procesando: {url_actual[:90]}")

    # ── Registros por categoría en tiempo real ────────────────────────────────
    tipos_con_datos = {
        k: len(v) for k, v in res_parciales.items()
        if isinstance(v, list) and v
    }
    if tipos_con_datos:
        st.markdown(
            '<div class="dh-label" style="margin-top:20px;">Registros por categoria</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(min(len(tipos_con_datos), 4))
        for i, (tipo, cnt) in enumerate(tipos_con_datos.items()):
            cols[i % len(cols)].metric(tipo.capitalize(), cnt)

    # ── Log dinámico ──────────────────────────────────────────────────────────
    st.markdown(
        '<div class="dh-label" style="margin-top:20px;">Registro de actividad</div>',
        unsafe_allow_html=True,
    )
    ultimos = logs[-30:]
    lineas = []
    for entry in reversed(ultimos):
        nivel = entry.get("nivel", "info")
        color = _NIVEL_COLOR.get(nivel, "#8892a4")
        label = _NIVEL_LABEL.get(nivel, "INFO")
        msg   = entry.get("msg", "")
        lineas.append(
            f'<span style="color:{color};font-family:monospace;font-size:0.78rem;">'
            f'[{label}]</span> '
            f'<span style="color:#cdd6f4;font-size:0.78rem;">{msg}</span>'
        )
    html_log = (
        "<br>".join(lineas)
        if lineas
        else '<span style="color:#3a3f52;font-size:0.78rem;">Esperando actividad...</span>'
    )
    st.markdown(f'<div class="dh-log-box">{html_log}</div>', unsafe_allow_html=True)
