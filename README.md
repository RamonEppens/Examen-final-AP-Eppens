# Examen Final — Análisis Predictivo

**Autor:** Ramon Eppens  
**Curso:** Análisis Predictivo — ITBA, 2026

## Objetivo

Predecir el rating promedio (`average`) de juegos de mesa de BoardGameGeek (BGG) a partir de sus características (mecánicas, categorías, duración, jugadores, año, etc.).

## Estructura

```
├── data/
│   ├── raw/                        # XMLs de BGG API (gitignoreado, no se sube)
│   └── processed/
│       ├── bgg_games.csv           # Dataset consolidado (ranking + ficha por ID)
│       └── bgg_games_clean.csv     # Dataset final limpio (el que usan los notebooks)
├── notebooks/
│   ├── 01_eda.ipynb                # Análisis exploratorio
│   ├── 02_experimentos.ipynb       # Pruebas de modelos (no entregable)
│   ├── 03_train_final.ipynb        # ENTREGABLE: entrenamiento final
│   └── 04_predict_test.ipynb       # ENTREGABLE: predicción sobre test
├── src/
│   ├── build_dataset.py            # XML → tabla final
│   ├── clean_dataset.py            # Limpieza y normalización
│   ├── download_details.py         # BGG API v2 en lotes con reintentos
│   ├── download_rankings.py        # Descarga ranking CSV de beefsack
│   ├── features.py                 # Feature engineering (usado por 02, 03 y 04)
│   └── load_kaggle.py              # Plan B: carga del dataset desde Kaggle
├── models/
│   └── lgbm_final.joblib           # Modelo entrenado (regenerado por 03_train_final)
├── presentacion/                   # Presentación interactiva — ver sección Presentación
│   ├── index.html, styles.css, script.js, charts.js
│   ├── data/                       # Un JSON + un JS por sección de la presentación
│   └── presentacion_final.pdf      # Export a PDF, un slide por paso
├── tuning/                         # Búsqueda de hiperparámetros con Optuna (200 trials)
├── requirements.txt
├── requirements-lock.txt           # Versiones exactas verificadas (Python 3.12)
└── README.md
```

## Reproducibilidad

Los notebooks corren directo con los datos ya incluidos en el repo (`data/processed/`) — **no hace falta descargar ni regenerar nada** para reproducir los resultados.

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

Métricas verificadas reproducibles con las versiones de `requirements-lock.txt` (Python 3.12).

### 2. Ejecutar notebooks

Ejecutar en orden: `01 → 03 → 04`.  
El notebook `02` es experimental y no es entregable.

### 3. Regenerar los datos desde cero (opcional)

```bash
python src/download_rankings.py
python src/download_details.py
python src/build_dataset.py
```

> Requiere un token de la API de BGG (app registrada) en la variable de entorno `BGG_TOKEN`; la descarga toma ~3 horas por rate limit.

## Presentación

- **En vivo:** https://ramoneppens.github.io/Examen-final-AP-Eppens/presentacion/
- **PDF:** [`presentacion/presentacion_final.pdf`](presentacion/presentacion_final.pdf)

## Entregables

| Archivo | Descripción |
|---|---|
| `data/processed/bgg_games.csv` | Dataset final limpio |
| `notebooks/03_train_final.ipynb` | Entrenamiento y serialización del modelo |
| `notebooks/04_predict_test.ipynb` | Predicciones sobre el conjunto de test |
| `models/` | Modelo serializado con joblib |
| `presentacion/presentacion_final.pdf` | Presentación exportada a PDF |
