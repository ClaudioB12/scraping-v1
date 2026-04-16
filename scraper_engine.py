import asyncio
import re
import time
import random
import os
import subprocess
import requests
from typing import Callable, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False
    print("[WARN] Playwright no instalado.")

try:
    import yt_dlp
    YTDLP_OK = True
except ImportError:
    YTDLP_OK = False
    print("[WARN] yt-dlp no instalado. Instálalo con: pip install yt-dlp")

STEALTH_SCRIPTS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} };
Object.defineProperty(navigator, 'languages', { get: () => ['es-PE', 'es', 'en-US', 'en'] });
Object.defineProperty(navigator, 'platform',  { get: () => 'Win32' });
"""

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


async def mover_raton_bezier(page: "Page", x_dest: float, y_dest: float, pasos: int = 15):
    try:
        x0, y0 = 100, 100
        ctrl_x = random.uniform(min(x0, x_dest), max(x0, x_dest))
        ctrl_y = random.uniform(min(y0, y_dest) - 100, max(y0, y_dest) + 100)
        for i in range(pasos + 1):
            t = i / pasos
            x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * ctrl_x + t ** 2 * x_dest
            y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * ctrl_y + t ** 2 * y_dest
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.01, 0.03))
    except Exception:
        pass


async def scroll_humano(page: "Page"):
    try:
        altura_total = await page.evaluate("() => document.body.scrollHeight")
        posicion = 0
        while posicion < altura_total:
            delta = random.randint(200, 600)
            posicion = min(posicion + delta, altura_total)
            await page.evaluate(f"window.scrollTo({{top: {posicion}, behavior: 'smooth'}})")
            await asyncio.sleep(random.uniform(0.5, 1.5))
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────
# UTILIDADES DE DESCARGA DE VIDEO
# ─────────────────────────────────────────────────────────────

def descargar_hls_ffmpeg(url_m3u8: str, carpeta_salida: str, nombre: str = None) -> Optional[str]:
    """Descarga un stream HLS (m3u8) o DASH (mpd) usando ffmpeg.
    Si ffmpeg no está disponible, cae automáticamente al método sin ffmpeg."""
    if not nombre:
        nombre = f"video_hls_{int(time.time())}.mp4"
    ruta = os.path.join(carpeta_salida, nombre)

    # Verificar si ffmpeg está disponible
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True, timeout=10)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        print("[WARN] ffmpeg no disponible. Usando método alternativo por segmentos...")
        return descargar_hls_sin_ffmpeg(url_m3u8, carpeta_salida, nombre)

    # Limpiar URL si tiene comas (formato de algunos CDNs)
    url_limpia = url_m3u8.split(',')[0] if ',' in url_m3u8 else url_m3u8

    comando = [
        "ffmpeg", "-y",
        "-i", url_limpia,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        ruta
    ]

    try:
        print(f"[INFO] Ejecutando ffmpeg para: {url_limpia[:60]}...")
        subprocess.run(comando, check=True, capture_output=True, timeout=300)
        return ruta
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"[WARN] ffmpeg falló: {e}. Intentando método por segmentos...")
        return descargar_hls_sin_ffmpeg(url_m3u8, carpeta_salida, nombre)


def descargar_hls_sin_ffmpeg(url_m3u8: str, carpeta_salida: str, nombre: str = None) -> Optional[str]:
    """Descarga un stream HLS segmento a segmento sin ffmpeg (fallback)."""
    if not nombre:
        nombre = f"video_hls_{int(time.time())}.mp4"
    ruta = os.path.join(carpeta_salida, nombre)

    try:
        url_limpia = url_m3u8.split(',')[0] if ',' in url_m3u8 else url_m3u8
        response = requests.get(url_limpia, timeout=30)
        response.raise_for_status()

        segmentos = []
        for linea in response.text.splitlines():
            linea = linea.strip()
            if linea and not linea.startswith('#'):
                if not linea.startswith('http'):
                    base_url = url_limpia.rsplit('/', 1)[0]
                    segmentos.append(f"{base_url}/{linea}")
                else:
                    segmentos.append(linea)

        if not segmentos:
            print("[WARN] No se encontraron segmentos en el manifiesto")
            return None

        print(f"[INFO] Descargando {len(segmentos)} segmentos HLS...")
        with open(ruta, 'wb') as archivo_salida:
            for i, seg_url in enumerate(segmentos):
                print(f"[INFO] Segmento {i+1}/{len(segmentos)}")
                seg_resp = requests.get(seg_url, timeout=30)
                seg_resp.raise_for_status()
                archivo_salida.write(seg_resp.content)

        return ruta
    except Exception as e:
        print(f"[WARN] Falló descarga HLS sin ffmpeg: {e}")
        return None


def descargar_con_ytdlp(url: str, carpeta_salida: str) -> Optional[str]:
    """Descarga video de YouTube, Vimeo u otras plataformas usando yt-dlp."""
    if not YTDLP_OK:
        print("[WARN] yt-dlp no disponible.")
        return None
    ydl_opts = {
        "outtmpl": os.path.join(carpeta_salida, "%(title)s.%(ext)s"),
        "format": "best[height<=720]/best",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "extract_flat": False,
        "socket_timeout": 60,
        "extractor_args": {
            "youtube": {"player_client": ["android", "web"]}
        },
        "extractor_retries": 3,
        "fragment_retries": 10,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"[WARN] yt-dlp falló para {url}: {e}")
        return None


def descargar_youtube_especifico(url: str, carpeta_salida: str) -> Optional[str]:
    """Función especializada para descargar videos de YouTube (watch, shorts, youtu.be)."""
    if not YTDLP_OK:
        print("[WARN] yt-dlp no disponible.")
        return None

    video_id = None
    if "youtube.com/watch?v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com/shorts/" in url:
        video_id = url.split("shorts/")[1].split("?")[0]

    direct_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else url

    ydl_opts = {
        "outtmpl": os.path.join(carpeta_salida, "%(title)s.%(ext)s"),
        "format": "best[height<=720]/best",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "extract_flat": False,
        "socket_timeout": 60,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "skip": ["dash", "hls"],
            }
        },
        "extractor_retries": 5,
        "fragment_retries": 15,
        "cookiefile": "youtube_cookies.txt" if os.path.exists("youtube_cookies.txt") else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(direct_url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"[WARN] Método específico de YouTube falló ({e}), intentando fallback genérico...")
        return descargar_con_ytdlp(url, carpeta_salida)


PLATAFORMAS_YTDLP = [
    "youtube.com", "youtu.be", "vimeo.com",
    "dailymotion.com", "twitch.tv", "tiktok.com"
]


def es_plataforma_conocida(url: str) -> bool:
    return any(p in url for p in PLATAFORMAS_YTDLP)


# ─────────────────────────────────────────────────────────────
# MOTOR PRINCIPAL
# ─────────────────────────────────────────────────────────────

class ScraperEngine:
    def __init__(self, config: dict, log_callback: Optional[Callable] = None):
        self.config = config
        self.log = log_callback or (lambda msg, nivel="info": print(f"[{nivel.upper()}] {msg}"))
        self.ua = random.choice(USER_AGENTS)
        self.carpeta_descargas = config.get("carpeta_salida", "descargas_manuales")
        os.makedirs(self.carpeta_descargas, exist_ok=True)

    def scrape(self, url: str, opciones: dict, stop_flag=None, progress_callback=None) -> dict:
        return asyncio.run(self._scrape_async(url, opciones, stop_flag, progress_callback))

    async def _scrape_async(self, url: str, opciones: dict, stop_flag=None, progress_callback=None) -> dict:
        resultados = {}
        if self.config.get("modo") == "manual":
            self.config["headless"] = False

        async with async_playwright() as pw:
            motor = getattr(pw, self.config.get("navegador", "chromium"))
            browser: Browser = await motor.launch(
                headless=self.config["headless"],
                channel="chrome" if self.config["headless"] else None,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            context: BrowserContext = await browser.new_context(
                user_agent=self.ua,
                viewport={"width": 1920, "height": 1080},
                accept_downloads=True,
            )
            if self.config.get("stealth"):
                await context.add_init_script(STEALTH_SCRIPTS)

            page: Page = await context.new_page()

            try:
                if self.config.get("modo") == "manual":
                    await self._modo_human_in_the_loop(page, url)
                    resultados["mensaje"] = (
                        f"Extraccion manual finalizada. "
                        f"Archivos guardados en: {os.path.abspath(self.carpeta_descargas)}"
                    )
                else:
                    resultados = await self._modo_automatico(
                        page, url, opciones, stop_flag, progress_callback
                    )
            finally:
                await browser.close()

        return resultados

    # =========================================================
    # MODO MANUAL: Detector Universal de Nodos
    # =========================================================
    async def _modo_human_in_the_loop(self, page, url: str):
        self.log("Iniciando modo de supervision asistida. Navegador en espera de interaccion del usuario.", "info")

        async def descargar_elemento(datos):
            url_recurso = datos.get("url")
            if not url_recurso:
                return
            self.log(f"Interaccion detectada. Iniciando descarga desde: {url_recurso[:60]}", "info")
            try:
                if es_plataforma_conocida(url_recurso):
                    self.log("Plataforma de video reconocida. Delegando descarga a yt-dlp.", "info")
                    if "youtube.com" in url_recurso or "youtu.be" in url_recurso:
                        ruta = descargar_youtube_especifico(url_recurso, self.carpeta_descargas)
                    else:
                        ruta = descargar_con_ytdlp(url_recurso, self.carpeta_descargas)
                    if ruta:
                        self.log(f"Recurso almacenado correctamente via yt-dlp: {os.path.basename(ruta)}", "ok")
                        return

                cookies = await page.context.cookies()
                session = requests.Session()
                for cookie in cookies:
                    session.cookies.set(cookie["name"], cookie["value"])
                session.headers.update({"User-Agent": self.ua, "Referer": page.url})

                resp = session.get(url_recurso, timeout=30, stream=True)
                if resp.status_code == 200:
                    nombre_archivo = os.path.basename(urlparse(url_recurso).path)
                    if not nombre_archivo:
                        nombre_archivo = f"descarga_{int(time.time())}.dat"
                    ruta = os.path.join(self.carpeta_descargas, nombre_archivo)
                    with open(ruta, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    self.log(f"Recurso almacenado correctamente: {nombre_archivo}", "ok")
            except Exception as e:
                self.log(f"Error durante la descarga del recurso: {e}", "err")

        await page.context.expose_function("enviarAPython", descargar_elemento)

        script_inyeccion = """
            const isClickable = (el) => {
                const tag = el.tagName.toUpperCase();
                if (['A', 'BUTTON', 'IMG', 'VIDEO', 'AUDIO'].includes(tag)) return true;
                if (el.getAttribute('role') === 'button' || el.hasAttribute('onclick')) return true;
                if (window.getComputedStyle(el).cursor === 'pointer') return true;
                return false;
            };
            document.addEventListener('mouseover', (e) => {
                if(isClickable(e.target)) {
                    e.target.dataset.oldOutline = e.target.style.outline;
                    e.target.style.outline = '3px dashed #10b981';
                    e.target.style.boxShadow = '0 0 10px #10b981';
                    e.target.style.cursor = 'crosshair';
                }
            });
            document.addEventListener('mouseout', (e) => {
                if(isClickable(e.target)) {
                    e.target.style.outline = e.target.dataset.oldOutline || '';
                    e.target.style.boxShadow = '';
                }
            });
            document.addEventListener('click', (e) => {
                if (isClickable(e.target)) {
                    let url = '';
                    if (e.target.tagName === 'A') {
                        url = e.target.href;
                    } else if (['IMG', 'VIDEO', 'AUDIO', 'SOURCE'].includes(e.target.tagName)) {
                        url = e.target.src || e.target.currentSrc;
                    } else {
                        url = e.target.getAttribute('data-url') || e.target.getAttribute('data-href');
                        if (!url) {
                            let bg = window.getComputedStyle(e.target).backgroundImage;
                            if (bg && bg !== 'none') {
                                url = bg.replace(/^url\\(["']?/, '').replace(/["']?\\)$/, '');
                            }
                        }
                    }
                    if (url && window.enviarAPython) {
                        e.preventDefault();
                        e.stopPropagation();
                        window.enviarAPython({ url: url, tipo: e.target.tagName });
                        e.target.style.outline = '3px solid #f59e0b';
                        setTimeout(() => e.target.style.outline = '', 500);
                    }
                }
            }, { capture: true });
        """
        await page.add_init_script(script_inyeccion)
        await page.goto(url, wait_until="domcontentloaded")
        try:
            await page.wait_for_event("close", timeout=0)
        except Exception:
            pass

    # =========================================================
    # MODO AUTOMÁTICO: ARAÑA WEB + CAZADOR DE VIDEO AVANZADO
    # =========================================================
    async def _modo_automatico(self, page, url_inicial: str, opciones: dict,
                               stop_flag=None, progress_callback=None) -> dict:
        self.log("Iniciando motor de rastreo automatico. Explorando subpaginas y recursos del sitio.", "info")

        resultados = {
            "archivos_descargados": [], "tablas": [], "links": [],
            "titulos": [], "texto": [], "imagenes": [], "archivos": [],
            "videos": [],
        }

        descargas_pendientes = []

        # ── 1. INTERCEPTOR NATIVO DE DESCARGAS ──
        async def on_download(download):
            nombre = download.suggested_filename
            ruta = os.path.join(self.carpeta_descargas, nombre)
            self.log(f"Descarga interceptada por el navegador: {nombre}", "info")
            tarea = asyncio.create_task(download.save_as(ruta))
            descargas_pendientes.append((tarea, nombre))

        page.on("download", on_download)

        # ── 2. INTERCEPTOR DE RED: CAPTURA URLs DE VIDEO EN TRÁFICO ──
        urls_red_capturadas: list = []

        async def on_request(request):
            url = request.url
            if any(ext in url for ext in [".m3u8", ".mpd", ".mp4", ".webm", ".ts"]):
                if url.endswith(".ts") and ".m3u8" not in url:
                    return
                tipo = (
                    "hls_stream" if ".m3u8" in url
                    else "dash_stream" if ".mpd" in url
                    else os.path.splitext(urlparse(url).path.lower())[1]
                )
                entry = {"src": url, "tipo": tipo, "titulo": "Video detectado en red", "poster": ""}
                if url not in {v["src"] for v in urls_red_capturadas}:
                    self.log(f"URL de video detectada en trafico de red: {url[:70]}", "ok")
                    urls_red_capturadas.append(entry)

        page.on("request", on_request)

        # ── 3. SISTEMA DE CRAWLER (BFS) ──
        visitados = set()
        cola = [url_inicial]
        dominio_base = urlparse(url_inicial).netloc
        paginas_procesadas = 0
        max_paginas = self.config.get("max_paginas", 10)

        kw_descarga = [
            "descargar", "download", "ir al recurso", "csv", "excel",
            "xlsx", "zip", "datos", "mp4",
        ]
        exts_descarga = [
            ".csv", ".pdf", ".xlsx", ".zip", ".xls",
            ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"
        ]

        while cola and paginas_procesadas < max_paginas:
            if stop_flag and stop_flag.is_set():
                self.log("Proceso detenido por solicitud del usuario.", "warn")
                break

            url_actual = cola.pop(0)
            if url_actual in visitados:
                continue
            visitados.add(url_actual)
            self.log(f"Analizando pagina [{paginas_procesadas+1}/{max_paginas}]: {url_actual}", "info")

            try:
                await page.goto(url_actual, wait_until="domcontentloaded", timeout=40000)
                paginas_procesadas += 1
                await asyncio.sleep(2)

                if self.config.get("scroll_pagina"):
                    await scroll_humano(page)

                # ── A. DISPARAR REPRODUCCIÓN PARA FORZAR CARGA DE STREAMS ──
                if opciones.get("videos"):
                    await page.evaluate("""
                        () => {
                            document.querySelectorAll('video').forEach(v => {
                                v.muted = true;
                                v.play().catch(() => {});
                            });
                        }
                    """)
                    await asyncio.sleep(3)

                # ── B. CAZAR BOTONES DE DESCARGA ──
                elementos = await page.locator("a, button, [role='button']").all()
                for el in elementos:
                    try:
                        if await el.is_visible():
                            texto = (await el.inner_text()).lower().strip()
                            href = await el.get_attribute("href")
                            es_descarga = (
                                any(kw in texto for kw in kw_descarga)
                                or (href and any(href.lower().endswith(ext) for ext in exts_descarga))
                            )
                            if es_descarga:
                                self.log(f"Elemento de descarga identificado: '{texto[:20]}'. Activando enlace.", "warn")
                                url_antes = page.url
                                await el.click(timeout=5000)
                                await asyncio.sleep(2.0)
                                if page.url != url_antes:
                                    self.log("El enlace produjo navegacion. Retrocediendo a la pagina anterior.", "info")
                                    await page.go_back(wait_until="domcontentloaded")
                    except Exception:
                        pass

                # ── C. DESCUBRIR NUEVAS PÁGINAS ──
                if paginas_procesadas < max_paginas:
                    todos_los_links = await page.locator("a[href]").all()
                    for a in todos_los_links:
                        try:
                            href = await a.get_attribute("href")
                            texto_link = (await a.inner_text()).strip()
                            if href and not href.startswith(("javascript", "#", "mailto:")):
                                link_abs = urljoin(url_actual, href).split("#")[0]
                                if (
                                    urlparse(link_abs).netloc == dominio_base
                                    and link_abs not in visitados
                                    and link_abs not in cola
                                ):
                                    if (re.search(r"20\d{2}", texto_link)
                                            or "recurso" in texto_link.lower()
                                            or "indicador" in texto_link.lower()):
                                        self.log(f"Enlace prioritario encolado: '{texto_link}'", "ok")
                                        cola.insert(0, link_abs)
                                    else:
                                        cola.append(link_abs)
                        except Exception:
                            pass

                # ── D. EXTRACCIÓN DE CONTENIDO ESTÁNDAR ──
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")

                if opciones.get("titulos"):  resultados["titulos"].extend(self._extraer_titulos(soup))
                if opciones.get("texto"):    resultados["texto"].extend(self._extraer_texto(soup))
                if opciones.get("links"):    resultados["links"].extend(self._extraer_links(soup, url_actual))
                if opciones.get("archivos"): resultados["archivos"].extend(self._extraer_archivos(soup, url_actual))
                if opciones.get("imagenes"): resultados["imagenes"].extend(self._extraer_imagenes(soup, url_actual))
                if opciones.get("tablas"):   resultados["tablas"].extend(self._extraer_tablas(soup))
                if opciones.get("videos"):
                    resultados["videos"].extend(self._extraer_videos(soup, url_actual))
                    videos_dom = await self._extraer_videos_dom(page, url_actual)
                    resultados["videos"].extend(videos_dom)

                if progress_callback:
                    progress_callback(paginas_procesadas, max_paginas, url_actual, resultados)

            except Exception as e:
                self.log(f"Error durante el analisis de '{url_actual}': {e}", "err")

        # ── 4. AGREGAR URLs CAPTURADAS EN RED ──
        if opciones.get("videos") and urls_red_capturadas:
            self.log(f"Incorporando {len(urls_red_capturadas)} URL(s) de video detectadas en el trafico de red.", "ok")
            resultados["videos"].extend(urls_red_capturadas)

        # ── 5. DEDUPLICAR VIDEOS ──
        resultados["videos"] = self._deduplicar_videos(resultados["videos"])

        # ── 6. DESCARGAR STREAMS HLS/DASH + PLATAFORMAS CON yt-dlp ──
        if opciones.get("videos"):
            for video in resultados["videos"]:
                src = video.get("src", "")
                tipo = video.get("tipo", "")

                if tipo == "hls_stream" or src.endswith(".m3u8"):
                    self.log(f"Iniciando descarga de stream HLS: {src[:60]}", "info")
                    nombre = f"video_hls_{int(time.time())}.mp4"
                    ruta = descargar_hls_ffmpeg(src, self.carpeta_descargas, nombre)
                    if ruta:
                        self.log(f"Stream HLS almacenado correctamente: {nombre}", "ok")
                        resultados["archivos_descargados"].append(nombre)
                        video["descargado"] = nombre

                elif tipo == "dash_stream" or src.endswith(".mpd"):
                    self.log(f"Iniciando descarga de stream DASH: {src[:60]}", "info")
                    nombre = f"video_dash_{int(time.time())}.mp4"
                    ruta = descargar_hls_ffmpeg(src, self.carpeta_descargas, nombre)
                    if ruta:
                        self.log(f"Stream DASH almacenado correctamente: {nombre}", "ok")
                        resultados["archivos_descargados"].append(nombre)
                        video["descargado"] = nombre

                elif tipo in ("iframe_embed", "youtube_link") and es_plataforma_conocida(src):
                    self.log(f"Iniciando descarga desde plataforma de video via yt-dlp: {src[:60]}", "info")
                    if "youtube.com" in src or "youtu.be" in src:
                        ruta = descargar_youtube_especifico(src, self.carpeta_descargas)
                    else:
                        ruta = descargar_con_ytdlp(src, self.carpeta_descargas)
                    if ruta:
                        nombre = os.path.basename(ruta)
                        self.log(f"Recurso de plataforma almacenado correctamente via yt-dlp: {nombre}", "ok")
                        resultados["archivos_descargados"].append(nombre)
                        video["descargado"] = nombre

        # ── 7. ESPERAR DESCARGAS NATIVAS PENDIENTES ──
        if descargas_pendientes:
            self.log(f"Aguardando la finalizacion de {len(descargas_pendientes)} descarga(s) en segundo plano.", "warn")
            for tarea, nombre in descargas_pendientes:
                try:
                    await tarea
                    self.log(f"Descarga completada satisfactoriamente: {nombre}", "ok")
                    if nombre not in resultados["archivos_descargados"]:
                        resultados["archivos_descargados"].append(nombre)
                except Exception:
                    pass

        self.log(f"Rastreo concluido. Total de paginas procesadas: {paginas_procesadas}.", "info")
        return resultados

    # =========================================================
    # EXTRACCIÓN DINÁMICA DE VIDEO VÍA DOM EN VIVO
    # =========================================================
    async def _extraer_videos_dom(self, page, base: str) -> list:
        try:
            video_urls = await page.evaluate("""
                () => {
                    const resultados = [];
                    document.querySelectorAll('video').forEach(v => {
                        if (v.src) resultados.push({ src: v.src, tipo: 'video_dom', titulo: v.title || '', poster: v.poster || '' });
                        if (v.currentSrc && v.currentSrc !== v.src) resultados.push({ src: v.currentSrc, tipo: 'video_dom_current', titulo: '', poster: '' });
                        v.querySelectorAll('source').forEach(s => {
                            if (s.src) resultados.push({ src: s.src, tipo: s.type || 'source_dom', titulo: '', poster: '' });
                        });
                    });
                    document.querySelectorAll('iframe').forEach(f => {
                        const src = f.src || f.getAttribute('data-src') || '';
                        if (src && (src.includes('youtube') || src.includes('vimeo') || src.includes('dailymotion') || src.includes('twitch'))) {
                            resultados.push({ src: src, tipo: 'iframe_embed', titulo: f.title || '', poster: '' });
                        }
                    });
                    const extsVideo = ['.mp4','.webm','.mkv','.m3u8','.mpd','.flv'];
                    document.querySelectorAll('[data-src],[data-video],[data-url],[data-file]').forEach(el => {
                        ['data-src','data-video','data-url','data-file'].forEach(attr => {
                            const val = el.getAttribute(attr);
                            if (val && extsVideo.some(e => val.includes(e))) {
                                resultados.push({ src: val, tipo: 'data_attr', titulo: el.title || el.alt || '', poster: '' });
                            }
                        });
                    });
                    document.querySelectorAll('object, embed').forEach(el => {
                        const src = el.getAttribute('data') || el.getAttribute('src') || '';
                        if (src) resultados.push({ src: src, tipo: 'object_embed', titulo: '', poster: '' });
                    });
                    return resultados;
                }
            """)
            return video_urls if video_urls else []
        except Exception as e:
            self.log(f"Error durante la extraccion de video en DOM: {e}", "warn")
            return []

    # =========================================================
    # MÉTODOS DE PARSEO ESTÁTICO (BeautifulSoup)
    # =========================================================
    def _extraer_titulos(self, soup):
        return [
            {"nivel": t.name, "texto": t.get_text(strip=True)}
            for t in soup.find_all(["h1", "h2", "h3"])
            if t.get_text(strip=True)
        ]

    def _extraer_texto(self, soup):
        return [
            {"parrafo": p.get_text(strip=True)}
            for p in soup.find_all("p")
            if len(p.get_text(strip=True)) > 20
        ]

    def _extraer_links(self, soup, base):
        return [
            {"href": urljoin(base, a["href"]), "texto": a.get_text(strip=True)[:50]}
            for a in soup.find_all("a", href=True)
        ]

    def _extraer_imagenes(self, soup, base):
        return [
            {"src": urljoin(base, img.get("src", "")), "alt": img.get("alt", "")}
            for img in soup.find_all("img")
            if img.get("src")
        ]

    def _extraer_tablas(self, soup):
        return [
            [
                [c.get_text(strip=True) for c in fila.find_all(["td", "th"])]
                for fila in tabla.find_all("tr")
            ]
            for tabla in soup.find_all("table")
            if len(tabla.find_all("tr")) > 1
        ]

    def _extraer_archivos(self, soup, base):
        exts = {".pdf", ".docx", ".xlsx", ".zip", ".csv"}
        archivos = []
        for a in soup.find_all("a", href=True):
            href = urljoin(base, a["href"])
            ext = os.path.splitext(urlparse(href).path.lower())[1]
            if ext in exts:
                archivos.append({
                    "nombre": os.path.basename(href),
                    "tipo": ext,
                    "url": href,
                    "texto_enlace": a.get_text(strip=True)[:50],
                })
        return archivos

    def _extraer_videos(self, soup, base):
        videos = []
        exts_video = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".m4v", ".ogv"}

        for video in soup.find_all("video"):
            src = video.get("src")
            if src:
                videos.append({
                    "src": urljoin(base, src),
                    "tipo": "video_tag",
                    "titulo": video.get("title", ""),
                    "poster": urljoin(base, video.get("poster", "")) if video.get("poster") else "",
                })
            for source in video.find_all("source"):
                src = source.get("src")
                if src:
                    videos.append({
                        "src": urljoin(base, src),
                        "tipo": source.get("type", "source_tag"),
                        "titulo": "",
                        "poster": "",
                    })

        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "") or iframe.get("data-src", "")
            if src and any(h in src for h in ["youtube.com", "youtu.be", "vimeo.com", "dailymotion.com", "twitch.tv"]):
                videos.append({
                    "src": src,
                    "tipo": "iframe_embed",
                    "titulo": iframe.get("title", ""),
                    "poster": "",
                })

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if any(yt in href for yt in ["youtube.com/watch", "youtu.be/", "youtube.com/shorts/"]):
                url_yt = href if href.startswith("http") else f"https://www.youtube.com{href}"
                videos.append({
                    "src": url_yt,
                    "tipo": "youtube_link",
                    "titulo": a.get_text(strip=True)[:80],
                    "poster": "",
                })

        for a in soup.find_all("a", href=True):
            href = urljoin(base, a["href"])
            ext = os.path.splitext(urlparse(href).path.lower())[1]
            if ext in exts_video:
                videos.append({
                    "src": href,
                    "tipo": ext,
                    "titulo": a.get_text(strip=True)[:80],
                    "poster": "",
                })

        for tag in soup.find_all(attrs={"data-src": True}):
            data_src = tag.get("data-src", "")
            ext = os.path.splitext(urlparse(data_src).path.lower())[1]
            if ext in exts_video or ".m3u8" in data_src or ".mpd" in data_src:
                tipo = "hls_stream" if ".m3u8" in data_src else "dash_stream" if ".mpd" in data_src else f"lazy_{ext}"
                videos.append({
                    "src": urljoin(base, data_src),
                    "tipo": tipo,
                    "titulo": tag.get("title", tag.get_text(strip=True)[:50]),
                    "poster": "",
                })

        for script in soup.find_all("script"):
            if not script.string:
                continue
            texto_js = script.string
            for m in re.findall(r'["\']([^"\']*\.m3u8[^"\']*)["\']', texto_js):
                videos.append({"src": urljoin(base, m), "tipo": "hls_stream", "titulo": "HLS en JS", "poster": ""})
            for m in re.findall(r'["\']([^"\']*\.mpd[^"\']*)["\']', texto_js):
                videos.append({"src": urljoin(base, m), "tipo": "dash_stream", "titulo": "DASH en JS", "poster": ""})
            for m in re.findall(r'["\']([^"\']*\.mp4[^"\']*)["\']', texto_js):
                videos.append({"src": urljoin(base, m), "tipo": ".mp4", "titulo": "MP4 en JS", "poster": ""})

        return videos

    def _deduplicar_videos(self, videos: list) -> list:
        seen = set()
        unicos = []
        for v in videos:
            src = v.get("src", "")
            if src and src not in seen:
                seen.add(src)
                unicos.append(v)
        return unicos