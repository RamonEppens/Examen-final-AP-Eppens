"""
Feature engineering para BGG — reutilizable desde notebooks 02, 03 y 04.

API principal
-------------
    X, y, feat_names, top_mechs, top_cats = build_features(df_train)
    X_test, y_test, _, _, _ = build_features(df_test, top_mechs=top_mechs, top_cats=top_cats)

Modo fit  (top_mechs=None): calcula top-N desde df — usar SOLO en datos de train.
Modo apply (top_mechs=list): usa la lista provista — usar en validation / test.
"""

from __future__ import annotations

import re
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer

# ── Constantes globales ────────────────────────────────────────────────────────

TARGET_COL = "average"

LEAKAGE_COLS = ["bayes_average", "rank", "users_rated"]  # prohibidas como features

BASE_NUM_COLS = [
    "weight",
    "year",
    "min_players",
    "max_players",
    "min_playtime",
    "max_playtime",
    "min_age",
    "unlimited_players",
]


# ── Helpers internos ───────────────────────────────────────────────────────────

def _count_pipe(series: pd.Series) -> Counter:
    """Cuenta elementos en una columna pipe-separated."""
    counter: Counter = Counter()
    for val in series.dropna():
        for item in str(val).split("|"):
            item = item.strip()
            if item:
                counter[item] += 1
    return counter


def _sanitize(name: str) -> str:
    """Reemplaza caracteres no alfanuméricos con _ para compatibilidad con LightGBM/JSON."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def _binarize(series: pd.Series, items: list[str], prefix: str) -> pd.DataFrame:
    """
    Crea columnas binarias para cada item con exact-match en pipe-split.
    Usa MultiLabelBinarizer con classes fijas para garantizar consistencia
    entre train y test. Los nombres de columna se sanitizan para LightGBM.
    """
    parsed = series.apply(
        lambda x: frozenset(i.strip() for i in str(x).split("|"))
        if pd.notna(x)
        else frozenset()
    )
    mlb = MultiLabelBinarizer(classes=items)
    matrix = mlb.fit_transform(parsed)
    cols = [f"{prefix}{_sanitize(c)}" for c in mlb.classes_]
    return pd.DataFrame(matrix, columns=cols, index=series.index)


# ── Features de segunda ronda (ronda 2) ───────────────────────────────────────

MECH_FAMILIES: dict[str, list[str]] = {
    "fam_card_deck":   ["Deck Building", "Hand Management", "Card Drafting",
                        "Set Collection", "Trick-taking", "Multi-Use Cards"],
    "fam_worker":      ["Worker Placement"],
    "fam_dice":        ["Dice Rolling", "Re-rolling and Locking"],
    "fam_cooperative": ["Cooperative Game", "Solo / Solitaire Game", "Team-Based Game"],
    "fam_engine":      ["Engine Building", "Resource Management"],
    "fam_area":        ["Area Majority / Influence", "Area Movement"],
    "fam_deduction":   ["Deduction", "Hidden Roles", "Traitor Game"],
    "fam_route":       ["Route / Network Building", "Pick-up and Deliver"],
    "fam_tile":        ["Tile Placement", "Pattern Building"],
    "fam_auction":     ["Auction / Bidding"],
}


def add_v2_features(
    X: pd.DataFrame,
    df: pd.DataFrame,
    medians: dict[str, float] | None = None,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """
    Agrega las features de segunda ronda seleccionadas en el análisis de errores.

    Nuevas features
    ---------------
    playtime_ratio  : max_playtime / (min_playtime + 1)
    players_range   : max_players - min_players
    weight_missing  : 1 si weight es NaN (centinela de dato faltante en BGG)
    fam_*           : 10 flags binarias de familias temáticas de mecánicas

    Parámetros
    ----------
    X       : DataFrame base (output de build_features).
    df      : DataFrame fuente con columnas originales (mismo índice que X).
    medians : Dict con medianas de imputación. None → calcula desde df (solo en train).
              Guardar y reusar en test para consistencia.

    Retorna
    -------
    X_aug   : X con features adicionales.
    medians : Dict de medianas usadas (para persistir en artifacts).
    """
    X = X.copy()

    if medians is None:
        medians = {
            "max_playtime": float(df["max_playtime"].median()),
            "min_playtime": float(df["min_playtime"].fillna(0).median()),
            "min_players":  float(df["min_players"].median()),
            "max_players":  float(df["max_players"].median()),
        }

    mp   = df["max_playtime"].fillna(medians["max_playtime"])
    minp = df["min_playtime"].fillna(medians["min_playtime"])
    mn   = df["min_players"].fillna(medians["min_players"])
    mxp  = df["max_players"].fillna(medians["max_players"])

    X["playtime_ratio"]  = (mp / (minp + 1)).values
    X["players_range"]   = (mxp - mn).values
    X["weight_missing"]  = df["weight"].isna().astype(float).values

    mc = df["mechanics"].fillna("")
    for fam_name, terms in MECH_FAMILIES.items():
        X[fam_name] = mc.apply(
            lambda s, t=terms: int(any(term.lower() in str(s).lower() for term in t))
        ).values

    return X, medians


# ── Función principal ──────────────────────────────────────────────────────────

def build_features(
    df: pd.DataFrame,
    top_mechs: list[str] | None = None,
    top_cats: list[str] | None = None,
    top_n_mech: int = 40,
    top_n_cat: int = 30,
) -> tuple[pd.DataFrame, pd.Series, list[str], list[str], list[str]]:
    """
    Construye la matriz de features para el dataset BGG.

    Parámetros
    ----------
    df          : DataFrame limpio (bgg_games_clean.csv o subconjunto).
    top_mechs   : Lista de mecánicas a binarizar.
                  None → calcula desde df (modo fit, usar en train).
    top_cats    : Lista de categorías a binarizar.
                  None → calcula desde df (modo fit, usar en train).
    top_n_mech  : Cuántas mecánicas top usar cuando top_mechs es None.
    top_n_cat   : Cuántas categorías top usar cuando top_cats es None.

    Retorna
    -------
    X           : DataFrame de features. Los NaN numéricos NO se imputan
                  (LightGBM/XGBoost los manejan nativo; para modelos lineales
                  y RF usar SimpleImputer dentro del pipeline de sklearn).
    y           : Series del target (average).
    feat_names  : Lista de nombres de features (igual a list(X.columns)).
    top_mechs   : Lista de mecánicas usadas (para reusar en test).
    top_cats    : Lista de categorías usadas (para reusar en test).
    """
    df = df.copy()

    # — Features derivadas —
    df["n_mechanics"]  = df["mechanics"].str.split("|").str.len()
    df["n_categories"] = df["categories"].str.split("|").str.len()

    # unlimited_players puede venir como BooleanDtype de pandas → float
    if "unlimited_players" in df.columns:
        df["unlimited_players"] = df["unlimited_players"].astype(float)

    num_cols = BASE_NUM_COLS + ["n_mechanics", "n_categories"]

    # — Fit top_mechs / top_cats (solo desde train) —
    if top_mechs is None:
        top_mechs = [m for m, _ in _count_pipe(df["mechanics"]).most_common(top_n_mech)]
    if top_cats is None:
        top_cats = [c for c, _ in _count_pipe(df["categories"]).most_common(top_n_cat)]

    # — Binarización multilabel —
    mech_df = _binarize(df["mechanics"],   top_mechs, "mech_")
    cat_df  = _binarize(df["categories"],  top_cats,  "cat_")

    X = pd.concat(
        [
            df[num_cols].reset_index(drop=True),
            mech_df.reset_index(drop=True),
            cat_df.reset_index(drop=True),
        ],
        axis=1,
    )

    y = df[TARGET_COL].reset_index(drop=True)

    return X, y, list(X.columns), top_mechs, top_cats
