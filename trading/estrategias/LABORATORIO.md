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
