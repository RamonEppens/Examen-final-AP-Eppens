"""
Parsea los XML de BGG API descargados en data/raw/xml/ y construye
data/processed/bgg_games.csv con una fila por juego.

Columnas principales:
    game_id, name, year, min_players, max_players, min_playtime, max_playtime,
    min_age, weight, average, bayes_average, users_rated, rank,
    mechanics (pipe-separated), categories (pipe-separated), designers, publishers
"""

import os
import glob
import pandas as pd
from lxml import etree
from tqdm import tqdm

RAW_XML_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "xml")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "bgg_games.csv")


def _text(el, xpath: str, default=None):
    nodes = el.xpath(xpath)
    if not nodes:
        return default
    val = nodes[0].get("value") or nodes[0].text
    return val.strip() if val else default


def _float(el, xpath: str):
    val = _text(el, xpath)
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _int(el, xpath: str):
    val = _text(el, xpath)
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _links(el, link_type: str) -> str:
    vals = [n.get("value", "") for n in el.xpath(f"link[@type='{link_type}']")]
    return "|".join(vals)


def parse_item(item) -> dict:
    return {
        "game_id": int(item.get("id", 0)),
        "name": _text(item, "name[@type='primary']"),
        "year": _int(item, "yearpublished"),
        "min_players": _int(item, "minplayers"),
        "max_players": _int(item, "maxplayers"),
        "min_playtime": _int(item, "minplaytime"),
        "max_playtime": _int(item, "maxplaytime"),
        "min_age": _int(item, "minage"),
        "weight": _float(item, "statistics/ratings/averageweight"),
        "average": _float(item, "statistics/ratings/average"),
        "bayes_average": _float(item, "statistics/ratings/bayesaverage"),
        "users_rated": _int(item, "statistics/ratings/usersrated"),
        "rank": _int(item, "statistics/ratings/ranks/rank[@name='boardgame']"),
        "mechanics": _links(item, "boardgamemechanic"),
        "categories": _links(item, "boardgamecategory"),
        "designers": _links(item, "boardgamedesigner"),
        "publishers": _links(item, "boardgamepublisher"),
    }


def build_dataset(xml_dir: str = RAW_XML_DIR, out_path: str = OUT_PATH) -> pd.DataFrame:
    xml_files = sorted(glob.glob(os.path.join(xml_dir, "*.xml")))
    if not xml_files:
        raise FileNotFoundError(f"No se encontraron XML en {xml_dir}. Ejecuta download_details.py primero.")

    rows = []
    for path in tqdm(xml_files, desc="Parseando XML"):
        tree = etree.parse(path)
        for item in tree.xpath("//item[@type='boardgame']"):
            rows.append(parse_item(item))

    df = pd.DataFrame(rows).drop_duplicates("game_id")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Dataset guardado: {out_path}  ({len(df):,} juegos, {df.shape[1]} columnas)")
    return df


if __name__ == "__main__":
    build_dataset()
