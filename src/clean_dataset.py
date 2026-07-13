"""
Limpieza del dataset de BGG según decisiones tomadas en EDA Parte 1
(notebooks/01_eda.ipynb, sección 6 — Decisiones de limpieza).

Decisiones aplicadas
--------------------
1. Filtro de votos  : Users rated >= 50
2. Filtro de año    : 1900 <= Year <= 2026
3. Deduplicación    : drop_duplicates('game_id')
4. Centinelas BGG   : weight/min_players/max_players/min_playtime/max_playtime/min_age == 0 -> NaN
5. unlimited_players: max_players == 999 -> flag booleana + cap al p99
6. Playtime cap     : min_playtime y max_playtime capeados al p99
7. Columnas excluidas como features (documentadas, NO se eliminan del CSV):
   - bayes_average : funcion directa del target -> leakage
   - rank          : reordenacion determinista de bayes_average -> leakage
   - users_rated   : valido solo para filtro/analisis; no disponible en inferencia pre-lanzamiento

Uso
---
    python src/clean_dataset.py                      # lee data/processed/bgg_games.csv
    python src/clean_dataset.py --input my_file.csv  # CSV alternativo
    python src/clean_dataset.py --report-only        # solo estadisticas, no escribe

La funcion clean() tambien se puede importar directamente desde otros modulos.
"""

from __future__ import annotations

import os
import argparse
import numpy as np
import pandas as pd

# ── Constantes de las decisiones de limpieza ──────────────────────────────────
MIN_VOTES   = 50
MIN_YEAR    = 1900
MAX_YEAR    = 2026

SENTINEL_ZERO_COLS = [
    "weight", "min_players", "max_players",
    "min_playtime", "max_playtime", "min_age",
]

LEAKAGE_COLS = ["bayes_average", "rank", "users_rated",
                "Bayes average", "Rank", "Users rated"]

DEFAULT_IN  = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "bgg_games.csv")
DEFAULT_OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "bgg_games_clean.csv")


# ── Funcion principal ──────────────────────────────────────────────────────────

def clean(df: pd.DataFrame, verbose: bool = True) -> tuple[pd.DataFrame, dict]:
    """
    Aplica el pipeline de limpieza acordado en EDA Parte 1.

    Parametros
    ----------
    df      : DataFrame crudo (output de build_dataset.py o load_kaggle.py).
              Acepta tanto nombres con mayusculas (beefsack) como snake_case (API/Kaggle).
    verbose : si True, imprime el reporte de exclusiones.

    Retorna
    -------
    df_clean : DataFrame limpio.
    report   : dict con metricas de cada paso de filtrado.
    """
    # Normalizar nombres de columna a snake_case
    col_rename = {
        "ID": "game_id", "Name": "name", "Year": "year",
        "Rank": "rank", "Average": "average",
        "Bayes average": "bayes_average", "Users rated": "users_rated",
    }
    df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})

    id_col   = "game_id"
    year_col = "year"
    vote_col = "users_rated"
    total    = len(df)

    report: dict = {"total_bruto": total}

    # 1. Deduplicacion de IDs
    n_before = len(df)
    df = df.drop_duplicates(subset=id_col, keep="first")
    report["excl_duplicados"] = n_before - len(df)

    # 2. Year <= 0 o faltante
    mask_neg = df[year_col].isna() | (df[year_col] <= 0)
    excl_neg = df[mask_neg][["game_id", "name", year_col]].copy()
    df = df[~mask_neg]
    report["excl_year_nulo_o_cero"] = len(excl_neg)
    report["ejemplos_year_nulo"]    = excl_neg.head(5).to_dict("records")

    # 3. 1 <= Year < 1900 (historicos/folkloricos sin anio fiable)
    mask_old = df[year_col] < MIN_YEAR
    excl_old = df[mask_old][["game_id", "name", year_col]].copy()
    df = df[~mask_old]
    report["excl_year_lt_1900"] = len(excl_old)
    report["ejemplos_year_old"] = excl_old.head(5).to_dict("records")

    # 4. Year > 2026 (pre-lanzamientos y placeholders)
    mask_fut = df[year_col] > MAX_YEAR
    excl_fut = df[mask_fut][["game_id", "name", year_col]].copy()
    df = df[~mask_fut]
    report["excl_year_gt_2026"] = len(excl_fut)
    report["ejemplos_year_fut"] = excl_fut.head(5).to_dict("records")

    report["subtotal_tras_anio"] = len(df)

    # 5. Users rated < 50
    if vote_col in df.columns:
        mask_votes = df[vote_col] < MIN_VOTES
        excl_votes = df[mask_votes]
        df = df[~mask_votes]
        report["excl_votes_lt_50"] = len(excl_votes)
    else:
        report["excl_votes_lt_50"] = None

    report["subtotal_tras_votos"] = len(df)

    # 6. Centinelas BGG: 0 -> NaN (el cero significa "sin dato", no cero real)
    sentinel_report = {}
    for col in SENTINEL_ZERO_COLS:
        if col in df.columns:
            n_zeros = int((df[col] == 0).sum())
            if n_zeros:
                df[col] = df[col].replace(0, np.nan)
            sentinel_report[col] = n_zeros
    report["sentinel_zeros"] = sentinel_report

    # 7. unlimited_players flag + cap max_players al p99
    if "max_players" in df.columns:
        df["unlimited_players"] = (df["max_players"] == 999).astype("boolean")
        n_unlimited = int(df["unlimited_players"].sum())
        p99_mp = float(df["max_players"].quantile(0.99))
        df["max_players"] = df["max_players"].clip(upper=p99_mp)
        report["unlimited_players_count"] = n_unlimited
        report["max_players_p99_cap"]     = p99_mp
    else:
        report["unlimited_players_count"] = None
        report["max_players_p99_cap"]     = None

    # 8. Playtime: distribucion de extremos + cap al p99
    playtime_stats = {}
    for col in ["min_playtime", "max_playtime"]:
        if col in df.columns:
            col_clean = df[col].dropna()
            p99 = float(col_clean.quantile(0.99))
            stats = {
                "p50":         float(col_clean.quantile(0.50)),
                "p75":         float(col_clean.quantile(0.75)),
                "p90":         float(col_clean.quantile(0.90)),
                "p95":         float(col_clean.quantile(0.95)),
                "p99":         p99,
                "max_raw":     float(col_clean.max()),
                "n_over_1440": int((col_clean > 1440).sum()),
            }
            df[col] = df[col].clip(upper=p99)
            playtime_stats[col] = stats
    report["playtime_stats"] = playtime_stats

    # 9. Nulos finales por columna (post todas las transformaciones)
    nulls = df.isnull().sum()
    report["nulls_final"]   = {col: int(n) for col, n in nulls.items() if n > 0}
    report["total_limpio"]  = len(df)
    report["retencion_pct"] = round(len(df) / total * 100, 1)
    report["excl_total"]    = total - len(df)

    if verbose:
        _print_report(report)

    return df, report


def _print_report(r: dict) -> None:
    sep = "=" * 62

    print(sep)
    print("REPORTE DE LIMPIEZA -- clean_dataset.py")
    print(sep)
    print(f"Total bruto                        : {r['total_bruto']:>7,}")
    print(f"  Duplicados de ID removidos       : {r['excl_duplicados']:>7,}")

    ej = ", ".join(x["name"] for x in r["ejemplos_year_nulo"][:3])
    print(f"  Year <= 0 / nulo                 : {r['excl_year_nulo_o_cero']:>7,}  (ej.: {ej or 'ninguno'})")

    ej = ", ".join(x["name"] for x in r["ejemplos_year_old"][:3])
    print(f"  1 <= Year < 1900                 : {r['excl_year_lt_1900']:>7,}  (ej.: {ej or 'ninguno'})")

    ej = ", ".join(x["name"] for x in r["ejemplos_year_fut"][:3])
    print(f"  Year > 2026                      : {r['excl_year_gt_2026']:>7,}  (ej.: {ej or 'ninguno'})")

    print(f"  Subtotal tras filtro de anio     : {r['subtotal_tras_anio']:>7,}")
    if r["excl_votes_lt_50"] is not None:
        print(f"  Users rated < 50                 : {r['excl_votes_lt_50']:>7,}")
    print(f"  Subtotal tras filtro de votos    : {r['subtotal_tras_votos']:>7,}")
    print(sep)
    print(f"Dataset limpio                     : {r['total_limpio']:>7,}  ({r['retencion_pct']} %)")
    print(f"Excluidos totales                  : {r['excl_total']:>7,}  ({100 - r['retencion_pct']:.1f} %)")

    print()
    print(sep)
    print("CENTINELAS BGG: ceros -> NaN (despues del filtro de 50 votos)")
    print(sep)
    for col, n in r["sentinel_zeros"].items():
        flag = " <- NO IMPUTA, queda NaN" if n else ""
        print(f"  {col:<22} : {n:>5,} ceros convertidos{flag}")

    print()
    print(sep)
    print("MAX_PLAYERS: unlimited_players flag + cap al p99")
    print(sep)
    if r["unlimited_players_count"] is not None:
        print(f"  Juegos con max_players == 999    : {r['unlimited_players_count']:>5,}  (-> unlimited_players = True)")
        print(f"  Cap al p99                       : {r['max_players_p99_cap']:>5.0f} jugadores")

    print()
    print(sep)
    print("PLAYTIME: distribucion de extremos (antes de cap) + cap al p99")
    print(sep)
    for col, s in r["playtime_stats"].items():
        print(f"  {col}:")
        print(f"    p50 = {s['p50']:>6.0f} min  |  p75 = {s['p75']:>6.0f} min  |  p90 = {s['p90']:>6.0f} min")
        print(f"    p95 = {s['p95']:>6.0f} min  |  p99 = {s['p99']:>6.0f} min  |  max = {s['max_raw']:>6.0f} min")
        print(f"    Registros con playtime > 24h (>1440 min): {s['n_over_1440']:,}")
        print(f"    Cap aplicado al p99: {s['p99']:.0f} min")

    print()
    print(sep)
    print("NULOS FINALES (post-limpieza completa)")
    print(sep)
    nf = r.get("nulls_final", {})
    if nf:
        for col, n in nf.items():
            pct = n / r["total_limpio"] * 100
            print(f"  {col:<22} : {n:>6,}  ({pct:.2f}%)  <- NO imputado")
    else:
        print("  Sin nulos en ninguna columna.")

    print()
    print(sep)
    print("Columnas prohibidas como features (leakage):")
    print("  bayes_average  -- funcion directa del target (average)")
    print("  rank           -- reordenacion determinista de bayes_average")
    print("  users_rated    -- no disponible en inferencia pre-lanzamiento")
    print()
    print("Target: average  (escala raw [1, 10], sin transformacion)")
    print(sep)


# ── Entrypoint ─────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Limpia bgg_games.csv segun EDA Parte 1")
    parser.add_argument("--input",       default=DEFAULT_IN,  help="CSV de entrada")
    parser.add_argument("--output",      default=DEFAULT_OUT, help="CSV de salida")
    parser.add_argument("--report-only", action="store_true", help="Solo reporte, no escribe")
    args = parser.parse_args()

    print(f"Leyendo: {args.input}")
    df_raw = pd.read_csv(args.input, low_memory=False)

    df_clean, _ = clean(df_raw, verbose=True)

    if not args.report_only:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        df_clean.to_csv(args.output, index=False)
        print(f"Guardado: {args.output}")


if __name__ == "__main__":
    main()
