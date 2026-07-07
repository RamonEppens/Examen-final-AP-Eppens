"""
Tuning de hiperparametros con Optuna sobre el modelo final congelado
(LightGBM + 92 features: base 80 + playtime_ratio + players_range + 10 familias
de mecanicas). Exploratorio -- NO modifica notebooks/03 ni 04, NO toca el holdout.

Objetivo: minimizar RMSE en el mismo KFold(k=5, shuffle=True, seed=42) sobre
train (year <= 2023) usado en 02_experimentos.ipynb / 03_train_final.ipynb.

n_estimators se define con early stopping sobre un split interno (85/15) del
propio fold de entrenamiento -- nunca se usa el fold de validacion externo ni
el holdout para decidir cuantos arboles entrenar.

Uso:
    python tuning/optuna_search.py                # corre hasta 200 trials o 2h
    python tuning/optuna_search.py --trials 20     # override rapido para pruebas
    python tuning/optuna_search.py --timeout 120   # override rapido para pruebas
    python tuning/optuna_search.py --report-only   # solo regenera el reporte
                                                    # a partir del study.db existente
"""

from __future__ import annotations

import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner
import lightgbm as lgb
from sklearn.model_selection import KFold, train_test_split
from sklearn.metrics import mean_squared_error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.features import build_features, add_v2_features  # noqa: E402

SEED = 42
DATA_PATH = os.path.join(ROOT, "data", "processed", "bgg_games_clean.csv")
TUNING_DIR = os.path.dirname(os.path.abspath(__file__))
STUDY_DB = os.path.join(TUNING_DIR, "optuna_study.db")
STUDY_NAME = "lgbm_bgg_tuning"

CURRENT_RMSE = 0.5686
CURRENT_STD = 0.0055
DECISION_THRESHOLD = 0.563  # regla de decision fijada de antemano

DEFAULT_N_TRIALS = 200
DEFAULT_TIMEOUT_S = 2 * 3600  # 2 horas


def load_train_features() -> tuple[pd.DataFrame, pd.Series]:
    """Reproduce EXACTAMENTE la pipeline de features del modelo final (03_train_final.ipynb)."""
    df = pd.read_csv(DATA_PATH)
    df_train = df[df["year"] <= 2023].reset_index(drop=True)

    X, y, _, top_mechs, top_cats = build_features(df_train)
    X, medians = add_v2_features(X, df_train)
    X = X.drop(columns=["weight_missing"])  # excluida en el modelo final (ver notebook 02)

    print(f"X_train: {X.shape}  (esperado: (22010, 92))")
    assert X.shape[1] == 92, f"Se esperaban 92 features, hay {X.shape[1]}"
    return X, y


X_TRAIN, Y_TRAIN = load_train_features()
KF = KFold(n_splits=5, shuffle=True, random_state=SEED)
FOLDS = list(KF.split(X_TRAIN))


def objective(trial: optuna.Trial) -> float:
    params = {
        "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
        "num_leaves":        trial.suggest_int("num_leaves", 20, 200),
        "max_depth":         trial.suggest_int("max_depth", 3, 12),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
        "subsample":         trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree":  trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "reg_alpha":         trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda":        trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "subsample_freq":    1,   # necesario para que 'subsample' tenga efecto en LightGBM
        "n_estimators":      3000,  # tope superior; early stopping decide el real
        "random_state":      SEED,
        "n_jobs":            -1,
        "verbose":           -1,
    }

    fold_rmses = []
    for fold_idx, (tr_idx, val_idx) in enumerate(FOLDS):
        X_tr_full, y_tr_full = X_TRAIN.iloc[tr_idx], Y_TRAIN.iloc[tr_idx]
        X_val, y_val = X_TRAIN.iloc[val_idx], Y_TRAIN.iloc[val_idx]

        # Split interno SOLO del fold de train, para decidir n_estimators via
        # early stopping. El fold de validacion externo (X_val/y_val) nunca
        # participa de esta decision -- se usa solo para medir RMSE final.
        X_fit, X_es, y_fit, y_es = train_test_split(
            X_tr_full, y_tr_full, test_size=0.15, random_state=SEED
        )

        model = lgb.LGBMRegressor(**params)
        model.fit(
            X_fit, y_fit,
            eval_set=[(X_es, y_es)],
            eval_metric="rmse",
            callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)],
        )

        pred = model.predict(X_val)
        rmse = float(np.sqrt(mean_squared_error(y_val, pred)))
        fold_rmses.append(rmse)

        trial.report(float(np.mean(fold_rmses)), step=fold_idx)
        if trial.should_prune():
            trial.set_user_attr("fold_rmses_partial", fold_rmses)
            raise optuna.TrialPruned()

    trial.set_user_attr("fold_rmses", fold_rmses)
    trial.set_user_attr("std_rmse", float(np.std(fold_rmses)))
    return float(np.mean(fold_rmses))


def build_study() -> optuna.Study:
    sampler = TPESampler(seed=SEED)
    pruner = MedianPruner(n_startup_trials=10, n_warmup_steps=2)
    storage = f"sqlite:///{STUDY_DB}"
    study = optuna.create_study(
        study_name=STUDY_NAME,
        storage=storage,
        direction="minimize",
        sampler=sampler,
        pruner=pruner,
        load_if_exists=True,
    )
    return study


def run(n_trials: int, timeout: int) -> optuna.Study:
    study = build_study()
    n_existing = len(study.trials)
    n_remaining = max(0, n_trials - n_existing)
    print(f"Trials existentes en el study: {n_existing}  |  a correr ahora: {n_remaining}")

    if n_remaining > 0:
        start = time.time()
        study.optimize(objective, n_trials=n_remaining, timeout=timeout, show_progress_bar=False)
        elapsed = time.time() - start
        print(f"\nOptimizacion terminada en {elapsed/60:.1f} min "
              f"({len(study.trials)} trials totales en el study)")
    else:
        print("Ya hay >= n_trials en el study, no se corren trials nuevos.")

    return study


def write_report(study: optuna.Study) -> None:
    completed = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    pruned = [t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED]
    failed = [t for t in study.trials if t.state == optuna.trial.TrialState.FAIL]

    best = study.best_trial
    fold_rmses = best.user_attrs.get("fold_rmses", [])
    std_rmse = best.user_attrs.get("std_rmse")
    if std_rmse is None and fold_rmses:
        std_rmse = float(np.std(fold_rmses))

    delta = best.value - CURRENT_RMSE
    beats_threshold = best.value < DECISION_THRESHOLD

    lines = []
    lines.append("# Reporte de tuning -- Optuna sobre LightGBM (modelo final, 92 features)\n")
    lines.append(f"- Trials totales: {len(study.trials)}  "
                 f"(completos: {len(completed)}, podados: {len(pruned)}, fallidos: {len(failed)})")
    lines.append(f"- Sampler: TPESampler(seed={SEED})  |  Pruner: MedianPruner(n_startup_trials=10, n_warmup_steps=2)")
    lines.append(f"- CV: KFold(k=5, shuffle=True, seed={SEED}) sobre train (year <= 2023, n={len(X_TRAIN)})")
    lines.append(f"- Holdout 2024-2026: NO TOCADO\n")

    lines.append("## Resultado del mejor trial\n")
    lines.append(f"- **RMSE CV: {best.value:.4f} ± {std_rmse:.4f}**")
    lines.append(f"- Folds individuales: {', '.join(f'{r:.4f}' for r in fold_rmses)}")
    lines.append(f"- Trial number: {best.number}\n")

    lines.append("## Hiperparametros ganadores\n")
    lines.append("```")
    for k, v in best.params.items():
        lines.append(f"{k:<18} = {v}")
    lines.append("```\n")

    lines.append("## Comparacion contra el modelo actual\n")
    lines.append(f"| | RMSE CV | Std |")
    lines.append(f"|---|---|---|")
    lines.append(f"| Actual (LightGBM, params manuales) | {CURRENT_RMSE:.4f} | {CURRENT_STD:.4f} |")
    lines.append(f"| Optuna (mejor trial) | {best.value:.4f} | {std_rmse:.4f} |")
    lines.append(f"| Delta | {delta:+.4f} | -- |\n")

    lines.append("## Regla de decision (fijada de antemano)\n")
    lines.append(f"Umbral: RMSE CV < {DECISION_THRESHOLD}\n")
    if beats_threshold:
        lines.append(f"**Resultado: {best.value:.4f} < {DECISION_THRESHOLD} -> el tuning SI supera el umbral.** "
                     f"Pendiente de decision del usuario sobre si adoptar estos hiperparametros.")
    else:
        lines.append(f"**Resultado: {best.value:.4f} >= {DECISION_THRESHOLD} -> el tuning NO supera el umbral.** "
                     f"Segun la regla ya acordada, el modelo actual (params manuales, RMSE {CURRENT_RMSE:.4f}) "
                     f"queda como final. Este tuning se documenta como mejora explorada sin ganancia significativa.")

    report_path = os.path.join(TUNING_DIR, "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nReporte guardado en: {report_path}")

    best_params_path = os.path.join(TUNING_DIR, "best_params.json")
    with open(best_params_path, "w", encoding="utf-8") as f:
        json.dump({
            "rmse_cv": best.value,
            "std_rmse": std_rmse,
            "fold_rmses": fold_rmses,
            "params": best.params,
            "trial_number": best.number,
            "n_trials_total": len(study.trials),
            "beats_threshold": beats_threshold,
            "threshold": DECISION_THRESHOLD,
            "current_rmse": CURRENT_RMSE,
            "current_std": CURRENT_STD,
        }, f, ensure_ascii=False, indent=2)
    print(f"Mejores params guardados en: {best_params_path}")

    print("\n" + "\n".join(lines))


def save_plots(study: optuna.Study) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from optuna.visualization.matplotlib import plot_optimization_history, plot_param_importances

    ax = plot_optimization_history(study)
    fig = ax.get_figure()
    fig.tight_layout()
    hist_path = os.path.join(TUNING_DIR, "optimization_history.png")
    fig.savefig(hist_path, dpi=140)
    plt.close(fig)
    print(f"Grafico de historia guardado en: {hist_path}")

    completed = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    if len(completed) >= 2:
        try:
            ax2 = plot_param_importances(study)
            fig2 = ax2.get_figure()
            fig2.tight_layout()
            imp_path = os.path.join(TUNING_DIR, "param_importances.png")
            fig2.savefig(imp_path, dpi=140)
            plt.close(fig2)
            print(f"Grafico de importancia de hiperparametros guardado en: {imp_path}")
        except Exception as e:
            print(f"No se pudo generar plot_param_importances: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=DEFAULT_N_TRIALS)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()

    if args.report_only:
        study = build_study()
    else:
        study = run(args.trials, args.timeout)

    save_plots(study)
    write_report(study)


if __name__ == "__main__":
    main()
