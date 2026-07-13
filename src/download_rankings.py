"""
Descarga el CSV de rankings de BGG desde el mirror de beefsack y lo guarda en data/raw/.
URL: https://raw.githubusercontent.com/beefsack/bgg-ranking-historicals/master/...
"""

import os
import truststore
import requests

truststore.inject_into_ssl()

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
RANKINGS_URL = (
    "https://raw.githubusercontent.com/beefsack/bgg-ranking-historicals"
    "/master/2026-07-01.csv"
)
OUT_PATH = os.path.join(RAW_DIR, "bgg_rankings.csv")


def download_rankings(url: str = RANKINGS_URL, out_path: str = OUT_PATH) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    print(f"Descargando rankings desde {url} ...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)
    print(f"Guardado en {out_path}  ({len(resp.content) / 1024:.1f} KB)")


if __name__ == "__main__":
    download_rankings()
