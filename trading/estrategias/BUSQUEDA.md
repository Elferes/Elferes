# Búsqueda de estrategias — 2026-11-18

- Variantes probadas: **11664** (base × filtros × salida) en 24 series.
- Protocolo: se elige la mejor variante solo con el 70 % antiguo; se aprueba si en el 30 % reciente tiene ≥ 30 operaciones, esperanza ≥ +0.1 R, PF ≥ 1.2, entrenamiento ≥ +0.05 R, **significancia estadística t ≥ 2.0 en la prueba** (≈ menos de 5 % de probabilidad de ser suerte) y t ≥ 1.5 en entrenamiento, y **las dos mitades de la prueba en positivo**. Costes incluidos.
- **Aprobadas con datos reales: 0** · **Aprobadas con precios desordenados (suerte): 0** de 248 candidatas.

Tasa de aprobación real 0.0% frente a 0.0% por azar. **No hay más ganadoras que las esperables por suerte: tomar con mucha cautela.**

## Estrategias aprobadas (prueba ciega)

| Activo | TF | Variante | Entreno (ops, R, t) | Prueba ops | Acierto | Esperanza | t | PF | Máx DD | Mitades (R) |
|---|---|---|---|---|---|---|---|---|---|---|

## Mejores candidatas no aprobadas (las 15 con mejor prueba)

| Activo | TF | Variante | Prueba ops | Esperanza | t | PF | Motivo |
|---|---|---|---|---|---|---|---|
| US Tech 100 | 1h | `donchian|tendencia200,vol_baja|base` | 40 | 0.498 | 2.59 | 2.28 | una mitad o el entreno flojos |
| US 500 | 1h | `cruce_ema|sesion_lny|obj1r` | 35 | 0.478 | 3.33 | 3.0 | una mitad o el entreno flojos |
| XAU/USD | 1h | `ruptura_asiatica|vol_alta|obj2r` | 16 | 0.474 | 1.57 | 2.63 | pocas ops |
| US Tech 100 | 1h | `macd_giro|vol_baja|obj2r` | 18 | 0.404 | 1.14 | 1.78 | pocas ops |
| GBP/USD | 1h | `envolvente_nivel|tendencia200|obj2r` | 26 | 0.376 | 1.41 | 1.85 | pocas ops |
| US Tech 100 | 1h | `ruptura_rango|sesion_lny|obj1r` | 20 | 0.364 | 2.11 | 2.77 | pocas ops |
| US 500 | 1h | `macd_giro|tendencia200,sesion_lny|base` | 28 | 0.354 | 1.57 | 1.84 | pocas ops |
| XAU/USD | 4h | `donchian|tendencia200,sesion_lny|base` | 28 | 0.35 | 1.62 | 1.96 | pocas ops |
| XAU/USD | 15m | `cruce_ema|vol_alta|obj1r` | 12 | 0.345 | 1.34 | 2.27 | pocas ops |
| XAU/USD | 1h | `macd_giro|vol_alta|obj2r` | 63 | 0.322 | 1.8 | 1.63 | no significativa (t bajo) |
| USD/JPY | 4h | `inside_bar|sesion_lny|obj2r` | 21 | 0.301 | 1.11 | 1.77 | pocas ops |
| AUD/USD | 1h | `cruce_ema|tendencia200,vol_baja|obj2r` | 49 | 0.228 | 1.16 | 1.44 | no significativa (t bajo) |
| XAU/USD | 4h | `macd_giro|tendencia200|obj2r` | 33 | 0.227 | 0.99 | 1.46 | no significativa (t bajo) |
| USD/JPY | 1h | `envolvente_nivel|vol_alta|base` | 56 | 0.221 | 1.44 | 1.51 | no significativa (t bajo) |
| EUR/USD | 4h | `doble_techo_suelo|vol_baja|obj2r` | 38 | 0.201 | 1.03 | 1.47 | no significativa (t bajo) |
