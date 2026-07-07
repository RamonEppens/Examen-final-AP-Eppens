# Reporte de tuning -- Optuna sobre LightGBM (modelo final, 92 features)

- Trials totales: 200  (completos: 185, podados: 14, fallidos: 0)
- Sampler: TPESampler(seed=42)  |  Pruner: MedianPruner(n_startup_trials=10, n_warmup_steps=2)
- CV: KFold(k=5, shuffle=True, seed=42) sobre train (year <= 2023, n=22010)
- Holdout 2024-2026: NO TOCADO

## Resultado del mejor trial

- **RMSE CV: 0.5675 ± 0.0054**
- Folds individuales: 0.5651, 0.5662, 0.5616, 0.5777, 0.5669
- Trial number: 173

## Hiperparametros ganadores

```
learning_rate      = 0.012292573749453549
num_leaves         = 183
max_depth          = 12
min_child_samples  = 5
subsample          = 0.7448928146288163
colsample_bytree   = 0.6516687915463434
reg_alpha          = 4.360788189009667e-05
reg_lambda         = 7.899774207738307e-07
```

## Comparacion contra el modelo actual

| | RMSE CV | Std |
|---|---|---|
| Actual (LightGBM, params manuales) | 0.5686 | 0.0055 |
| Optuna (mejor trial) | 0.5675 | 0.0054 |
| Delta | -0.0011 | -- |

## Regla de decision (fijada de antemano)

Umbral: RMSE CV < 0.563

**Resultado: 0.5675 >= 0.563 -> el tuning NO supera el umbral.** Segun la regla ya acordada, el modelo actual (params manuales, RMSE 0.5686) queda como final. Este tuning se documenta como mejora explorada sin ganancia significativa.