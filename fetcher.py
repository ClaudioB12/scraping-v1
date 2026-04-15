import sqlite3
import time
import feedparser
import requests
from bs4 import BeautifulSoup

DB_PATH = "noticias.db"

# ➜ Lista de FUENTES (solo nombre + URL RSS)
FUENTES = [
    # Medios principales (Perú)
    ("RPP", "https://rpp.pe/rss"),
    ("Perú21", "https://peru21.pe/feed/"),
    ("La República", "https://larepublica.pe/rss"),
    ("El Comercio", "https://elcomercio.pe/feed/"),
    ("Gestión", "https://gestion.pe/feed/"),
    ("Andina", "https://andina.pe/agencia/seccion-rss.aspx?seccion=9&canal=3"),
    ("América Noticias", "https://www.americatv.com.pe/noticias/rss"),
    ("Depor", "https://depor.com/feed/"),

    # Regional
    ("Sin Fronteras Puno", "https://www.diariosinfronteras.pe/feed/"),

    # Internacionales en español
    ("BBC Mundo", "https://www.bbc.com/mundo/index.xml"),
    ("DW Español", "https://rss.dw.com/xml/rss-es-all"),
    ("CNN Español", "https://cnnespanol.cnn.com/feed/"),

    # Tecnología
    ("Xataka", "https://www.xataka.com/index.xml"),
    ("Genbeta", "https://www.genbeta.com/index.xml"),

    # Deportes internacionales
    ("ESPN", "https://www.espn.com/espn/rss/news"),
    ("Marca", "https://e00-marca.uecdn.es/rss/portada.xml"),
]

USER_AGENT = {"User-Agent": "Mozilla/5.0"}


def init_db():
    """Crea la tabla news si no existe."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        title TEXT,
        summary TEXT,
        link TEXT UNIQUE,
        published_ts INTEGER,
        image TEXT
    )
    """)
    con.commit()
    con.close()


def _try_extract_image_from_page(url: str) -> str | None:
    """Si el RSS no trae imagen, intenta sacar og:image de la página."""
    try:
        r = requests.get(url, headers=USER_AGENT, timeout=8)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]
    except Exception:
        pass
    return None


def _get_entry_image(entry) -> str | None:
    """Intenta obtener imagen directamente del RSS (media:content, enclosure, etc.)."""
    # media:content
    if "media_content" in entry and entry.media_content:
        mc = entry.media_content[0]
        if isinstance(mc, dict) and mc.get("url"):
            return mc["url"]

    # enclosure con tipo image/*
    if "links" in entry:
        for ln in entry.links:
            if ln.get("rel") == "enclosure" and ln.get("type", "").startswith("image/"):
                return ln.get("href")

    # algunos feeds usan entry.image
    if "image" in entry and isinstance(entry.image, dict) and entry.image.get("href"):
        return entry.image["href"]

    return None


def fetch_all(limit_por_feed: int | None = None) -> int:
    """
    Descarga noticias de todas las fuentes y guarda sin duplicar.
    Devuelve cuántas noticias NUEVAS se insertaron.
    """
    init_db()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    nuevos = 0

    for fuente, url in FUENTES:
        print(f"[INFO] Descargando RSS de {fuente} -> {url}")
        feed = feedparser.parse(url)
        entries = feed.entries

        if limit_por_feed:
            entries = entries[:limit_por_feed]

        for e in entries:
            title = e.get("title", "Sin título").strip()
            summary = (e.get("summary") or e.get("description") or "").strip()
            link = e.get("link", "#").strip()

            # Timestamp de publicación
            if "published_parsed" in e and e.published_parsed:
                published_ts = int(time.mktime(e.published_parsed))
            else:
                published_ts = int(time.time())

            # Imagen (primero intentamos del RSS, luego de la página)
            image = _get_entry_image(e) or _try_extract_image_from_page(link) or ""

            try:
                cur.execute("""
                    INSERT OR IGNORE INTO news (source, title, summary, link, published_ts, image)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (fuente, title, summary, link, published_ts, image))
                if cur.rowcount == 1:
                    nuevos += 1
            except Exception as ex:
                # Si hay algún error raro de encoding, etc., solo lo saltamos
                print(f"[WARN] Error insertando noticia de {fuente}: {ex}")

    con.commit()
    con.close()
    print(f"[INFO] Noticias nuevas insertadas: {nuevos}")
    return nuevos


if __name__ == "__main__":
    # Si ejecutas: python fetcher.py
    # hará una carga manual y mostrará cuántas noticias nuevas hay.
    n = fetch_all()
    print("Total nuevas:", n)
