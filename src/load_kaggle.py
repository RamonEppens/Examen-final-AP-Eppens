"""
PLAN B — Carga del dataset de BGG desde Kaggle.

Alternativa a download_details.py + build_dataset.py cuando la BGG API
no está disponible.  El pipeline original (API) sigue siendo la vía
principal; este script es independiente y no lo reemplaza.

Dataset objetivo (default):
    threnjen/board-games-database-from-boardgamegeek
    Archivo: games.csv
    ~20 k juegos  |  última actualización: enero 2022

Alternativa más reciente:
    bwandowando/boardgamegeek-board-games-reviews-jan-2025
    ~162 k filas (incluye expansiones y accesorios)

Prerequisitos:
    pip install kaggle
    Poner ~/.kaggle/kaggle.json con las credenciales de la API de Kaggle
    (descargá el token desde kaggle.com → Settings → API → Create New Token)

Uso:
    # Dataset por default (threnjen):
    python src/load_kaggle.py

    # Dataset alternativo:
    python src/load_kaggle.py --dataset bwandowando/boardgamegeek-board-games-reviews-jan-2025

    # Si ya descargaste el CSV manualmente a data/raw/kaggle/:
    python src/load_kaggle.py --skip-download

    # Solo reporte de metadata + overlap (no genera bgg_games.csv):
    python src/load_kaggle.py --report-only
"""

import os
import argparse
import zipfile
import truststore
import requests
import pandas as pd

truststore.inject_into_ssl()

RAW_KAGGLE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "kaggle")
RANKINGS_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "bgg_rankings.csv")
OUT_PATH       = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "bgg_games.csv")

DEFAULT_DATASET = "threnjen/board-games-database-from-boardgamegeek"

# ── Schemas por dataset ────────────────────────────────────────────────────────
# Cada entry mapea los nombres originales de columna al schema canónico
# que produce build_dataset.py (pipeline principal con la API de BGG).
SCHEMAS = {
    "threnjen/board-games-database-from-boardgamegeek": {
        "file": "games.csv",
        "sep": ";",           # separador de mecánicas/dominios en ese CSV
        "col_map": {
            "BGG_Id":             "game_id",
            "Name":               "name",
            "Year Published":     "year",
            "Min Players":        "min_players",
            "Max Players":        "max_players",
            "Play Time":          "max_playtime",
            "Min Age":            "min_age",
            "Users Rated":        "users_rated",
            "Rating Average":     "average",
            "BGG Rank":           "rank",
            "Complexity Average": "weight",
            "Owned Users":        "owned_users",
            "Mechanics":          "mechanics",
            "Domains":            "categories",
        },
        # columnas que no existen en este dataset
        "missing": ["bayes_average", "min_playtime", "designers", "publishers"],
    },
    "bwandowando/boardgamegeek-board-games-reviews-jan-2025": {
        "file": "boardgames.csv",
        "sep": ",",
        "col_map": {
            "Game_Id":    "game_id",
            "Title":      "name",
            "Year":       "year",
            "AvgRating":  "average",
            "GeekRating": "bayes_average",
            "Voters":     "users_rated",
            "Rank":       "rank",
        },
        "missing": [
            "min_players", "max_players", "min_playtime", "max_playtime",
            "min_age", "weight", "mechanics", "categories",
            "designers", "publishers", "owned_users",
        ],
    },
}


# ── Descarga ───────────────────────────────────────────────────────────────────

def download_kaggle(dataset: str, out_dir: str) -> None:
    try:
        import kaggle  # noqa: F401 – valida que el paquete esté instalado
    except ImportError:
        raise SystemExit(
            "Paquete 'kaggle' no instalado. Corré: pip install kaggle"
        )

    if not os.path.exists(os.path.expanduser("~/.kaggle/kaggle.json")):
        raise SystemExit(
            "Credenciales de Kaggle no encontradas en ~/.kaggle/kaggle.json\n"
            "Descargalas desde kaggle.com → Settings → API → Create New Token"
        )

    os.makedirs(out_dir, exist_ok=True)
    print(f"Descargando {dataset} ...")
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(dataset, path=out_dir, unzip=True, quiet=False)
    print(f"Dataset descomprimido en {out_dir}")


# ── Carga y normalización ──────────────────────────────────────────────────────

def find_csv(directory: str, filename: str) -> str:
    path = os.path.join(directory, filename)
    if os.path.exists(path):
        return path
    # búsqueda recursiva si el nombre exacto no está en la raíz
    for root, _, files in os.walk(directory):
        for f in files:
            if f.lower() == filename.lower():
                return os.path.join(root, f)
    available = [f for f in os.listdir(directory) if f.endswith(".csv")]
    raise FileNotFoundError(
        f"No se encontró '{filename}' en {directory}.\n"
        f"CSVs disponibles: {available}\n"
        "Ajustá el campo 'file' en SCHEMAS para este dataset."
    )


def load_and_normalize(dataset: str, raw_dir: str) -> pd.DataFrame:
    schema = SCHEMAS.get(dataset)
    if schema is None:
        raise ValueError(
            f"Dataset '{dataset}' no tiene schema definido en SCHEMAS. "
            "Agregalo o usá --skip-download con el CSV ya renombrado."
        )

    csv_path = find_csv(raw_dir, schema["file"])
    print(f"Cargando {csv_path} ...")
    df_raw = pd.read_csv(csv_path, low_memory=False)
    print(f"  Filas crudas: {len(df_raw):,}  |  Columnas: {df_raw.shape[1]}")

    # renombrar solo las columnas que existen en el CSV
    col_map = {k: v for k, v in schema["col_map"].items() if k in df_raw.columns}
    missing_src = [k for k in schema["col_map"] if k not in df_raw.columns]
    if missing_src:
        print(f"  AVISO: columnas no encontradas en el CSV fuente: {missing_src}")

    df = df_raw.rename(columns=col_map)

    # normalizar separadores de mecánicas y categorías a pipe (igual que build_dataset.py)
    sep = schema.get("sep", ";")
    if sep != "|":
        for col in ("mechanics", "categories"):
            if col in df.columns:
                df[col] = df[col].str.replace(sep, "|", regex=False)

    # agregar columnas faltantes como NaN para mantener schema canónico
    canonical_cols = [
        "game_id", "name", "year", "min_players", "max_players",
        "min_playtime", "max_playtime", "min_age", "weight",
        "average", "bayes_average", "users_rated", "rank",
        "mechanics", "categories", "designers", "publishers", "owned_users",
    ]
    for col in canonical_cols:
        if col not in df.columns:
            df[col] = None

    df["game_id"] = pd.to_numeric(df["game_id"], errors="coerce").dropna().astype(int)
    df = df.drop_duplicates("game_id")

    return df[canonical_cols]


# ── Reporte ────────────────────────────────────────────────────────────────────

def print_report(df: pd.DataFrame, dataset: str) -> None:
    rankings_path = RANKINGS_PATH
    print("\n" + "=" * 60)
    print("REPORTE DE CALIDAD — DATASET KAGGLE")
    print("=" * 60)
    print(f"Dataset : {dataset}")
    print(f"Juegos  : {len(df):,}")

    if "year" in df.columns:
        valid_years = pd.to_numeric(df["year"], errors="coerce").dropna()
        print(f"Año máx : {int(valid_years.max())}  |  Año mín: {int(valid_years.min())}")

    print()
    print("Nulos por columna:")
    nulls = df.isnull().sum().sort_values(ascending=False)
    print(nulls[nulls > 0].to_string())

    # overlap con rankings
    if os.path.exists(rankings_path):
        ranks = pd.read_csv(rankings_path)
        id_col = next(c for c in ranks.columns if c.lower() == "id")
        ranking_ids = set(ranks[id_col].dropna().astype(int))
        kaggle_ids  = set(df["game_id"].dropna().astype(int))
        overlap     = ranking_ids & kaggle_ids
        missing     = ranking_ids - kaggle_ids
        pct         = len(overlap) / len(ranking_ids) * 100

        print(f"\nIDs en rankings (beefsack 2026-07-01): {len(ranking_ids):,}")
        print(f"IDs en Kaggle dataset               : {len(kaggle_ids):,}")
        print(f"Overlap                              : {len(overlap):,}  ({pct:.1f}%)")
        print(f"Rankings sin datos en Kaggle         : {len(missing):,}  ({100 - pct:.1f}%)")

        if missing:
            print(f"\nPrimeros 20 IDs sin match: {sorted(missing)[:20]}")
    else:
        print(f"\nAVISO: no se encontró {rankings_path} para calcular overlap.")

    print("=" * 60)


# ── Build final CSV ────────────────────────────────────────────────────────────

def build_output(df: pd.DataFrame, out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"\nDataset guardado: {out_path}  ({len(df):,} filas, {df.shape[1]} columnas)")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="PLAN B: carga BGG desde Kaggle")
    parser.add_argument("--dataset",       default=DEFAULT_DATASET,
                        help="slug de Kaggle (user/dataset-name)")
    parser.add_argument("--skip-download", action="store_true",
                        help="no descargar; usar lo que ya está en data/raw/kaggle/")
    parser.add_argument("--report-only",   action="store_true",
                        help="solo imprime el reporte, no escribe bgg_games.csv")
    args = parser.parse_args()

    raw_dir = RAW_KAGGLE_DIR

    if not args.skip_download:
        download_kaggle(args.dataset, raw_dir)

    df = load_and_normalize(args.dataset, raw_dir)
    print_report(df, args.dataset)

    if not args.report_only:
        build_output(df, OUT_PATH)


if __name__ == "__main__":
    main()
