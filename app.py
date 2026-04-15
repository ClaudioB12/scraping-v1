from flask import Flask, request, redirect, url_for, render_template_string, session, Response
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime
from fetcher import fetch_all

app = Flask(__name__)
app.secret_key = "clave_secreta_123"
app.permanent_session_lifetime = timedelta(days=7)

DB_PATH = "noticias.db"


# ---------------------------
#  Asegurar tabla users y plan
# ---------------------------
def ensure_users_table_and_plan():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # Crear tabla si no existe (incluye columna plan)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            plan TEXT DEFAULT 'free'
        )
    """)
    # Revisar si existe la columna plan
    cur.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in cur.fetchall()]
    if "plan" not in cols:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free'")
            con.commit()
        except Exception:
            pass
    con.close()


ensure_users_table_and_plan()


# ---------------------------
#   Decorador login requerido
# ---------------------------
def login_required(fn):
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


# ---------------------------
#           LOGIN
# ---------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        # ahora leemos también el plan
        cur.execute("SELECT id, password_hash, plan FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        con.close()

        if row and check_password_hash(row[1], password):
            session["user_id"] = row[0]
            session["username"] = username
            session["plan"] = row[2] if row[2] else "free"
            return redirect(url_for("home"))
        else:
            error = "Usuario o contraseña incorrectos."

    html = """
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Login - Portal de Noticias</title>
    <style>
      *{margin:0;padding:0;box-sizing:border-box;}
      body{font-family:'Segoe UI',Tahoma,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
           display:flex;justify-content:center;align-items:center;min-height:100vh;}
      .card{background:white;padding:40px;border-radius:20px;min-width:380px;
            box-shadow:0 20px 60px rgba(0,0,0,.3);}
      h1{text-align:center;margin-bottom:10px;color:#1f2937;font-size:28px;}
      .subtitle{text-align:center;color:#6b7280;margin-bottom:30px;font-size:14px;}
      input{width:100%;padding:12px 15px;margin-bottom:15px;border-radius:10px;border:2px solid #e5e7eb;
            font-size:15px;transition:all 0.3s;}
      input:focus{outline:none;border-color:#667eea;}
      button{width:100%;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
             color:white;border:none;border-radius:10px;cursor:pointer;font-size:16px;font-weight:600;
             transition:transform 0.2s;}
      button:hover{transform:translateY(-2px);}
      .error{text-align:center;color:#ef4444;margin-bottom:15px;background:#fee2e2;padding:10px;
             border-radius:8px;font-size:14px;}
      a{text-decoration:none;color:#667eea;font-weight:600;}
      .link{text-align:center;margin-top:20px;font-size:14px;color:#6b7280;}
    </style></head>
    <body>
      <div class="card">
        <h1>🔐 Iniciar sesión</h1>
        <div class="subtitle">Portal de Noticias</div>
        {% if error %}
          <div class="error">{{ error }}</div>
        {% endif %}
        <form method="post">
          <input name="username" placeholder="👤 Usuario" required>
          <input name="password" type="password" placeholder="🔒 Contraseña" required>
          <button>Entrar</button>
        </form>
        <div class="link">
          ¿No tienes cuenta? <a href="{{ url_for('register') }}">Crear cuenta</a>
        </div>
      </div>
    </body></html>
    """
    return render_template_string(html, error=error)


# ---------------------------
#          REGISTRO
# ---------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        password2 = request.form.get("password2", "").strip()

        # por defecto SIEMPRE creamos como plan free
        plan = "free"

        if not username or not password or not password2:
            error = "Completa todos los campos."
        elif password != password2:
            error = "Las contraseñas no coinciden."
        else:
            password_hash = generate_password_hash(password)
            con = sqlite3.connect(DB_PATH)
            cur = con.cursor()
            try:
                cur.execute(
                    "INSERT INTO users (username, password_hash, plan) VALUES (?, ?, ?)",
                    (username, password_hash, plan)
                )
                con.commit()
                user_id = cur.lastrowid
                con.close()
                session["user_id"] = user_id
                session["username"] = username
                session["plan"] = plan
                return redirect(url_for("home"))
            except:
                error = "Ese usuario ya existe."

    html = """
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Registro - Portal de Noticias</title>
    <style>
      *{margin:0;padding:0;box-sizing:border-box;}
      body{font-family:'Segoe UI',Tahoma,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
           display:flex;justify-content:center;align-items:center;min-height:100vh;}
      .card{background:white;padding:40px;border-radius:20px;min-width:380px;
            box-shadow:0 20px 60px rgba(0,0,0,.3);}
      h1{text-align:center;margin-bottom:10px;color:#1f2937;font-size:28px;}
      .subtitle{text-align:center;color:#6b7280;margin-bottom:30px;font-size:14px;}
      label{font-size:14px;color:#374151;margin-bottom:4px;display:block;}
      input{width:100%;padding:12px 15px;margin-bottom:15px;border-radius:10px;border:2px solid #e5e7eb;
            font-size:15px;transition:all 0.3s;}
      input:focus{outline:none;border-color:#667eea;}
      button{width:100%;padding:12px;background:linear-gradient(135deg,#10b981 0%,#059669 100%);
             color:white;border:none;border-radius:10px;cursor:pointer;font-size:16px;font-weight:600;
             transition:transform 0.2s;}
      button:hover{transform:translateY(-2px);}
      .info-plan{font-size:13px;color:#6b7280;margin-bottom:15px;}
      .error{text-align:center;color:#ef4444;margin-bottom:15px;background:#fee2e2;padding:10px;
             border-radius:8px;font-size:14px;}
      a{text-decoration:none;color:#667eea;font-weight:600;}
      .link{text-align:center;margin-top:20px;font-size:14px;color:#6b7280;}
    </style></head>
    <body>
      <div class="card">
        <h1>🆕 Crear cuenta</h1>
        <div class="subtitle">Portal de Noticias</div>
        {% if error %}
          <div class="error">{{ error }}</div>
        {% endif %}
        <form method="post">
          <label>Usuario</label>
          <input name="username" placeholder="👤 Usuario" required>

          <label>Contraseña</label>
          <input name="password" type="password" placeholder="🔒 Contraseña" required>

          <label>Repetir contraseña</label>
          <input name="password2" type="password" placeholder="🔒 Repetir contraseña" required>

          <div class="info-plan">
            📌 Tu cuenta se creará con <b>Plan Free</b> (gratuito). Luego podrás subir a <b>Plan Pro</b> desde el portal.
          </div>

          <button>Registrarme</button>
        </form>
        <div class="link">
          ¿Ya tienes cuenta? <a href="{{ url_for('login') }}">Inicia sesión</a>
        </div>
      </div>
    </body></html>
    """
    return render_template_string(html, error=error)


# ---------------------------
#          LOGOUT
# ---------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------
#  Tiempo relativo amigable
# ---------------------------
def tiempo_relativo(timestamp_value):
    """
    Convierte un timestamp (segundos desde epoch) o string ISO a un texto tipo:
    'Hace 2 horas', 'Hace 3 días', etc.
    """
    try:
        # Si viene como número (int/float)
        if isinstance(timestamp_value, (int, float)):
            dt = datetime.fromtimestamp(timestamp_value)
        else:
            # Asumimos string
            ts_str = str(timestamp_value)
            # Si parece epoch en texto
            if ts_str.isdigit():
                dt = datetime.fromtimestamp(int(ts_str))
            else:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt
        segundos = diff.total_seconds()

        if segundos < 60:
            return "Hace unos segundos"
        elif segundos < 3600:
            mins = int(segundos / 60)
            return f"Hace {mins} minuto{'s' if mins != 1 else ''}"
        elif segundos < 86400:
            horas = int(segundos / 3600)
            return f"Hace {horas} hora{'s' if horas != 1 else ''}"
        elif segundos < 604800:
            dias = int(segundos / 86400)
            return f"Hace {dias} día{'s' if dias != 1 else ''}"
        else:
            return dt.strftime("%d/%m/%Y")
    except Exception:
        return "Fecha desconocida"


# ---------------------------
#      Consultas a la BD
# ---------------------------
def obtener_noticias(limit, search_query=None, source_filter=None):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    query = """
        SELECT id, source, title, summary, image AS image_url, link, published_ts
        FROM news
        WHERE 1=1
    """
    params = []

    if search_query:
        query += " AND (title LIKE ? OR summary LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    
    if source_filter:
        query += " AND source = ?"
        params.append(source_filter)

    query += " ORDER BY published_ts DESC LIMIT ?"
    params.append(limit)

    cur.execute(query, params)
    rows = cur.fetchall()
    con.close()

    noticias = []
    for r in rows:
        noticias.append({
            "source": r[1],
            "title": r[2],
            "summary": r[3] or "",
            "image_url": r[4],
            "link": r[5],
            "published_ts": r[6],
            "tiempo_relativo": tiempo_relativo(r[6]) if r[6] is not None else "Fecha desconocida"
        })
    return noticias


def obtener_fuentes():
    """Obtiene lista de fuentes únicas"""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT DISTINCT source FROM news ORDER BY source")
    fuentes = [row[0] for row in cur.fetchall()]
    con.close()
    return fuentes


def contar_noticias(search_query=None, source_filter=None):
    """Cuenta total de noticias según filtros"""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    query = "SELECT COUNT(*) FROM news WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND (title LIKE ? OR summary LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    
    if source_filter:
        query += " AND source = ?"
        params.append(source_filter)
    
    cur.execute(query, params)
    total = cur.fetchone()[0]
    con.close()
    return total


# ---------------------------
#      HOME / PORTAL
# ---------------------------
@app.route("/")
@login_required
def home():
    plan = session.get("plan", "free")

    # Límite solicitado por la URL
    limit = int(request.args.get("limit", 30))

    # Si el plan es FREE, forzamos máximo 30 noticias
    if plan == "free" and limit > 30:
        limit = 30

    search_query = request.args.get("search", "").strip()
    source_filter = request.args.get("source", "").strip()
    
    noticias = obtener_noticias(
        limit,
        search_query if search_query else None,
        source_filter if source_filter else None,
    )
    fuentes = obtener_fuentes()
    total_noticias = contar_noticias(
        search_query if search_query else None,
        source_filter if source_filter else None,
    )

    html = """
    <!DOCTYPE html>
    <html><head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Portal de Noticias</title>
    <style>
      *{margin:0;padding:0;box-sizing:border-box;}
      body{font-family:'Segoe UI',Tahoma,sans-serif;background:#f8fafc;min-height:100vh;}
      
      header{background:linear-gradient(135deg,#1e293b 0%,#334155 100%);color:white;
             box-shadow:0 4px 12px rgba(0,0,0,.1);position:sticky;top:0;z-index:100;}
      .header-top{display:flex;justify-content:space-between;align-items:center;
                  padding:15px 30px;border-bottom:1px solid rgba(255,255,255,.1);}
      .logo{display:flex;align-items:center;gap:12px;font-size:24px;font-weight:700;}
      .logo-icon{background:linear-gradient(135deg,#3b82f6,#8b5cf6);padding:8px 12px;
                 border-radius:10px;font-size:20px;}
      .user-info{display:flex;align-items:center;gap:20px;font-size:14px;}
      .user-name{display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);
                 padding:8px 15px;border-radius:20px;}
      .plan-badge{background:rgba(56,189,248,.15);color:#7dd3fc;padding:4px 10px;
                  border-radius:999px;font-size:11px;font-weight:700;text-transform:uppercase;
                  letter-spacing:0.05em;}
      .logout-btn{background:rgba(239,68,68,.9);padding:8px 16px;border-radius:8px;
                  text-decoration:none;color:white;font-weight:600;transition:all 0.3s;}
      .logout-btn:hover{background:#ef4444;transform:translateY(-2px);}
      .upgrade-link{background:rgba(249,115,22,.15);color:#fed7aa;padding:6px 12px;border-radius:999px;
                    font-size:12px;font-weight:700;text-decoration:none;display:inline-flex;
                    align-items:center;gap:6px;}
      .upgrade-link:hover{background:rgba(248,150,45,.3);}
      
      .search-bar{padding:20px 30px;display:flex;gap:15px;flex-wrap:wrap;align-items:center;}
      .search-input-wrapper{flex:1;min-width:300px;position:relative;}
      .search-icon{position:absolute;left:15px;top:50%;transform:translateY(-50%);color:#64748b;}
      .search-input{width:100%;padding:12px 15px 12px 45px;border:2px solid rgba(255,255,255,.2);
                    border-radius:12px;background:rgba(255,255,255,.1);color:white;font-size:15px;}
      .search-input::placeholder{color:rgba(255,255,255,.6);}
      .search-input:focus{outline:none;border-color:rgba(255,255,255,.4);background:rgba(255,255,255,.15);}
      
      .filter-select{padding:12px 15px;border:2px solid rgba(255,255,255,.2);border-radius:12px;
                     background:rgba(255,255,255,.1);color:white;font-size:15px;cursor:pointer;}
      .filter-select option{background:#1e293b;color:white;}
      
      .toolbar{background:white;padding:15px 30px;display:flex;gap:10px;flex-wrap:wrap;
               box-shadow:0 2px 8px rgba(0,0,0,.05);}
      .btn{padding:10px 18px;border-radius:10px;border:2px solid #e2e8f0;background:white;
           text-decoration:none;color:#1e293b;font-size:14px;font-weight:600;
           transition:all 0.3s;display:inline-flex;align-items:center;gap:8px;cursor:pointer;}
      .btn:hover{background:#f1f5f9;border-color:#cbd5e1;transform:translateY(-2px);}
      .btn-primary{background:linear-gradient(135deg,#3b82f6,#2563eb);color:white;border:none;}
      .btn-primary:hover{background:linear-gradient(135deg,#2563eb,#1d4ed8);}
      .btn.active{background:#3b82f6;color:white;border-color:#3b82f6;}
      
      .btn-upgrade{border-color:#f97316;color:#c2410c;}
      .btn-upgrade:hover{background:#ffedd5;border-color:#fb923c;}
      
      .stats{margin-left:auto;display:flex;align-items:center;gap:8px;color:#64748b;
             font-size:14px;font-weight:600;}
      
      .loading-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;
                      background:rgba(0,0,0,.5);z-index:200;justify-content:center;align-items:center;}
      .loading-overlay.active{display:flex;}
      .loading-content{background:white;padding:40px;border-radius:20px;text-align:center;
                       box-shadow:0 20px 60px rgba(0,0,0,.3);}
      .spinner{border:4px solid #e2e8f0;border-top:4px solid #3b82f6;border-radius:50%;
               width:50px;height:50px;animation:spin 1s linear infinite;margin:0 auto 20px;}
      @keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
      
      .cards-container{padding:30px;max-width:1600px;margin:0 auto;}
      .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:25px;}
      
      .card{background:white;border-radius:16px;box-shadow:0 4px 12px rgba(0,0,0,.08);
            overflow:hidden;transition:all 0.3s;cursor:pointer;display:flex;flex-direction:column;
            height:100%;}
      .card:hover{transform:translateY(-8px);box-shadow:0 12px 24px rgba(0,0,0,.15);}
      
      .card-image-wrapper{position:relative;width:100%;height:200px;overflow:hidden;background:#e2e8f0;}
      .card-image{width:100%;height:100%;object-fit:cover;transition:transform 0.3s;}
      .card:hover .card-image{transform:scale(1.05);}
      .card-source{position:absolute;top:12px;left:12px;background:rgba(59,130,246,.95);
                   color:white;padding:6px 14px;border-radius:20px;font-size:12px;font-weight:700;
                   backdrop-filter:blur(10px);}
      .card-time{position:absolute;bottom:12px;right:12px;background:rgba(0,0,0,.75);
                 color:white;padding:6px 12px;border-radius:20px;font-size:11px;font-weight:600;
                 backdrop-filter:blur(10px);display:flex;align-items:center;gap:5px;}
      
      .card-content{padding:20px;flex:1;display:flex;flex-direction:column;}
      .card-title{font-size:18px;font-weight:700;color:#1e293b;margin-bottom:12px;
                  line-height:1.4;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;
                  overflow:hidden;}
      .card-title a{text-decoration:none;color:inherit;transition:color 0.3s;}
      .card-title a:hover{color:#3b82f6;}
      .card-summary{font-size:14px;color:#64748b;line-height:1.6;display:-webkit-box;
                    -webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;flex:1;}
      
      .card-footer{padding:0 20px 20px;display:flex;justify-content:space-between;align-items:center;}
      .read-more{color:#3b82f6;font-size:14px;font-weight:600;text-decoration:none;
                 display:flex;align-items:center;gap:5px;}
      .read-more:hover{gap:8px;}
      
      .no-results{text-align:center;padding:80px 20px;}
      .no-results-icon{font-size:64px;margin-bottom:20px;}
      .no-results h2{font-size:24px;color:#1e293b;margin-bottom:10px;}
      .no-results p{color:#64748b;font-size:16px;}
      
      @media(max-width:768px){
        .header-top{flex-direction:column;gap:15px;text-align:center;}
        .logo{font-size:20px;}
        .search-bar{padding:15px 20px;}
        .toolbar{padding:15px 20px;justify-content:center;}
        .stats{margin-left:0;width:100%;justify-content:center;}
        .cards-container{padding:20px;}
        .cards{grid-template-columns:1fr;}
      }
    </style>
    </head>
    <body>
    
    <div class="loading-overlay" id="loadingOverlay">
      <div class="loading-content">
        <div class="spinner"></div>
        <h3>Actualizando noticias...</h3>
        <p style="color:#64748b;margin-top:10px;">Esto puede tomar unos segundos</p>
      </div>
    </div>
    
    <header>
      <div class="header-top">
        <div class="logo">
          <div class="logo-icon">📰</div>
          <div>Portal de Noticias</div>
        </div>
        <div class="user-info">
          <div class="user-name">
            <span>👤</span>
            <span>{{ session['username'] }}</span>
            <span class="plan-badge">
              PLAN {{ plan.upper() }}
            </span>
          </div>
          {% if plan == 'free' %}
          <a href="{{ url_for('upgrade') }}" class="upgrade-link">
            🔺 Subir a Plan Pro
          </a>
          {% endif %}
          <a href="{{ url_for('logout') }}" class="logout-btn">Cerrar sesión</a>
        </div>
      </div>
      
      <div class="search-bar">
        <div class="search-input-wrapper">
          <span class="search-icon">🔍</span>
          <input type="text" class="search-input" placeholder="Buscar noticias..." 
                 id="searchInput" value="{{ request.args.get('search', '') }}">
        </div>
        <select class="filter-select" id="sourceFilter">
          <option value="">📂 Todas las fuentes</option>
          {% for f in fuentes %}
            <option value="{{ f }}" {% if request.args.get('source') == f %}selected{% endif %}>{{ f }}</option>
          {% endfor %}
        </select>
      </div>
    </header>
    
    <div class="toolbar">
      <a href="#" class="btn btn-primary" onclick="actualizarNoticias(event)">
        🔄 Actualizar ahora
      </a>
      <a href="/?limit=30" class="btn {% if request.args.get('limit', '30') == '30' %}active{% endif %}">
        Mostrar 30
      </a>
      {% if plan in ['pro', 'admin'] %}
      <a href="/?limit=60" class="btn {% if request.args.get('limit') == '60' %}active{% endif %}">
        Mostrar 60
      </a>
      <a href="/?limit=100" class="btn {% if request.args.get('limit') == '100' %}active{% endif %}">
        Mostrar 100
      </a>
      {% endif %}
      <a href="{{ url_for('export_csv') }}" class="btn">
        ⬇️ Exportar CSV
      </a>
      {% if plan in ['pro', 'admin'] %}
      <a href="{{ url_for('metricas') }}" class="btn">
        📊 Métricas
      </a>
      <a href="{{ url_for('clusters') }}" class="btn">
        🧩 Clusters
      </a>
      {% endif %}
      {% if plan == 'free' %}
      <a href="{{ url_for('upgrade') }}" class="btn btn-upgrade">
        🔺 Subir de plan
      </a>
      {% endif %}
      <div class="stats">
        📊 Mostrando {{ noticias|length }} de {{ total_noticias }} noticias
      </div>
    </div>
    
    <div class="cards-container">
      {% if noticias %}
        <div class="cards">
          {% for n in noticias %}
            <div class="card">
              <div class="card-image-wrapper">
                <img class="card-image" 
                     src="{{ n.image_url if n.image_url else 'https://via.placeholder.com/600x400/3b82f6/ffffff?text=Sin+Imagen' }}"
                     alt="{{ n.title }}">
                <div class="card-source">{{ n.source }}</div>
                <div class="card-time">
                  🕒 {{ n.tiempo_relativo }}
                </div>
              </div>
              <div class="card-content">
                <h3 class="card-title">
                  <a href="{{ n.link }}" target="_blank">{{ n.title }}</a>
                </h3>
                <p class="card-summary">{{ n.summary }}</p>
              </div>
              <div class="card-footer">
                <a href="{{ n.link }}" target="_blank" class="read-more">
                  Leer más →
                </a>
              </div>
            </div>
          {% endfor %}
        </div>
      {% else %}
        <div class="no-results">
          <div class="no-results-icon">🔍</div>
          <h2>No se encontraron noticias</h2>
          <p>Intenta ajustar los filtros de búsqueda</p>
        </div>
      {% endif %}
    </div>
    
    <script>
      let searchTimeout;
      document.getElementById('searchInput').addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          aplicarFiltros();
        }, 500);
      });
      
      document.getElementById('sourceFilter').addEventListener('change', function() {
        aplicarFiltros();
      });
      
      function aplicarFiltros() {
        const search = document.getElementById('searchInput').value;
        const source = document.getElementById('sourceFilter').value;
        const limit = new URLSearchParams(window.location.search).get('limit') || '30';
        
        let url = '/?limit=' + limit;
        if (search) url += '&search=' + encodeURIComponent(search);
        if (source) url += '&source=' + encodeURIComponent(source);
        
        window.location.href = url;
      }
      
      function actualizarNoticias(e) {
        e.preventDefault();
        document.getElementById('loadingOverlay').classList.add('active');
        
        fetch('/update')
          .then(response => response.text())
          .then(data => {
            document.getElementById('loadingOverlay').classList.remove('active');
            location.reload();
          })
          .catch(error => {
            document.getElementById('loadingOverlay').classList.remove('active');
            alert('Error al actualizar: ' + error);
          });
      }
    </script>
    
    </body></html>
    """

    return render_template_string(
        html, noticias=noticias, fuentes=fuentes, total_noticias=total_noticias, plan=plan
    )


# ---------------------------
#     ACTUALIZAR NOW
# ---------------------------
@app.route("/update")
@login_required
def update_now():
    nuevos = fetch_all()
    return f"Actualizado. Noticias nuevas: {nuevos}"


# ---------------------------
#      EXPORTAR CSV
# ---------------------------
@app.route("/export")
@login_required
def export_csv():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT source, title, summary, link, published_ts FROM news")
    rows = cur.fetchall()
    con.close()

    output_lines = []
    output_lines.append("source,title,summary,link,published_ts")
    for r in rows:
        safe = [str(x).replace('"', '""').replace("\n", " ") for x in r]
        line = '"' + '","'.join(safe) + '"'
        output_lines.append(line)
    csv_data = "\n".join(output_lines)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=noticias.csv"}
    )


# ---------------------------
#       MÉTRICAS
# ---------------------------
@app.route("/metricas")
@login_required
def metricas():
    plan = session.get("plan", "free")
    if plan not in ("pro", "admin"):
        return redirect(url_for("home"))

    html = """
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Métricas</title>
    <style>
      body{font-family:'Segoe UI',Tahoma,sans-serif;background:#f8fafc;margin:0;padding:40px;}
      .container{max-width:800px;margin:0 auto;background:white;padding:40px;border-radius:20px;
                 box-shadow:0 4px 12px rgba(0,0,0,.08);}
      h1{text-align:center;color:#1e293b;margin-bottom:10px;}
      p{text-align:center;color:#64748b;margin-bottom:30px;}
      .btn{display:inline-block;padding:10px 20px;background:#3b82f6;color:white;
           text-decoration:none;border-radius:10px;font-weight:600;transition:all 0.3s;}
      .btn:hover{background:#2563eb;transform:translateY(-2px);}
      .btn-container{text-align:center;}
    </style></head>
    <body>
      <div class="container">
        <h1>📊 Métricas del modelo</h1>
        <p>Aquí podrás mostrar tus gráficas de accuracy, F1, etc. (solo Plan Pro)</p>
        <div class="btn-container">
          <a href="/" class="btn">← Volver al inicio</a>
        </div>
      </div>
    </body></html>
    """
    return html


# ---------------------------
#       CLUSTERS
# ---------------------------
@app.route("/clusters")
@login_required
def clusters():
    plan = session.get("plan", "free")
    if plan not in ("pro", "admin"):
        return redirect(url_for("home"))

    html = """
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Clusters</title>
    <style>
      body{font-family:'Segoe UI',Tahoma,sans-serif;background:#f8fafc;margin:0;padding:40px;}
      .container{max-width:800px;margin:0 auto;background:white;padding:40px;border-radius:20px;
                 box-shadow:0 4px 12px rgba(0,0,0,.08);}
      h1{text-align:center;color:#1e293b;margin-bottom:10px;}
      p{text-align:center;color:#64748b;margin-bottom:30px;}
      .btn{display:inline-block;padding:10px 20px;background:#3b82f6;color:white;
           text-decoration:none;border-radius:10px;font-weight:600;transition:all 0.3s;}
      .btn:hover{background:#2563eb;transform:translateY(-2px);}
      .btn-container{text-align:center;}
    </style></head>
    <body>
      <div class="container">
        <h1>🧩 Clusters de noticias</h1>
        <p>Aquí podrás mostrar los grupos de noticias generados por tu script de clustering (solo Plan Pro)</p>
        <div class="btn-container">
          <a href="/" class="btn">← Volver al inicio</a>
        </div>
      </div>
    </body></html>
    """
    return html


# ---------------------------
#       UPGRADE PLAN
# ---------------------------
@app.route("/upgrade", methods=["GET", "POST"])
@login_required
def upgrade():
    plan = session.get("plan", "free")
    # Si ya es pro o admin, no tiene sentido
    if plan in ("pro", "admin"):
        return redirect(url_for("home"))

    if request.method == "POST":
        user_id = session.get("user_id")
        if user_id:
            con = sqlite3.connect(DB_PATH)
            cur = con.cursor()
            cur.execute("UPDATE users SET plan = 'pro' WHERE id = ?", (user_id,))
            con.commit()
            con.close()
            session["plan"] = "pro"
        return redirect(url_for("home"))

    html = """
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Subir de plan</title>
    <style>
      body{font-family:'Segoe UI',Tahoma,sans-serif;background:#f8fafc;margin:0;padding:40px;}
      .container{max-width:800px;margin:0 auto;background:white;padding:40px;border-radius:20px;
                 box-shadow:0 4px 12px rgba(0,0,0,.08);}
      h1{text-align:center;color:#1e293b;margin-bottom:10px;}
      h2{text-align:center;color:#0f172a;margin-bottom:10px;}
      p{text-align:center;color:#64748b;margin-bottom:10px;}
      ul{max-width:500px;margin:20px auto;text-align:left;color:#475569;}
      li{margin-bottom:8px;}
      .plans{display:flex;flex-wrap:wrap;gap:20px;justify-content:center;margin:30px 0;}
      .plan-card{border-radius:16px;padding:20px 25px;min-width:260px;border:2px solid #e2e8f0;}
      .plan-card.pro{border-color:#3b82f6;background:#eff6ff;}
      .plan-title{font-size:18px;font-weight:700;margin-bottom:5px;}
      .plan-price{font-size:24px;font-weight:800;margin-bottom:10px;color:#0f172a;}
      .tag{display:inline-block;margin-bottom:8px;font-size:11px;padding:3px 8px;border-radius:999px;
           background:#e5e7eb;color:#374151;}
      .tag-pro{background:#dbeafe;color:#1d4ed8;}
      .btn{display:inline-block;padding:10px 20px;background:#3b82f6;color:white;
           text-decoration:none;border-radius:10px;font-weight:600;transition:all 0.3s;border:none;
           cursor:pointer;}
      .btn:hover{background:#2563eb;transform:translateY(-2px);}
      .btn-sec{background:#e5e7eb;color:#111827;}
      .btn-sec:hover{background:#d4d4d8;}
      .btn-container{text-align:center;margin-top:20px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap;}
      form{display:inline;}
    </style></head>
    <body>
      <div class="container">
        <h1>🔺 Subir de plan</h1>
        <p>Actualmente estás en <b>Plan Free</b>. Puedes subir a <b>Plan Pro</b> (demo) para desbloquear más funciones.</p>

        <div class="plans">
          <div class="plan-card">
            <div class="plan-title">Plan Free</div>
            <span class="tag">Actual</span>
            <p class="plan-price">S/ 0</p>
            <ul>
              <li>Hasta 30 noticias visibles</li>
              <li>Búsqueda y filtros básicos</li>
              <li>Exportar CSV</li>
              <li>Sin acceso a métricas avanzadas</li>
              <li>Sin acceso a clusters de noticias</li>
            </ul>
          </div>

          <div class="plan-card pro">
            <div class="plan-title">Plan Pro (Demo)</div>
            <span class="tag tag-pro">Recomendado</span>
            <p class="plan-price">S/ 20 (demo)</p>
            <ul>
              <li>Más noticias (60, 100, ...)</li>
              <li>Acceso a métricas del modelo</li>
              <li>Acceso a clusters de noticias</li>
              <li>Mejor análisis y segmentación</li>
              <li>Ideal para proyectos académicos</li>
            </ul>
          </div>
        </div>

        <div class="btn-container">
          <form method="post">
            <button type="submit" class="btn">Activar Plan Pro (demo)</button>
          </form>
          <a href="/" class="btn btn-sec">← Volver sin cambiar</a>
        </div>
      </div>
    </body></html>
    """
    return html


# ---------------------------
#        MAIN
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
