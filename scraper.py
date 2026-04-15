import requests
from bs4 import BeautifulSoup
from tabulate import tabulate

url = "https://rpp.pe/"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)

if resp.status_code == 200:
    soup = BeautifulSoup(resp.text, "html.parser")
    articulos = soup.find_all("article", limit=10)

    datos = []
    for art in articulos:
        titulo = art.find("h2")
        titulo_texto = titulo.get_text(strip=True) if titulo else "Sin título"

        categoria = art.find("a", class_="section")
        categoria_texto = categoria.get_text(strip=True) if categoria else "Sin categoría"

        fecha = art.find("time")
        fecha_texto = fecha.get_text(strip=True) if fecha else "Sin fecha"

        datos.append([titulo_texto, categoria_texto, fecha_texto])

    # Mostrar tabla
    print(tabulate(datos, headers=["Título", "Categoría", "Fecha"], tablefmt="grid"))
else:
    print("Error al acceder a RPP:", resp.status_code)
