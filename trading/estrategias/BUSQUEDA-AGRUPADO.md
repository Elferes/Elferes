# Búsqueda de estrategias — 2026-11-18

- Variantes probadas: **1512** (base × filtros × salida) en 24 series.
- Protocolo: se elige la mejor variante solo con el 70 % antiguo; se aprueba si en el 30 % reciente tiene ≥ 30 operaciones, esperanza ≥ +0.1 R, PF ≥ 1.2, entrenamiento ≥ +0.05 R, **significancia estadística t ≥ 2.0 en la prueba** (≈ menos de 5 % de probabilidad de ser suerte) y t ≥ 1.5 en entrenamiento, y **las dos mitades de la prueba en positivo**. Costes incluidos.
- **Aprobadas con datos reales: 0** · **Aprobadas con precios desordenados (suerte): 0** de 27 candidatas.

Tasa de aprobación real 0.0% frente a 0.0% por azar. **No hay más ganadoras que las esperables por suerte: tomar con mucha cautela.**

## Estrategias aprobadas (prueba ciega)

| Activo | TF | Variante | Entreno (ops, R, t) | Prueba ops | Acierto | Esperanza | t | PF | Máx DD | Mitades (R) |
|---|---|---|---|---|---|---|---|---|---|---|

## Desglose por activo en la prueba (agrupado)

- `reversion_bollinger|tendencia200|obj2r` (1h, no aprobada): EUR/USD 7 ops +0.423R, GBP/USD 11 ops +0.397R, USD/JPY 3 ops +0.132R, AUD/USD 7 ops -0.289R, XAU/USD 3 ops +0.951R, BTC/USD 7 ops +0.307R, US 500 1 ops -1.057R
- `reversion_bollinger||obj2r` (4h, no aprobada): EUR/USD 1 ops +0.109R, GBP/USD 7 ops +0.243R, USD/JPY 9 ops +0.162R, AUD/USD 5 ops +0.149R, XAU/USD 3 ops +0.975R, BTC/USD 8 ops +0.408R, US 500 3 ops +0.219R, US Tech 100 3 ops -0.794R
- `rsi2_reversion|sesion_ny|obj2r` (4h, no aprobada): EUR/USD 65 ops +0.249R, GBP/USD 66 ops +0.093R, USD/JPY 48 ops +0.197R, AUD/USD 69 ops +0.182R, XAU/USD 49 ops +0.084R, BTC/USD 47 ops -0.162R, US 500 52 ops +0.131R, US Tech 100 61 ops +0.211R
- `pin_nivel|vol_baja|obj1r` (4h, no aprobada): EUR/USD 2 ops +0.944R, GBP/USD 4 ops -0.81R, USD/JPY 5 ops +0.142R, AUD/USD 12 ops +0.105R, XAU/USD 5 ops +0.176R, BTC/USD 16 ops +0.068R, US 500 2 ops +0.954R, US Tech 100 2 ops -0.033R
- `macd_giro|tendencia200,sesion_lny|base` (4h, no aprobada): EUR/USD 19 ops -0.013R, GBP/USD 18 ops +0.12R, USD/JPY 17 ops +0.108R, AUD/USD 17 ops +0.19R, XAU/USD 18 ops +0.271R, BTC/USD 19 ops +0.018R, US 500 11 ops +0.097R, US Tech 100 10 ops -0.407R
- `ruptura_rango|tendencia200,sesion_lny|obj2r` (1h, no aprobada): EUR/USD 54 ops +0.188R, GBP/USD 57 ops +0.021R, USD/JPY 50 ops +0.045R, AUD/USD 33 ops +0.196R, XAU/USD 36 ops +0.132R, BTC/USD 48 ops -0.198R, US 500 10 ops +0.124R, US Tech 100 14 ops +0.334R
- `ruptura_asiatica|tendencia200,vol_baja|obj2r` (1h, no aprobada): EUR/USD 75 ops +0.059R, GBP/USD 84 ops +0.08R, USD/JPY 52 ops -0.129R, AUD/USD 46 ops +0.14R, XAU/USD 33 ops +0.296R, BTC/USD 39 ops +0.051R
- `macd_giro|vol_baja|obj2r` (1h, no aprobada): EUR/USD 103 ops +0.094R, GBP/USD 115 ops -0.055R, USD/JPY 109 ops -0.093R, AUD/USD 91 ops +0.153R, XAU/USD 80 ops -0.128R, BTC/USD 95 ops +0.126R, US 500 23 ops +0.3R, US Tech 100 18 ops +0.404R

## Mejores candidatas no aprobadas (las 15 con mejor prueba)

| Activo | TF | Variante | Prueba ops | Esperanza | t | PF | Motivo |
|---|---|---|---|---|---|---|---|
| TODOS | 1h | `reversion_bollinger|tendencia200|obj2r` | 39 | 0.247 | 1.23 | 1.56 | no significativa (t bajo) |
| TODOS | 4h | `reversion_bollinger||obj2r` | 39 | 0.217 | 1.06 | 1.46 | no significativa (t bajo) |
| TODOS | 4h | `rsi2_reversion|sesion_ny|obj2r` | 457 | 0.132 | 2.07 | 1.23 | una mitad o el entreno flojos |
| TODOS | 4h | `pin_nivel|vol_baja|obj1r` | 48 | 0.092 | 0.66 | 1.22 | esperanza/PF bajos |
| TODOS | 4h | `macd_giro|tendencia200,sesion_lny|base` | 129 | 0.071 | 0.69 | 1.14 | esperanza/PF bajos |
| TODOS | 1h | `ruptura_rango|tendencia200,sesion_lny|obj2r` | 302 | 0.07 | 1.07 | 1.15 | esperanza/PF bajos |
| TODOS | 1h | `ruptura_asiatica|tendencia200,vol_baja|obj2r` | 329 | 0.068 | 0.99 | 1.13 | esperanza/PF bajos |
| TODOS | 1h | `macd_giro|vol_baja|obj2r` | 634 | 0.036 | 0.67 | 1.06 | esperanza/PF bajos |
| TODOS | 1h | `divergencia_rsi|tendencia200|base` | 211 | 0.036 | 0.6 | 1.11 | esperanza/PF bajos |
| TODOS | 4h | `ruptura_rango|tendencia200,vol_baja|obj2r` | 62 | 0.02 | 0.14 | 1.04 | esperanza/PF bajos |
| TODOS | 4h | `inside_bar|tendencia200,sesion_lny|base` | 128 | 0.013 | 0.14 | 1.03 | esperanza/PF bajos |
| TODOS | 4h | `divergencia_rsi|tendencia200|obj2r` | 56 | 0.005 | 0.03 | 1.01 | esperanza/PF bajos |
| TODOS | 1h | `envolvente_nivel|tendencia200,vol_alta|obj1r` | 73 | -0.003 | -0.03 | 0.99 | esperanza/PF bajos |
| TODOS | 4h | `donchian|tendencia200,sesion_lny|obj2r` | 237 | -0.01 | -0.13 | 0.98 | esperanza/PF bajos |
| TODOS | 1h | `rsi2_reversion|sesion_ny|obj2r` | 1584 | -0.038 | -1.14 | 0.94 | esperanza/PF bajos |
