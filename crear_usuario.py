# crear_usuario.py
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "noticias.db"

def init_users_table():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)
    con.commit()
    con.close()

def crear_usuario():
    username = input("Nuevo nombre de usuario: ").strip()
    password = input("Nueva contraseña: ").strip()

    if not username or not password:
        print("Usuario y contraseña no pueden estar vacíos.")
        return

    password_hash = generate_password_hash(password)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        con.commit()
        print("Usuario creado correctamente.")
    except sqlite3.IntegrityError:
        print("Error: ese usuario ya existe.")
    finally:
        con.close()

if __name__ == "__main__":
    init_users_table()
    crear_usuario()
