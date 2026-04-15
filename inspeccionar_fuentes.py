# inspeccionar_fuentes.py
import sqlite3

con = sqlite3.connect("noticias.db")
cur = con.cursor()

print("Noticias por fuente:")
for row in cur.execute("SELECT source, COUNT(*) FROM news GROUP BY source ORDER BY COUNT(*) DESC"):
    print(f"{row[0]:20s} {row[1]}")
con.close()
