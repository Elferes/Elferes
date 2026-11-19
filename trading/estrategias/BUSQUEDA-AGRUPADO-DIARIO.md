# Búsqueda de estrategias — 2026-11-18

- Variantes probadas: **1120** (base × filtros × salida) en 16 series.
- Protocolo: se elige la mejor variante solo con el 70 % antiguo; se aprueba si en el 30 % reciente tiene ≥ 30 operaciones, esperanza ≥ +0.1 R, PF ≥ 1.2, entrenamiento ≥ +0.05 R, **significancia estadística t ≥ 2.0 en la prueba** (≈ menos de 5 % de probabilidad de ser suerte) y t ≥ 1.5 en entrenamiento, y **las dos mitades de la prueba en positivo**. Costes incluidos.
- **Aprobadas con datos reales: 0** · **Aprobadas con precios desordenados (suerte): 1** de 25 candidatas.

Tasa de aprobación real 0.0% frente a 4.0% por azar. **No hay más ganadoras que las esperables por suerte: tomar con mucha cautela.**

## Estrategias aprobadas (prueba ciega)

| Activo | TF | Variante | Entreno (ops, R, t) | Prueba ops | Acierto | Esperanza | t | PF | Máx DD | Mitades (R) |
|---|---|---|---|---|---|---|---|---|---|---|

## Desglose por activo en la prueba (agrupado)

- `divergencia_rsi|d_tend,d_impulso|obj2r` (1h, no aprobada): EUR/USD 14 ops +0.269R, GBP/USD 13 ops -0.118R, USD/JPY 15 ops +0.303R, AUD/USD 16 ops -0.117R, XAU/USD 14 ops +0.36R, BTC/USD 13 ops +0.436R, US 500 5 ops +0.17R, US Tech 100 4 ops +0.005R
- `pin_nivel|d_retroceso|obj2r` (1h, no aprobada): EUR/USD 11 ops +0.404R, GBP/USD 9 ops -0.88R, USD/JPY 8 ops +0.453R, AUD/USD 10 ops -0.067R, XAU/USD 12 ops -0.042R, BTC/USD 21 ops +0.34R, US 500 4 ops -0.287R, US Tech 100 5 ops +1.363R
- `ruptura_asiatica|d_tend,d_impulso|obj2r` (1h, no aprobada): EUR/USD 30 ops +0.145R, GBP/USD 39 ops -0.004R, USD/JPY 32 ops -0.268R, AUD/USD 22 ops +0.254R, XAU/USD 16 ops +0.463R, BTC/USD 25 ops -0.017R
- `rsi2_reversion|d_retroceso|obj2r` (1h, no aprobada): EUR/USD 91 ops +0.025R, GBP/USD 87 ops +0.114R, USD/JPY 61 ops +0.19R, AUD/USD 94 ops -0.143R, XAU/USD 89 ops -0.134R, BTC/USD 110 ops -0.023R, US 500 37 ops +0.514R, US Tech 100 36 ops +0.33R
- `macd_giro|d_tend,vol_baja|obj2r` (1h, no aprobada): EUR/USD 46 ops +0.096R, GBP/USD 53 ops +0.002R, USD/JPY 71 ops -0.086R, AUD/USD 45 ops +0.291R, XAU/USD 44 ops -0.349R, BTC/USD 51 ops +0.216R, US 500 16 ops +0.139R, US Tech 100 11 ops +0.499R
- `cruce_ema|d_tend,sesion_lny|obj1r` (15m, no aprobada): EUR/USD 16 ops -0.016R, GBP/USD 16 ops -0.142R, USD/JPY 13 ops +0.07R, AUD/USD 13 ops -0.011R, XAU/USD 4 ops -0.37R, BTC/USD 11 ops +0.172R, US 500 4 ops +0.926R, US Tech 100 2 ops -0.058R
- `ruptura_rango|d_tend,sesion_lny|obj2r` (1h, no aprobada): EUR/USD 37 ops +0.122R, GBP/USD 34 ops -0.152R, USD/JPY 33 ops +0.062R, AUD/USD 23 ops -0.012R, XAU/USD 25 ops +0.171R, BTC/USD 37 ops -0.293R, US 500 6 ops +0.391R, US Tech 100 8 ops +0.614R
- `inside_bar|d_tend,sesion_ny|obj2r` (15m, no aprobada): EUR/USD 3 ops -0.167R, GBP/USD 10 ops -0.341R, USD/JPY 7 ops -0.288R, AUD/USD 7 ops +0.426R, XAU/USD 16 ops +0.396R, BTC/USD 9 ops -0.0R, US 500 7 ops +0.131R, US Tech 100 9 ops -0.608R

## Mejores candidatas no aprobadas (las 15 con mejor prueba)

| Activo | TF | Variante | Prueba ops | Esperanza | t | PF | Motivo |
|---|---|---|---|---|---|---|---|
| TODOS | 1h | `divergencia_rsi|d_tend,d_impulso|obj2r` | 94 | 0.175 | 1.74 | 1.57 | no significativa (t bajo) |
| TODOS | 1h | `pin_nivel|d_retroceso|obj2r` | 80 | 0.147 | 0.97 | 1.26 | no significativa (t bajo) |
| TODOS | 1h | `ruptura_asiatica|d_tend,d_impulso|obj2r` | 164 | 0.05 | 0.5 | 1.09 | esperanza/PF bajos |
| TODOS | 1h | `rsi2_reversion|d_retroceso|obj2r` | 605 | 0.044 | 0.78 | 1.07 | esperanza/PF bajos |
| TODOS | 1h | `macd_giro|d_tend,vol_baja|obj2r` | 337 | 0.044 | 0.6 | 1.07 | esperanza/PF bajos |
| TODOS | 15m | `cruce_ema|d_tend,sesion_lny|obj1r` | 79 | 0.028 | 0.27 | 1.07 | esperanza/PF bajos |
| TODOS | 1h | `ruptura_rango|d_tend,sesion_lny|obj2r` | 203 | 0.009 | 0.11 | 1.02 | esperanza/PF bajos |
| TODOS | 15m | `inside_bar|d_tend,sesion_ny|obj2r` | 68 | -0.017 | -0.13 | 0.96 | esperanza/PF bajos |
| TODOS | 1h | `envolvente_nivel|d_tend,vol_alta|obj1r` | 147 | -0.017 | -0.23 | 0.96 | esperanza/PF bajos |
| TODOS | 15m | `donchian|d_tend,sesion_lny|base` | 183 | -0.036 | -0.41 | 0.94 | esperanza/PF bajos |
| TODOS | 1h | `squeeze|d_impulso|obj1r` | 175 | -0.076 | -1.03 | 0.85 | esperanza/PF bajos |
| TODOS | 15m | `rsi2_reversion|d_tend,sesion_ny|obj2r` | 254 | -0.098 | -1.26 | 0.84 | esperanza/PF bajos |
| TODOS | 1h | `inside_bar|d_tend,sesion_ny|obj2r` | 239 | -0.099 | -1.4 | 0.81 | esperanza/PF bajos |
| TODOS | 15m | `squeeze|d_impulso|obj2r` | 41 | -0.132 | -0.67 | 0.79 | esperanza/PF bajos |
| TODOS | 1h | `doble_techo_suelo|d_retroceso,sesion_ny|obj2r` | 114 | -0.138 | -1.55 | 0.71 | esperanza/PF bajos |
