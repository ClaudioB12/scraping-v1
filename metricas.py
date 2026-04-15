# metricas.py
import sqlite3
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)

DB_PATH = "noticias.db"
OBJETIVO_FUENTE = "RPP"  # puedes cambiarlo a "El Comercio", etc.

def calcular_metricas():
    # 1. Cargar datos
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT source, title, COALESCE(summary,'') AS summary FROM news",
        con
    )
    con.close()

    df["texto"] = (df["title"].fillna("") + " " + df["summary"].fillna("")).str.strip()
    df["y"] = (df["source"] == OBJETIVO_FUENTE).astype(int)
    df = df[df["texto"].str.len() > 0].copy()

    if len(df) < 10 or df["y"].nunique() < 2:
        # Muy pocos datos o solo una clase
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "auc": 0.0,
            "matriz": [[0, 0], [0, 0]],
            "total": int(len(df))
        }

    # 2. Vectorización
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=2
    )
    X = vectorizer.fit_transform(df["texto"])
    y = df["y"].values

    # 3. Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    # 4. Modelo
    model = LogisticRegression(max_iter=2000)
    model.fit(X_train, y_train)

    # 5. Predicciones
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    # 6. Métricas
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_test, y_proba)
    except Exception:
        auc = 0.0

    cm = confusion_matrix(y_test, y_pred)

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "auc": round(auc, 4),
        "matriz": cm.tolist(),
        "total": int(len(df))
    }
