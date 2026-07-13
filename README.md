# Examen Final — Análisis Predictivo

**Autor:** Ramon Eppens  
**Curso:** Análisis Predictivo — ITBA, 2026

## Objetivo

Predecir el rating promedio (`average`) de juegos de mesa de BoardGameGeek (BGG) a partir de sus características (mecánicas, categorías, duración, jugadores, año, etc.).

## Estructura

```
├── data/
│   ├── raw/            # XMLs de BGG API + parquet crudo (gitignoreado)
│   └── processed/      # bgg_games.csv final (~5-10 MB, commiteado)
├── notebooks/
│   ├── 01_eda.ipynb            # Análisis exploratorio
│   ├── 02_experimentos.ipynb   # Pruebas de modelos (no entregable)
│   ├── 03_train_final.ipynb    # ENTREGABLE: entrenamiento final
│   └── 04_predict_test.ipynb   # ENTREGABLE: predicción sobre test
├── src/
│   ├── download_rankings.py    # Descarga ranking CSV de beefsack
│   ├── download_details.py     # BGG API v2 en lotes con reintentos
│   └── build_dataset.py        # XML → tabla final
└── models/                     # Modelos entrenados (.joblib)
```

## Reproducibilidad

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

Métricas verificadas reproducibles con las versiones de `requirements-lock.txt` (Python 3.12).

### 2. Descargar datos

```bash
python src/download_rankings.py
python src/download_details.py
python src/build_dataset.py
```

### 3. Ejecutar notebooks

Ejecutar en orden: `01 → 03 → 04`.  
El notebook `02` es experimental y no es entregable.

## Entregables

| Archivo | Descripción |
|---|---|
| `data/processed/bgg_games.csv` | Dataset final limpio |
| `notebooks/03_train_final.ipynb` | Entrenamiento y serialización del modelo |
| `notebooks/04_predict_test.ipynb` | Predicciones sobre el conjunto de test |
| `models/` | Modelo serializado con joblib |
