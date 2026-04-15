# logistica.py
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    roc_curve
)

DB_PATH = "noticias.db"
OBJETIVO_FUENTE = "RPP"   # puedes cambiar por "El Comercio", "La República", etc.

# ==========================================================
# 1. Cargar los datos
# ==========================================================
def cargar_datos(db_path: str) -> pd.DataFrame:
    con = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        "SELECT source, title, COALESCE(summary,'') AS summary FROM news",
        con
    )
    con.close()
    df["texto"] = (df["title"].fillna("") + " " + df["summary"].fillna("")).str.strip()
    df["y"] = (df["source"] == OBJETIVO_FUENTE).astype(int)
    df = df[df["texto"].str.len() > 0].copy()
    return df

# ==========================================================
# 2. Entrenar modelo y calcular métricas
# ==========================================================
def entrenar_y_evaluar(df: pd.DataFrame):
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=2)
    X = vectorizer.fit_transform(df["texto"])
    y = df["y"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=2000, solver="lbfgs")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    # ======================================================
    # Métricas principales
    # ======================================================
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)

    print("\n================== MÉTRICAS ==================")
    print(f"Exactitud (Accuracy): {acc:.4f}")
    print(f"Precisión: {prec:.4f}")
    print(f"Recall (Sensibilidad): {rec:.4f}")
    print(f"F1-score: {f1:.4f}")
    print(f"AUC-ROC: {auc:.4f}")

    # ======================================================
    # Matriz de confusión
    # ======================================================
    cm = confusion_matrix(y_test, y_pred)
    print("\nMatriz de confusión:\n", cm)
    print("\nReporte de clasificación:\n")
    print(classification_report(y_test, y_pred, target_names=["No RPP", "RPP"], digits=4))

    # ======================================================
    # Gráficos: Curva ROC y Matriz de Confusión
    # ======================================================
    # Curva ROC
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    plt.figure(figsize=(10,4))

    plt.subplot(1,2,1)
    plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"AUC = {auc:.2f}")
    plt.plot([0,1],[0,1], color="navy", lw=1, linestyle="--")
    plt.xlabel("Tasa Falsos Positivos (FPR)")
    plt.ylabel("Tasa Verdaderos Positivos (TPR)")
    plt.title("Curva ROC")
    plt.legend()

    # Matriz de confusión visual
    plt.subplot(1,2,2)
    plt.imshow(cm, cmap="Blues")
    plt.title("Matriz de Confusión")
    plt.colorbar()
    plt.xticks([0,1], ["No RPP", "RPP"])
    plt.yticks([0,1], ["No RPP", "RPP"])
    plt.xlabel("Predicción")
    plt.ylabel("Real")
    for i in range(2):
        for j in range(2):
            plt.text(j, i, cm[i,j], ha="center", va="center", color="black", fontsize=12)
    plt.tight_layout()
    plt.show()

# ==========================================================
# 3. Ejecución principal
# ==========================================================
def main():
    print(f"Cargando datos desde {DB_PATH} ...")
    df = cargar_datos(DB_PATH)
    print(f"Total de noticias con texto: {len(df)}")
    if len(df["y"].unique()) < 2:
        print(f"No hay suficientes clases (se necesita noticias de '{OBJETIVO_FUENTE}' y otras fuentes).")
        return
    entrenar_y_evaluar(df)

if __name__ == "__main__":
    main()
