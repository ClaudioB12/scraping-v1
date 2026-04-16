"""
DataHarvest Pro — Sistema Profesional de Recoleccion Web
"""

import os
import sys
import time
import threading
import asyncio

import streamlit as st

from scraper_engine import ScraperEngine
from ui.header    import render_header
from ui.sidebar   import render_sidebar
from ui.dashboard import render_dashboard, render_idle
from ui.results   import render_results

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

st.set_page_config(
    page_title="DataHarvest Pro",
    page_icon="D",
    layout="wide",
    initial_sidebar_state="expanded",
)

_css_path = os.path.join(os.path.dirname(__file__), "styles.css")
with open(_css_path, encoding="utf-8") as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

# ── Estado de sesion ──────────────────────────────────────────────────────────
_defaults = {
    "is_scraping":  False,
    "scraping_ok":  False,
    "stop_flag":    None,
    "thread":       None,
    "tiempo_inicio": None,
    "resultados":   {},
    # _shared: dict Python plano accesible desde el hilo secundario
    # sin pasar por el proxy de Streamlit (evita ScriptRunContext error)
    "_shared": {
        "logs":        [],
        "paginas":     0,
        "max_paginas": 10,
        "url_actual":  "",
        "registros":   0,
        "res_parciales": {},
        "done":        False,
        "resultado":   {},
        "error":       None,
    },
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── UI ────────────────────────────────────────────────────────────────────────
render_header()
sidebar = render_sidebar()

# ── Accion: INICIAR ───────────────────────────────────────────────────────────
if sidebar["start_clicked"] and not st.session_state.is_scraping:

    # Reiniciar el dict compartido (plain Python, seguro desde cualquier hilo)
    shared = {
        "logs":          [],
        "paginas":       0,
        "max_paginas":   sidebar["config"]["max_paginas"],
        "url_actual":    "",
        "registros":     0,
        "res_parciales": {},
        "done":          False,
        "resultado":     {},
        "error":         None,
    }
    st.session_state["_shared"]      = shared
    st.session_state.scraping_ok     = False
    st.session_state.resultados      = {}
    st.session_state.tiempo_inicio   = time.time()

    stop_flag = threading.Event()
    st.session_state.stop_flag = stop_flag

    # Callbacks que escriben SOLO al dict plano, nunca a st.session_state
    def _log_cb(msg, nivel="info"):
        shared["logs"].append({"msg": msg, "nivel": nivel})

    def _progress_cb(paginas, total, url, res):
        shared["paginas"]      = paginas
        shared["max_paginas"]  = total
        shared["url_actual"]   = url
        shared["registros"]    = sum(
            len(v) for v in res.values() if isinstance(v, list)
        )
        shared["res_parciales"] = res

    engine = ScraperEngine(sidebar["config"], log_callback=_log_cb)

    def _run():
        try:
            result = engine.scrape(
                sidebar["url"],
                sidebar["opciones"],
                stop_flag=stop_flag,
                progress_callback=_progress_cb,
            )
            shared["resultado"] = result
        except Exception as exc:
            shared["error"] = str(exc)
            shared["logs"].append({"msg": f"Error critico: {exc}", "nivel": "err"})
        finally:
            shared["done"] = True

    t = threading.Thread(target=_run, daemon=True)
    st.session_state.thread      = t
    st.session_state.is_scraping = True
    t.start()

# ── Accion: DETENER ───────────────────────────────────────────────────────────
if sidebar["stop_clicked"] and st.session_state.is_scraping:
    if st.session_state.stop_flag:
        st.session_state.stop_flag.set()
        st.session_state["_shared"]["logs"].append({
            "msg": "Solicitud de detencion enviada al motor de rastreo.",
            "nivel": "warn",
        })

# ── Comprobar si el hilo termino ──────────────────────────────────────────────
if st.session_state.is_scraping:
    shared = st.session_state["_shared"]
    if shared.get("done"):
        st.session_state.is_scraping = False
        resultado = shared.get("resultado", {})
        if resultado:
            st.session_state.resultados  = resultado
            st.session_state.scraping_ok = True
        elif shared.get("error"):
            st.error(f"Error en el proceso de recoleccion: {shared['error']}")

# ── Area principal ────────────────────────────────────────────────────────────
if st.session_state.is_scraping:
    render_dashboard()
    time.sleep(1)
    st.rerun()

elif st.session_state.scraping_ok and st.session_state.resultados:
    render_results(
        st.session_state.resultados,
        sidebar["config"]["carpeta_salida"],
    )

else:
    render_idle()
