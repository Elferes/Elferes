# Búsqueda de estrategias — 2026-11-18

- Variantes probadas: **11664** (base × filtros × salida) en 24 series.
- Protocolo: se elige la mejor variante solo con el 70 % antiguo; se aprueba si en el 30 % reciente tiene ≥ 30 operaciones, esperanza ≥ +0.1 R, PF ≥ 1.2, entrenamiento ≥ +0.05 R, **significancia estadística t ≥ 2.0 en la prueba** (≈ menos de 5 % de probabilidad de ser suerte) y t ≥ 1.5 en entrenamiento, y **las dos mitades de la prueba en positivo**. Costes incluidos.
- **Aprobadas con datos reales: 0** · **Aprobadas con precios desordenados (suerte): 0** de 242 candidatas.

Tasa de aprobación real 0.0% frente a 0.0% por azar. **No hay más ganadoras que las esperables por suerte: tomar con mucha cautela.**

## Estrategias aprobadas (prueba ciega)

| Activo | TF | Variante | Entreno (ops, R, t) | Prueba ops | Acierto | Esperanza | t | PF | Máx DD | Mitades (R) |
|---|---|---|---|---|---|---|---|---|---|---|

## Mejores candidatas no aprobadas (las 15 con mejor prueba)

| Activo | TF | Variante | Prueba ops | Esperanza | t | PF | Motivo |
|---|---|---|---|---|---|---|---|
| US Tech 100 | 1h | `macd_giro|vol_baja|obj2r` | 19 | 0.516 | 1.52 | 2.12 | pocas ops |
| XAU/USD | 1h | `ruptura_asiatica|vol_alta|obj2r` | 15 | 0.514 | 1.61 | 2.71 | pocas ops |
| US Tech 100 | 1h | `donchian|tendencia200,vol_baja|base` | 39 | 0.41 | 2.07 | 1.96 | una mitad o el entreno flojos |
| GBP/USD | 1h | `envolvente_nivel|tendencia200|obj2r` | 26 | 0.376 | 1.41 | 1.85 | pocas ops |
| US Tech 100 | 1h | `ruptura_rango|sesion_lny|obj1r` | 20 | 0.364 | 2.11 | 2.77 | pocas ops |
| USD/JPY | 4h | `inside_bar|sesion_lny|obj2r` | 21 | 0.355 | 1.26 | 1.9 | pocas ops |
| XAU/USD | 15m | `cruce_ema|vol_alta|obj1r` | 12 | 0.345 | 1.34 | 2.27 | pocas ops |
| XAU/USD | 1h | `macd_giro|vol_alta|obj2r` | 65 | 0.33 | 1.87 | 1.65 | no significativa (t bajo) |
| US 500 | 1h | `macd_giro|tendencia200,sesion_lny|base` | 28 | 0.323 | 1.4 | 1.72 | pocas ops |
| XAU/USD | 4h | `donchian|tendencia200,sesion_lny|base` | 29 | 0.283 | 1.3 | 1.69 | pocas ops |
| AUD/USD | 1h | `cruce_ema|tendencia200,vol_baja|obj2r` | 49 | 0.255 | 1.28 | 1.49 | no significativa (t bajo) |
| EUR/USD | 4h | `doble_techo_suelo|vol_baja|obj2r` | 38 | 0.25 | 1.24 | 1.59 | no significativa (t bajo) |
| XAU/USD | 4h | `cruce_ema||obj2r` | 29 | 0.238 | 1.0 | 1.57 | pocas ops |
| USD/JPY | 4h | `rsi2_reversion|sesion_ny|obj2r` | 49 | 0.232 | 1.19 | 1.45 | no significativa (t bajo) |
| USD/JPY | 1h | `envolvente_nivel|vol_alta|base` | 57 | 0.216 | 1.43 | 1.51 | no significativa (t bajo) |
