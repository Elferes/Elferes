# Búsqueda de estrategias — 2026-11-18

- Variantes probadas: **504** (base × filtros × salida) en 8 series.
- Protocolo: se elige la mejor variante solo con el 70 % antiguo; se aprueba si en el 30 % reciente tiene ≥ 30 operaciones, esperanza ≥ +0.1 R, PF ≥ 1.2, entrenamiento ≥ +0.05 R, **significancia estadística t ≥ 2.0 en la prueba** (≈ menos de 5 % de probabilidad de ser suerte) y t ≥ 1.5 en entrenamiento, y **las dos mitades de la prueba en positivo**. Costes incluidos.
- **Aprobadas con datos reales: 2** · **Aprobadas con precios desordenados (suerte): 0** de 13 candidatas.

Tasa de aprobación real 16.7% frente a 0.0% por azar. **Hay más ganadoras que las esperables por suerte: señal de ventaja real.**

## Estrategias aprobadas (prueba ciega)

| Activo | TF | Variante | Entreno (ops, R, t) | Prueba ops | Acierto | Esperanza | t | PF | Máx DD | Mitades (R) |
|---|---|---|---|---|---|---|---|---|---|---|
| TODOS | 1d | `macd_giro|tendencia200,sesion_lny|obj2r` | 260, +0.137, 1.73 | 127 | 48.8 % | **+0.288** | 2.47 | 1.61 | 8.87 | 15.26, 21.26 |
| TODOS | 1d | `rsi2_reversion|tendencia200,sesion_lny|obj2r` | 364, +0.222, 2.96 | 163 | 43.6 % | **+0.247** | 2.18 | 1.44 | 9.21 | 9.22, 31.07 |

## Desglose por activo en la prueba (agrupado)

- `macd_giro|tendencia200,sesion_lny|obj2r` (1d, APROBADA): XAU/USD 2 ops +1.986R, US 500 67 ops +0.156R, US Tech 100 58 ops +0.381R
- `tendencia_retroceso|tendencia200,vol_baja|obj2r` (1d, no aprobada): EUR/USD 14 ops +0.147R, GBP/USD 34 ops +0.374R, USD/JPY 20 ops +0.259R, AUD/USD 16 ops +0.272R, XAU/USD 47 ops +0.19R, BTC/USD 31 ops +0.291R, US 500 46 ops +0.126R, US Tech 100 35 ops +0.436R
- `rsi2_reversion|tendencia200,sesion_lny|obj2r` (1d, APROBADA): US 500 82 ops +0.201R, US Tech 100 81 ops +0.294R
- `cruce_ema|tendencia200,vol_baja|obj2r` (1d, no aprobada): EUR/USD 14 ops +0.198R, GBP/USD 15 ops +0.281R, USD/JPY 15 ops +0.044R, AUD/USD 23 ops -0.031R, XAU/USD 20 ops +0.063R, BTC/USD 17 ops +0.37R, US 500 5 ops -0.145R, US Tech 100 9 ops +0.743R
- `donchian|tendencia200,vol_alta|obj2r` (1d, no aprobada): EUR/USD 33 ops +0.074R, GBP/USD 30 ops -0.04R, USD/JPY 28 ops +0.32R, AUD/USD 21 ops -0.273R, XAU/USD 45 ops +0.252R, BTC/USD 30 ops +0.007R, US 500 46 ops +0.014R, US Tech 100 48 ops +0.136R
- `inside_bar|tendencia200,vol_baja|obj2r` (1d, no aprobada): EUR/USD 6 ops -0.057R, GBP/USD 13 ops -0.21R, USD/JPY 9 ops +0.109R, AUD/USD 4 ops -0.705R, XAU/USD 15 ops +0.24R, BTC/USD 20 ops +0.048R, US 500 20 ops +0.33R, US Tech 100 27 ops +0.042R
- `pin_nivel|sesion_lny|obj2r` (1d, no aprobada): US 500 14 ops -0.119R, US Tech 100 13 ops +0.144R
- `ruptura_rango|tendencia200,vol_baja|obj2r` (1d, no aprobada): XAU/USD 19 ops -0.182R, BTC/USD 17 ops +0.11R, US 500 5 ops -0.201R, US Tech 100 8 ops +0.221R

## Mejores candidatas no aprobadas (las 15 con mejor prueba)

| Activo | TF | Variante | Prueba ops | Esperanza | t | PF | Motivo |
|---|---|---|---|---|---|---|---|
| TODOS | 1d | `tendencia_retroceso|tendencia200,vol_baja|obj2r` | 243 | 0.261 | 3.1 | 1.55 | una mitad o el entreno flojos |
| TODOS | 1d | `cruce_ema|tendencia200,vol_baja|obj2r` | 118 | 0.173 | 1.4 | 1.33 | no significativa (t bajo) |
| TODOS | 1d | `donchian|tendencia200,vol_alta|obj2r` | 281 | 0.083 | 1.09 | 1.15 | esperanza/PF bajos |
| TODOS | 1d | `inside_bar|tendencia200,vol_baja|obj2r` | 114 | 0.065 | 0.55 | 1.12 | esperanza/PF bajos |
| TODOS | 1d | `pin_nivel|sesion_lny|obj2r` | 27 | 0.008 | 0.03 | 1.01 | pocas ops |
| TODOS | 1d | `ruptura_rango|tendencia200,vol_baja|obj2r` | 49 | -0.017 | -0.1 | 0.97 | esperanza/PF bajos |
| TODOS | 1d | `squeeze|tendencia200|obj2r` | 113 | -0.073 | -0.64 | 0.88 | esperanza/PF bajos |
| TODOS | 1d | `divergencia_rsi|tendencia200|obj1r` | 72 | -0.09 | -0.95 | 0.77 | esperanza/PF bajos |
| TODOS | 1d | `doble_techo_suelo|tendencia200,sesion_lny|base` | 70 | -0.112 | -1.02 | 0.76 | esperanza/PF bajos |
| TODOS | 1d | `envolvente_nivel|vol_alta|obj2r` | 57 | -0.258 | -1.91 | 0.56 | esperanza/PF bajos |
