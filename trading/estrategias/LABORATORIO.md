# Laboratorio de estrategias

Lo mantiene `investigador-estrategias`. Cada entrada: hipótesis, cambio, resultado (entrenamiento y prueba),
conclusión y por qué funcionó o falló. Ranking actual: [RANKING.md](RANKING.md).

## Estrategias en la biblioteca (`trading/ejecutor/estrategias.py`)
| Estrategia | Idea | Mercado donde debería funcionar | Estado |
|---|---|---|---|
| tendencia_retroceso | Tendencia EMA 9/21/50 + retroceso a la EMA21 + vela de reanudación | Tendencia limpia | Desactivada: negativa en todos los activos y temporalidades |
| ruptura_rango | Compresión de 12 velas (< 2.5 ATR) y ruptura con cuerpo fuerte | Tras rangos estrechos, apertura de sesiones | **Activa** en XAU/USD 15m |
| reversion_bollinger | Fuera de Bollinger con RSI extremo y vuelta dentro, objetivo la media | Lateral (EMA50 plana) | **Activa** en GBP/USD 1h y EUR/USD 1h |
| cruce_ema | EMA9 cruza EMA21 a favor de la EMA50, con RSI | Inicio de tendencias | **Activa** en US 500 1h |
| envolvente_nivel | Envolvente en el máximo o mínimo de 30 velas | Giros en soportes y resistencias | **Activa** en US 500 1h |

## Diario del laboratorio
### 2026-11-18 — Creación
- Hipótesis: ninguna estrategia funciona en todos los mercados, así que el scalper debe usar solo las que demuestren
  ventaja fuera de muestra en cada activo.
- Primer backtest lanzado con 6 activos (EUR/USD, GBP/USD, USD/JPY, oro, BTC, US 500) en 5m, 15m y 1h.

### 2026-11-18 — Primer backtest (6 activos × 3 temporalidades × 5 estrategias)
- **Resultado:** 5 combinaciones APTA (prueba fuera de muestra, con costes):
  - GBP/USD 1h reversión Bollinger: +0.45 R, 70 % de acierto;
  - US 500 1h cruce EMA: +0.25 R;
  - XAU/USD 15m ruptura de rango: +0.20 R;
  - EUR/USD 1h reversión Bollinger: +0.18 R;
  - US 500 1h envolvente en nivel: +0.18 R.
- **Todas las de 5m pierden.** El coste por operación en 5m es una fracción grande del stop (ATR pequeño).
- **Conclusión:** el scalper pasa a operar solo esas 5 combinaciones (parámetros v2). Muestras pequeñas (23–54
  operaciones en prueba): hay que confirmarlo en vivo antes de subir el riesgo.
- **Idea para la próxima semana:** filtro por sesión (Londres/NY) para la ruptura de rango, y probar la reversión en
  Bollinger en AUD/USD y USD/JPY 1h.

### 2026-11-18 — Búsqueda sistemática (14 estrategias × filtros × salidas, prueba ciega + t ≥ 2 + azar)
- **Por activo (15m, 1h, 4h, 1d):** 0 aprobadas de 11664 variantes. 0 falsos positivos con precios desordenados.
  Con 1–2 años de intradía no hay operaciones suficientes para separar ventaja de suerte.
- **Agrupado en 8 activos, 1h y 4h:** 0 aprobadas. La mejor (`rsi2_reversion|sesion_ny|obj2r` en 4h, +0.13 R en 457
  operaciones) gana casi todo en los últimos meses y apenas en el entrenamiento: racha, no ventaja.
- **Agrupado en diario (~20 años, 6000 velas por activo): 2 APROBADAS, 0 por azar.**
  - `macd_giro|tendencia200,sesion_lny|obj2r`: entreno +0.14 R (260 ops), prueba **+0.29 R** (127 ops, t 2.47, PF 1.61), ambas mitades positivas.
  - `rsi2_reversion|tendencia200,sesion_lny|obj2r`: entreno +0.22 R (364 ops, t 2.96), prueba **+0.25 R** (163 ops, t 2.18, PF 1.44).
- **Por qué funcionan:** en diario el coste es una parte mínima del stop y los índices de EE.UU. tienen sesgo alcista de
  largo plazo; comprar retrocesos (RSI2) o giros del MACD por encima de la SMA200 aprovecha ese sesgo. La RSI(2) en el
  S&P 500 sobre la SMA200 es una estrategia conocida (Connors), lo que da credibilidad al resultado.
- **Ojo:** en velas diarias el filtro `sesion_lny` solo deja pasar las velas cuya hora de apertura cae en 12–16 UTC, que
  son los índices (US 500 y US Tech 100). En la práctica, las dos reglas son **para índices de EE.UU.**, no para divisas.
- **Casi aprobada:** `tendencia_retroceso|tendencia200,vol_baja|obj2r` en diario, positiva en los 8 activos (+0.26 R,
  243 ops, t 3.1) pero con un tramo débil. A favor de la tendencia y en diario sí funciona; en intradía pierde.
- **Pendiente:** son operaciones de varios días; el scalper intradía no las puede ejecutar. Hace falta un ejecutor diario
  y confirmar qué índices tienen Multipliers en Deriv (US 500 no los tiene).

### 2026-11-19 — Fusión: operaciones rápidas (15m/1h) filtradas con el contexto diario
- **Hipótesis:** si el diario tiene ventaja (tendencia SMA200 + retroceso RSI2), entrar en 15m/1h solo en esa dirección
  debería heredar la ventaja con operaciones rápidas.
- **Resultado (8 activos agrupados, 1120 variantes):** 0 aprobadas (1 de 25 por azar). Mejor: `divergencia_rsi|d_tend,d_impulso|obj2r`
  1h, +0.18 R en 94 ops, t 1.74 (no significativa).
- **Lo interesante:** `rsi2_reversion|d_retroceso|obj2r` en 1h gana solo en los índices de EE.UU. (US 500 +0.51 R en 37 ops,
  US Tech 100 +0.33 R en 36) y pierde o empata en divisas, oro y BTC. Coincide con el hallazgo diario: la ventaja está en los
  índices, no en la estrategia rápida. Muestra pequeña (73 ops): hipótesis, no regla.
- **Conclusión:** con datos de velas y costes reales no aparece ninguna estrategia rápida rentable de forma fiable.
