import streamlit as st

from ._utils import safe_dataframe


def render_tab_tablas(tablas: list):
    for i, tabla in enumerate(tablas):
        st.markdown(f"**Tabla {i + 1}**")
        if len(tabla) > 1:
            df = safe_dataframe(
                [dict(zip(tabla[0], fila)) for fila in tabla[1:]]
            )
        else:
            df = safe_dataframe(tabla)
        st.download_button(
            f"Exportar tabla {i + 1} (CSV)",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"tabla_{i + 1}.csv",
            key=f"tbl_{i}",
        )
        st.dataframe(df, use_container_width=True)
