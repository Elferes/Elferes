# Bitácora de aprendizaje

La mantiene el agente `revisor-aprendizaje`. Los analistas leen **Lecciones vigentes** cada mañana.

**Cuenta virtual:** empieza con 100 USD el 2026-11-19. El riesgo y los límites se calculan sobre este capital,
no sobre el saldo real de la demo.

## Lecciones vigentes
_(Reglas con al menos 5 casos de evidencia. Máximo 10.)_

- Aún no hay suficientes operaciones.

## Lecciones del backtest (2026-11-18, aún sin confirmar en vivo)
- **5 minutos no es rentable con estos costes:** el spread y la comisión equivalen a una parte grande del stop.
  Todas las estrategias en 5m salen negativas en los 6 activos.
- **La tendencia con retroceso pierde en casi todo** (hasta −0.62 R en 5m): demasiadas entradas tardías.
- **La reversión en Bollinger funciona en GBP/USD y EUR/USD 1h**, que pasan mucho tiempo en rango; en BTC 1h pierde, porque tiende.
- **Patrones más fiables:** doble techo en EUR/USD 15m (60.8 %, 296 casos), divergencia bajista en BTC 15m (60.0 %),
  doble techo en US 500 5m y 15m (58 %).

- **Intradía (15m–4h) no muestra ventaja significativa** con 14 estrategias y 11664 variantes: ni por activo ni agrupado.
- **En diario sí:** RSI(2) y giro del MACD a favor de la SMA200 en US 500 y US Tech 100 pasan la prueba ciega
  (+0.25 a +0.29 R por operación, t > 2, 0 aprobadas por azar). Las 5 combinaciones v2 del scalper no tienen
  significancia estadística: se mantienen solo como prueba en demo con 1 % de riesgo.

## Hipótesis por comprobar
- Las operaciones rápidas funcionan mejor en el solapamiento Londres–Nueva York (12:00–16:00 UTC).
- Operar a favor de la tendencia diaria y de fondo da mejor % de acierto que operar solo con la de 15 min.
- El oro y BTC necesitan un stop más amplio en ATR que las divisas.

## Experimentos
| Versión | Fecha | Cambio | Motivo (datos) | Métrica a vigilar | Evaluar el | Resultado |
|---|---|---|---|---|---|---|
| 1 | 2026-11-18 | Parámetros iniciales | — | % acierto y R medio del scalper | tras 20 operaciones | — |
| 2 | 2026-11-18 | El scalper deja 5m y opera solo 5 combinaciones APTA (GBP/USD 1h y EUR/USD 1h reversión Bollinger; US 500 1h cruce EMA y envolvente; oro 15m ruptura de rango) | Backtest: las 5 estrategias en 5m pierden con costes en todos los activos (−0.08 a −0.62 R); 5 combinaciones de 15m/1h dan +0.18 a +0.45 R fuera de muestra | Esperanza real por combinación frente al backtest | tras 20 operaciones | — |

## Estadísticas
_(Se actualizan cada día.)_

| Sistema | Operaciones | Ganadoras | % acierto | R medio | USD | Cuenta virtual |
|---|---|---|---|---|---|---|
| Plan diario | 0 | 0 | — | — | 0.00 | 100.00 |
| Scalper | 0 | 0 | — | — | 0.00 | — |

## Diario
_(Una entrada por día: qué pasó, por qué se ganó o se perdió.)_
