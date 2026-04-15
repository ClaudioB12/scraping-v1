# cluster.py
import sqlite3
import pandas as pd
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

DB_PATH = "noticias.db"

# ============================
# 1. Cargar datos desde SQLite
# ============================
def cargar_datos(db_path: str) -> pd.DataFrame:
    con = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        "SELECT source, title, COALESCE(summary,'') AS summary FROM news",
        con
    )
    con.close()

    df["texto"] = (df["title"].fillna("") + " " + df["summary"].fillna("")).str.strip()
    df = df[df["texto"].str.len() > 0].copy()
    df.reset_index(drop=True, inplace=True)
    return df

# ============================
# 2. Ajustar KMeans
# ============================
def _ajustar_kmeans(df: pd.DataFrame, k: int = 5):
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=3
    )
    X = vectorizer.fit_transform(df["texto"])

    kmeans = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )
    etiquetas = kmeans.fit_predict(X)
    df = df.copy()
    df["cluster"] = etiquetas

    try:
        sil = silhouette_score(X, etiquetas)
    except Exception:
        sil = np.nan

    return df, kmeans, vectorizer, sil

# ============================================
# 3. Resumen de clusters para usar en la WEB
# ============================================
def resumen_clusters(k: int = 5, n_palabras: int = 10, n_ejemplos: int = 5):
    df = cargar_datos(DB_PATH)
    if len(df) == 0:
        return {"total": 0, "k": k, "silhouette": None, "clusters": []}

    df_cl, kmeans, vectorizer, sil = _ajustar_kmeans(df, k)
    feature_names = np.array(vectorizer.get_feature_names_out())

    clusters_info = []
    for c in range(k):
        subset = df_cl[df_cl["cluster"] == c]
        centroide = kmeans.cluster_centers_[c]
        top_idx = np.argsort(centroide)[-n_palabras:][::-1]
        top_words = feature_names[top_idx].tolist()

        ejemplos = [
            {"source": row["source"], "title": row["title"]}
            for _, row in subset.head(n_ejemplos).iterrows()
        ]

        clusters_info.append({
            "id": c,
            "n": int(len(subset)),
            "top_words": top_words,
            "ejemplos": ejemplos
        })

    return {
        "total": int(len(df_cl)),
        "k": k,
        "silhouette": None if np.isnan(sil) else float(round(sil, 4)),
        "clusters": clusters_info
    }

# ============================================
# 4. main() para consola (como ya usabas)
# ============================================
def main():
    df = cargar_datos(DB_PATH)
    print(f"Total de noticias con texto: {len(df)}")
    if len(df) < 20:
        print("Hay muy pocas noticias para hacer clustering de forma útil.")
        return

    k = 5
    df_cl, kmeans, vectorizer, sil = _ajustar_kmeans(df, k)
    X_shape = df_cl.shape[0]

    print(f"Vector TF-IDF con forma: ({X_shape}, {len(vectorizer.get_feature_names_out())})")
    if not np.isnan(sil):
        print(f"\nSilhouette score (calidad de clusters): {sil:.4f}")
    else:
        print("\nSilhouette score no disponible.")

    feature_names = np.array(vectorizer.get_feature_names_out())

    for c in range(k):
        print("\n" + "="*60)
        print(f"CLUSTER {c}")
        subset = df_cl[df_cl["cluster"] == c]
        print(f"Noticias en este cluster: {len(subset)}")

        centroide = kmeans.cluster_centers_[c]
        top_idx = np.argsort(centroide)[-15:][::-1]
        top_words = feature_names[top_idx]
        print("\nPalabras más representativas:")
        print(", ".join(top_words))

        print("\nEjemplos de títulos:")
        for _, row in subset.head(5).iterrows():
            print(f" - [{row['source']}] {row['title'][:120]}")

    df_cl.to_csv("noticias_clusterizadas.csv", index=False, encoding="utf-8-sig")
    print("\nResultados guardados en 'noticias_clusterizadas.csv'")

if __name__ == "__main__":
    main()
