import pandas as pd
import streamlit as st


def render_tab_video(videos: list):
    df = pd.DataFrame(videos)
    st.metric("Recursos audiovisuales identificados", len(videos))

    tipos = df["tipo"].value_counts().to_dict() if "tipo" in df.columns else {}
    if tipos:
        cols = st.columns(min(len(tipos), 4))
        for i, (tipo, cnt) in enumerate(tipos.items()):
            cols[i % len(cols)].metric(tipo, cnt)

    st.download_button(
        "Exportar registro completo (CSV)",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="audiovisual.csv",
    )

    hls      = [v for v in videos if v.get("tipo") in ("hls_stream", "dash_stream")]
    embeds   = [v for v in videos if v.get("tipo") == "iframe_embed"]
    directos = [v for v in videos if v.get("tipo") not in ("iframe_embed", "hls_stream", "dash_stream")]

    if hls:
        st.subheader("Transmisiones en tiempo real (HLS / DASH)")
        for v in hls:
            col_a, col_b, col_c = st.columns([3, 1, 1])
            with col_a:
                st.markdown(f"`{v['tipo'].upper()}` — {v.get('titulo', '') or v['src'][:60]}")
                st.code(v["src"], language=None)
            with col_b:
                if v.get("descargado"):
                    st.success(f"Guardado: {v['descargado'][:20]}")
                else:
                    st.warning("No procesado")
            with col_c:
                st.markdown(
                    f"<a href='{v['src']}' target='_blank'>"
                    f"<button style='padding:6px 14px;background:#e94560;color:white;"
                    f"border:none;border-radius:6px;cursor:pointer;font-weight:600;"
                    f"letter-spacing:0.5px;'>Acceder</button></a>",
                    unsafe_allow_html=True,
                )

    if directos:
        st.subheader("Archivos de video directos")
        for v in directos:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"`{v['tipo'].upper()}` — {v.get('titulo', '') or v['src'][:60]}")
                st.code(v["src"], language=None)
            with col_b:
                st.markdown(
                    f"<a href='{v['src']}' target='_blank' download>"
                    f"<button style='padding:6px 14px;background:#0f3460;color:white;"
                    f"border:1px solid #e94560;border-radius:6px;cursor:pointer;"
                    f"font-weight:600;letter-spacing:0.5px;'>Descargar</button></a>",
                    unsafe_allow_html=True,
                )

    if embeds:
        st.subheader("Contenido incrustado (YouTube / Vimeo / otras plataformas)")
        for v in embeds:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"- [{v.get('titulo') or v['src'][:60]}]({v['src']})")
            with col_b:
                if v.get("descargado"):
                    st.success(f"Capturado: {v['descargado'][:20]}")
                else:
                    st.info("Active yt-dlp en el panel lateral")
