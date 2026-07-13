"""
Descarga detalles de juegos desde BGG API v2 en lotes, con reintentos.
Guarda las respuestas XML en data/raw/xml/.

Uso:
    python src/download_details.py [--ids-file data/raw/bgg_rankings.csv] [--batch-size 20]
"""

import os
import time
import argparse
import truststore
import requests
import pandas as pd
from tqdm import tqdm

truststore.inject_into_ssl()

BGG_API = "https://boardgamegeek.com/xmlapi2/thing"
RAW_XML_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "xml")
DEFAULT_RANKINGS = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "bgg_rankings.csv")

BATCH_SIZE = 20
SLEEP_BETWEEN_BATCHES = 5.0
MAX_RETRIES = 5
RETRY_BACKOFF = 10.0


def load_ids(ids_file: str) -> list[int]:
    df = pd.read_csv(ids_file)
    id_col = next(c for c in df.columns if "id" in c.lower())
    return df[id_col].dropna().astype(int).tolist()


def already_downloaded(batch_ids: list[int], out_dir: str) -> bool:
    path = os.path.join(out_dir, f"batch_{batch_ids[0]}_{batch_ids[-1]}.xml")
    return os.path.exists(path)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}


def _build_headers() -> dict:
    """Add Authorization header if BGG_TOKEN env var is set (BGG OAuth2 Bearer token)."""
    h = dict(HEADERS)
    token = os.environ.get("BGG_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def fetch_batch(ids: list[int], retries: int = MAX_RETRIES) -> bytes:
    params = {"id": ",".join(map(str, ids)), "stats": 1}
    headers = _build_headers()
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(BGG_API, params=params, headers=headers, timeout=60)
            if resp.status_code in (202, 429, 500, 503):
                # 429 = rate-limited; 202 = BGG queued the request, retry
                wait = RETRY_BACKOFF * attempt
                print(f"  HTTP {resp.status_code}, esperando {wait:.0f}s ...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as e:
            if attempt == retries:
                raise
            wait = RETRY_BACKOFF * attempt
            print(f"  Error en intento {attempt}: {e}. Reintentando en {wait:.0f}s ...")
            time.sleep(wait)
    raise RuntimeError("Se agotaron los reintentos")


def download_details(ids_file: str = DEFAULT_RANKINGS, batch_size: int = BATCH_SIZE) -> None:
    os.makedirs(RAW_XML_DIR, exist_ok=True)
    ids = load_ids(ids_file)

    if not os.environ.get("BGG_TOKEN"):
        print(
            "AVISO: BGG_TOKEN no configurado. "
            "Registrá una app en boardgamegeek.com/xmlapi/credentials y "
            "seteá: $env:BGG_TOKEN = '<tu_token>'"
        )

    print(f"{len(ids)} juegos encontrados. Descargando en lotes de {batch_size} ...")

    batches = [ids[i : i + batch_size] for i in range(0, len(ids), batch_size)]
    for batch in tqdm(batches, desc="Lotes"):
        if already_downloaded(batch, RAW_XML_DIR):
            continue
        xml_bytes = fetch_batch(batch)
        out_path = os.path.join(RAW_XML_DIR, f"batch_{batch[0]}_{batch[-1]}.xml")
        with open(out_path, "wb") as f:
            f.write(xml_bytes)
        time.sleep(SLEEP_BETWEEN_BATCHES)

    print("Descarga completa.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids-file", default=DEFAULT_RANKINGS)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()
    download_details(args.ids_file, args.batch_size)
