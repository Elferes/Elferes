# Laboratorio de estrategias

Lo mantiene `investigador-estrategias`. Cada entrada: hipótesis, cambio, resultado (entrenamiento y prueba),
conclusión y por qué funcionó o falló. Ranking actual: [RANKING.md](RANKING.md).

## Estrategias en la biblioteca (`trading/ejecutor/estrategias.py`)
| Estrategia | Idea | Mercado donde debería funcionar | Estado |
|---|---|---|---|
| tendencia_retroceso | Tendencia EMA 9/21/50 + retroceso a la EMA21 + vela de reanudación | Tendencia limpia | **Activa** (inicial) |
| ruptura_rango | Compresión de 12 velas (< 2.5 ATR) y ruptura con cuerpo fuerte | Tras rangos estrechos, apertura de sesiones | En prueba |
| reversion_bollinger | Fuera de Bollinger con RSI extremo y vuelta dentro, objetivo la media | Lateral (EMA50 plana) | En prueba |
| cruce_ema | EMA9 cruza EMA21 a favor de la EMA50, con RSI | Inicio de tendencias | En prueba |
| envolvente_nivel | Envolvente en el máximo o mínimo de 30 velas | Giros en soportes y resistencias | En prueba |

## Diario del laboratorio
### 2026-11-18 — Creación
- Hipótesis: ninguna estrategia funciona en todos los mercados, así que el scalper debe usar solo las que demuestren
  ventaja fuera de muestra en cada activo.
- Primer backtest lanzado con 6 activos (EUR/USD, GBP/USD, USD/JPY, oro, BTC, US 500) en 5m, 15m y 1h.
