import os
import json
import pandas as pd
from pathlib import Path


def _ruta(carpeta: str, nombre: str, ext: str) -> str:
    os.makedirs(carpeta, exist_ok=True)
    nombre_limpio = nombre.replace(".", "_").replace("/", "_")[:50]
    return os.path.join(carpeta, f"{nombre_limpio}.{ext}")


def exportar_csv(resultados: dict, carpeta: str, nombre: str) -> str:
    """
    Exporta todos los resultados en un CSV unificado con secciones.
    Cada tipo de dato tiene su propio bloque separado por líneas en blanco.
    """
    ruta = _ruta(carpeta, nombre, "csv")
    lineas = []

    def seccion(titulo, filas):
        if not filas:
            return
        lineas.append(f"# === {titulo.upper()} ===")
        if filas and isinstance(filas[0], dict):
            headers = list(filas[0].keys())
            lineas.append(",".join(f'"{h}"' for h in headers))
            for fila in filas:
                lineas.append(",".join(
                    f'"{str(fila.get(k, "")).replace(chr(34), chr(39))}"' for k in headers
                ))
        else:
            for fila in filas:
                texto = str(fila).replace('"', "'")
                lineas.append(f'"{texto}"')
        lineas.append("")

    info = resultados.get("info_pagina", {})
    if info:
        lineas.append("# === INFORMACIÓN DE LA PÁGINA ===")
        for k, v in info.items():
            lineas.append(f'"{k}","{str(v).replace(chr(34), chr(39))}"')
        lineas.append("")

    seccion("Títulos",             resultados.get("titulos", []))
    seccion("Texto",               [{"parrafo": t} for t in resultados.get("texto", [])])
    seccion("Archivos Documentos", resultados.get("archivos", []))
    seccion("Links",               resultados.get("links", []))
    seccion("Imágenes",            resultados.get("imagenes", []))
    seccion("Videos",              resultados.get("videos", []))
    seccion("Emails",              [{"email": e} for e in resultados.get("emails", [])])
    seccion("Custom",              resultados.get("custom", []))

    for i, tabla in enumerate(resultados.get("tablas", []), 1):
        lineas.append(f"# === TABLA HTML #{i} ===")
        for fila in tabla:
            lineas.append(",".join(f'"{str(c).replace(chr(34), chr(39))}"' for c in fila))
        lineas.append("")

    with open(ruta, "w", encoding="utf-8-sig", newline="\n") as f:
        f.write("\n".join(lineas))

    return ruta


def exportar_excel(resultados: dict, carpeta: str, nombre: str) -> str:
    """
    Exporta cada tipo de dato como una hoja separada en un archivo Excel.
    """
    ruta = _ruta(carpeta, nombre, "xlsx")

    with pd.ExcelWriter(ruta, engine="openpyxl") as writer:

        info = resultados.get("info_pagina", {})
        if info:
            df_info = pd.DataFrame(list(info.items()), columns=["Campo", "Valor"])
            df_info.to_excel(writer, sheet_name="Info_Página", index=False)

        if resultados.get("titulos"):
            pd.DataFrame(resultados["titulos"]).to_excel(writer, sheet_name="Títulos", index=False)

        if resultados.get("texto"):
            pd.DataFrame(resultados["texto"]).to_excel(writer, sheet_name="Texto", index=False)

        if resultados.get("archivos"):
            pd.DataFrame(resultados["archivos"]).to_excel(writer, sheet_name="Archivos", index=False)

        if resultados.get("links"):
            pd.DataFrame(resultados["links"]).to_excel(writer, sheet_name="Links", index=False)

        if resultados.get("imagenes"):
            pd.DataFrame(resultados["imagenes"]).to_excel(writer, sheet_name="Imágenes", index=False)

        if resultados.get("videos"):
            pd.DataFrame(resultados["videos"]).to_excel(writer, sheet_name="Videos", index=False)

        if resultados.get("archivos_descargados"):
            pd.DataFrame(resultados["archivos_descargados"], columns=["Archivo"]).to_excel(
                writer, sheet_name="Descargados", index=False
            )

        if resultados.get("emails"):
            pd.DataFrame(resultados["emails"], columns=["Email"]).to_excel(writer, sheet_name="Emails", index=False)

        if resultados.get("custom"):
            pd.DataFrame(resultados["custom"]).to_excel(writer, sheet_name="Selectores_Custom", index=False)

        if resultados.get("json_ld"):
            textos = [json.dumps(b, ensure_ascii=False, indent=2) for b in resultados["json_ld"]]
            pd.DataFrame({"json_ld": textos}).to_excel(writer, sheet_name="JSON_LD", index=False)

        for i, tabla in enumerate(resultados.get("tablas", []), 1):
            try:
                df_t = pd.DataFrame(tabla[1:], columns=tabla[0]) if len(tabla) > 1 else pd.DataFrame(tabla)
                sheet = f"Tabla_{i}"[:31]
                df_t.to_excel(writer, sheet_name=sheet, index=False)
            except Exception:
                pass

    return ruta


def exportar_json(resultados: dict, carpeta: str, nombre: str) -> str:
    """Exporta todos los resultados como un único JSON estructurado."""
    ruta = _ruta(carpeta, nombre, "json")
    datos_export = {k: v for k, v in resultados.items() if k != "html_raw"}
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos_export, f, ensure_ascii=False, indent=2, default=str)
    return ruta