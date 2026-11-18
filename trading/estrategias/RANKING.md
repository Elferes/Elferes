# Ranking de estrategias y patrones — 2026-11-18

Generado por `backtest.py`. **Prueba** = el 30 % más reciente del historial, no usado para elegir nada.
**APTA**: ≥ 20 operaciones en prueba, esperanza ≥ +0.10 R y profit factor ≥ 1.2 (ya con costes).

## Estrategias (ordenadas por esperanza en la prueba)

| Activo | TF | Estrategia | Ops prueba | Acierto | Esperanza (R) | Profit factor | Máx. DD (R) | Veredicto |
|---|---|---|---|---|---|---|---|---|
| US 500 | 15m | reversion_bollinger | 3 | 33.3 % | 0.52 | 1.74 | 1.08 | pocos datos |
| GBP/USD | 1h | reversion_bollinger | 23 | 69.6 % | 0.446 | 2.83 | 2.57 | APTA |
| US 500 | 15m | cruce_ema | 9 | 66.7 % | 0.361 | 2.0 | 2.16 | pocos datos |
| US 500 | 1h | cruce_ema | 54 | 53.7 % | 0.251 | 1.52 | 5.27 | APTA |
| XAU/USD | 15m | ruptura_rango | 41 | 56.1 % | 0.202 | 1.59 | 3.64 | APTA |
| EUR/USD | 1h | reversion_bollinger | 23 | 47.8 % | 0.181 | 1.31 | 4.57 | APTA |
| US 500 | 1h | envolvente_nivel | 24 | 54.2 % | 0.181 | 1.4 | 2.28 | APTA |
| XAU/USD | 1h | reversion_bollinger | 18 | 50.0 % | 0.118 | 1.25 | 2.19 | pocos datos |
| XAU/USD | 1h | ruptura_rango | 86 | 51.2 % | 0.088 | 1.2 | 8.87 | marginal |
| USD/JPY | 15m | envolvente_nivel | 49 | 63.3 % | 0.064 | 1.17 | 3.25 | marginal |
| EUR/USD | 1h | ruptura_rango | 129 | 49.6 % | 0.055 | 1.12 | 12.58 | marginal |
| US 500 | 1h | tendencia_retroceso | 96 | 45.8 % | 0.054 | 1.1 | 9.62 | marginal |
| XAU/USD | 15m | tendencia_retroceso | 106 | 45.3 % | 0.023 | 1.05 | 9.73 | marginal |
| USD/JPY | 15m | reversion_bollinger | 7 | 57.1 % | 0.017 | 1.03 | 2.98 | pocos datos |
| GBP/USD | 1h | envolvente_nivel | 88 | 46.6 % | 0.003 | 1.0 | 19.7 | marginal |
| XAU/USD | 1h | cruce_ema | 128 | 42.2 % | -0.014 | 0.98 | 12.93 | descartar |
| USD/JPY | 1h | envolvente_nivel | 110 | 49.1 % | -0.018 | 0.96 | 15.22 | descartar |
| XAU/USD | 15m | cruce_ema | 27 | 44.4 % | -0.031 | 0.94 | 5.91 | descartar |
| US 500 | 1h | ruptura_rango | 24 | 45.8 % | -0.049 | 0.9 | 4.97 | descartar |
| GBP/USD | 1h | ruptura_rango | 138 | 44.9 % | -0.067 | 0.88 | 17.24 | descartar |
| USD/JPY | 1h | ruptura_rango | 138 | 45.7 % | -0.068 | 0.87 | 19.42 | descartar |
| GBP/USD | 15m | cruce_ema | 46 | 52.2 % | -0.069 | 0.88 | 8.82 | descartar |
| EUR/USD | 15m | ruptura_rango | 27 | 48.1 % | -0.074 | 0.87 | 5.53 | descartar |
| XAU/USD | 5m | reversion_bollinger | 17 | 41.2 % | -0.083 | 0.84 | 4.47 | pocos datos |
| EUR/USD | 1h | cruce_ema | 165 | 42.4 % | -0.086 | 0.86 | 18.47 | descartar |
| EUR/USD | 1h | tendencia_retroceso | 366 | 41.8 % | -0.091 | 0.85 | 46.53 | descartar |
| XAU/USD | 1h | tendencia_retroceso | 303 | 39.3 % | -0.095 | 0.84 | 41.29 | descartar |
| USD/JPY | 1h | reversion_bollinger | 16 | 37.5 % | -0.1 | 0.84 | 8.76 | pocos datos |
| XAU/USD | 1h | envolvente_nivel | 93 | 40.9 % | -0.102 | 0.81 | 15.53 | descartar |
| GBP/USD | 15m | ruptura_rango | 32 | 50.0 % | -0.104 | 0.8 | 8.36 | descartar |
| GBP/USD | 1h | cruce_ema | 157 | 40.1 % | -0.11 | 0.82 | 21.32 | descartar |
| USD/JPY | 1h | tendencia_retroceso | 384 | 40.4 % | -0.115 | 0.81 | 49.73 | descartar |
| BTC/USD | 1h | envolvente_nivel | 103 | 40.8 % | -0.139 | 0.76 | 27.22 | descartar |
| XAU/USD | 15m | envolvente_nivel | 37 | 43.2 % | -0.141 | 0.73 | 8.63 | descartar |
| BTC/USD | 15m | cruce_ema | 57 | 45.6 % | -0.142 | 0.75 | 14.15 | descartar |
| US 500 | 5m | ruptura_rango | 30 | 40.0 % | -0.142 | 0.71 | 4.74 | descartar |
| BTC/USD | 1h | reversion_bollinger | 40 | 40.0 % | -0.151 | 0.72 | 9.89 | descartar |
| GBP/USD | 1h | tendencia_retroceso | 391 | 38.9 % | -0.155 | 0.75 | 66.36 | descartar |
| USD/JPY | 1h | cruce_ema | 153 | 38.6 % | -0.159 | 0.75 | 26.81 | descartar |
| BTC/USD | 15m | ruptura_rango | 44 | 40.9 % | -0.159 | 0.69 | 11.28 | descartar |
| US 500 | 15m | tendencia_retroceso | 23 | 43.5 % | -0.162 | 0.72 | 5.66 | descartar |
| BTC/USD | 1h | ruptura_rango | 135 | 38.5 % | -0.173 | 0.7 | 28.75 | descartar |
| EUR/USD | 1h | envolvente_nivel | 115 | 41.7 % | -0.186 | 0.7 | 24.91 | descartar |
| USD/JPY | 15m | ruptura_rango | 48 | 39.6 % | -0.202 | 0.64 | 10.6 | descartar |
| US 500 | 1h | reversion_bollinger | 4 | 25.0 % | -0.213 | 0.64 | 2.4 | pocos datos |
| BTC/USD | 15m | tendencia_retroceso | 146 | 40.4 % | -0.219 | 0.65 | 32.04 | descartar |
| BTC/USD | 1h | tendencia_retroceso | 386 | 36.5 % | -0.221 | 0.66 | 87.2 | descartar |
| GBP/USD | 15m | tendencia_retroceso | 128 | 41.4 % | -0.226 | 0.66 | 30.14 | descartar |
| XAU/USD | 5m | envolvente_nivel | 108 | 40.7 % | -0.231 | 0.59 | 29.09 | descartar |
| EUR/USD | 15m | tendencia_retroceso | 113 | 40.7 % | -0.234 | 0.63 | 36.73 | descartar |
| EUR/USD | 5m | reversion_bollinger | 14 | 35.7 % | -0.238 | 0.6 | 7.8 | pocos datos |
| XAU/USD | 5m | cruce_ema | 146 | 41.1 % | -0.241 | 0.6 | 39.37 | descartar |
| USD/JPY | 5m | ruptura_rango | 139 | 37.4 % | -0.244 | 0.53 | 33.98 | descartar |
| XAU/USD | 5m | ruptura_rango | 91 | 31.9 % | -0.262 | 0.5 | 25.12 | descartar |
| EUR/USD | 15m | cruce_ema | 41 | 36.6 % | -0.278 | 0.61 | 15.01 | descartar |
| US 500 | 5m | cruce_ema | 26 | 26.9 % | -0.279 | 0.52 | 9.01 | descartar |
| XAU/USD | 5m | tendencia_retroceso | 350 | 38.9 % | -0.28 | 0.57 | 104.43 | descartar |
| US 500 | 5m | tendencia_retroceso | 87 | 35.6 % | -0.283 | 0.54 | 28.45 | descartar |
| BTC/USD | 1h | cruce_ema | 152 | 32.2 % | -0.288 | 0.59 | 45.23 | descartar |
| USD/JPY | 15m | cruce_ema | 68 | 36.8 % | -0.309 | 0.52 | 24.58 | descartar |
| BTC/USD | 15m | reversion_bollinger | 7 | 42.9 % | -0.312 | 0.38 | 3.17 | pocos datos |
| XAU/USD | 15m | reversion_bollinger | 7 | 28.6 % | -0.329 | 0.41 | 2.81 | pocos datos |
| USD/JPY | 5m | envolvente_nivel | 131 | 36.6 % | -0.336 | 0.45 | 46.74 | descartar |
| BTC/USD | 5m | reversion_bollinger | 29 | 37.9 % | -0.34 | 0.47 | 10.33 | descartar |
| USD/JPY | 5m | reversion_bollinger | 29 | 37.9 % | -0.342 | 0.46 | 11.04 | descartar |
| EUR/USD | 15m | envolvente_nivel | 33 | 27.3 % | -0.345 | 0.43 | 12.37 | descartar |
| USD/JPY | 5m | cruce_ema | 188 | 34.0 % | -0.376 | 0.46 | 70.78 | descartar |
| USD/JPY | 15m | tendencia_retroceso | 154 | 33.1 % | -0.382 | 0.45 | 61.76 | descartar |
| US 500 | 5m | envolvente_nivel | 25 | 28.0 % | -0.385 | 0.43 | 11.26 | descartar |
| GBP/USD | 15m | envolvente_nivel | 49 | 38.8 % | -0.388 | 0.46 | 20.41 | descartar |
| BTC/USD | 15m | envolvente_nivel | 44 | 29.5 % | -0.395 | 0.43 | 17.39 | descartar |
| EUR/USD | 5m | ruptura_rango | 76 | 31.6 % | -0.401 | 0.35 | 30.47 | descartar |
| BTC/USD | 5m | cruce_ema | 184 | 35.3 % | -0.418 | 0.4 | 77.42 | descartar |
| GBP/USD | 5m | envolvente_nivel | 80 | 43.8 % | -0.439 | 0.42 | 36.32 | descartar |
| USD/JPY | 5m | tendencia_retroceso | 469 | 31.1 % | -0.451 | 0.36 | 211.68 | descartar |
| US 500 | 15m | ruptura_rango | 9 | 22.2 % | -0.451 | 0.41 | 5.48 | pocos datos |
| BTC/USD | 5m | envolvente_nivel | 108 | 33.3 % | -0.46 | 0.33 | 50.93 | descartar |
| BTC/USD | 5m | ruptura_rango | 129 | 31.0 % | -0.461 | 0.29 | 59.45 | descartar |
| BTC/USD | 5m | tendencia_retroceso | 462 | 34.0 % | -0.464 | 0.38 | 214.79 | descartar |
| US 500 | 15m | envolvente_nivel | 10 | 30.0 % | -0.468 | 0.33 | 4.68 | pocos datos |
| GBP/USD | 15m | reversion_bollinger | 8 | 25.0 % | -0.504 | 0.39 | 6.61 | pocos datos |
| EUR/USD | 5m | cruce_ema | 158 | 35.4 % | -0.507 | 0.39 | 80.93 | descartar |
| US 500 | 5m | reversion_bollinger | 7 | 14.3 % | -0.509 | 0.27 | 3.75 | pocos datos |
| GBP/USD | 5m | cruce_ema | 188 | 41.5 % | -0.512 | 0.37 | 98.31 | descartar |
| GBP/USD | 5m | ruptura_rango | 57 | 35.1 % | -0.531 | 0.28 | 32.22 | descartar |
| EUR/USD | 5m | tendencia_retroceso | 332 | 34.0 % | -0.549 | 0.35 | 187.03 | descartar |
| EUR/USD | 5m | envolvente_nivel | 101 | 29.7 % | -0.595 | 0.29 | 61.31 | descartar |
| GBP/USD | 5m | reversion_bollinger | 14 | 28.6 % | -0.617 | 0.25 | 8.86 | pocos datos |
| GBP/USD | 5m | tendencia_retroceso | 395 | 35.9 % | -0.624 | 0.3 | 246.49 | descartar |
| EUR/USD | 15m | reversion_bollinger | 4 | 0.0 % | -0.963 | 0.0 | 3.85 | pocos datos |

## Patrones más fiables (≥ 30 casos; avanzar 1 ATR a favor antes que 1 ATR en contra, 12 velas)

| Activo y TF | Patrón | Sesgo | Casos | Fiabilidad |
|---|---|---|---|---|
| EUR/USD 15m | doble_techo | venta | 296 | 60.8 % |
| BTC/USD 15m | divergencia_bajista | venta | 240 | 60.0 % |
| US 500 15m | divergencia_bajista | venta | 74 | 59.5 % |
| USD/JPY 15m | divergencia_alcista | compra | 207 | 58.0 % |
| US 500 5m | doble_techo | venta | 491 | 58.0 % |
| US 500 15m | doble_techo | venta | 166 | 57.8 % |
| US 500 15m | ruptura_maximo_20 | compra | 97 | 57.7 % |
| GBP/USD 15m | divergencia_bajista | venta | 254 | 56.7 % |
| XAU/USD 15m | tres_soldados | compra | 32 | 56.2 % |
| XAU/USD 1h | doble_techo | venta | 1876 | 56.2 % |
| US 500 5m | ruptura_minimo_20 | venta | 299 | 56.2 % |
| US 500 1h | ruptura_maximo_20 | compra | 503 | 56.1 % |
| US 500 15m | ruptura_minimo_20 | venta | 95 | 55.8 % |
| USD/JPY 5m | tres_soldados | compra | 167 | 54.5 % |
| GBP/USD 5m | divergencia_alcista | compra | 647 | 54.4 % |
| BTC/USD 1h | divergencia_bajista | venta | 905 | 54.4 % |
| GBP/USD 1h | doble_suelo | compra | 1717 | 54.0 % |
| US 500 1h | envolvente_alcista | compra | 274 | 54.0 % |
| US 500 5m | tres_cuervos | venta | 76 | 53.9 % |
| GBP/USD 1h | divergencia_alcista | compra | 780 | 53.5 % |
| XAU/USD 15m | ruptura_maximo_20 | compra | 202 | 53.5 % |
| EUR/USD 1h | martillo | compra | 569 | 53.4 % |
| US 500 1h | divergencia_bajista | venta | 350 | 53.4 % |
| EUR/USD 1h | divergencia_alcista | compra | 745 | 53.3 % |
| EUR/USD 5m | tres_cuervos | venta | 282 | 53.2 % |
| XAU/USD 5m | divergencia_bajista | venta | 430 | 53.0 % |
| XAU/USD 15m | ruptura_minimo_20 | venta | 302 | 53.0 % |
| GBP/USD 5m | divergencia_bajista | venta | 744 | 52.8 % |
| XAU/USD 15m | divergencia_alcista | compra | 248 | 52.8 % |
| US 500 1h | divergencia_alcista | compra | 159 | 52.8 % |
| GBP/USD 15m | doble_techo | venta | 596 | 52.7 % |
| US 500 15m | divergencia_alcista | compra | 74 | 52.7 % |
| USD/JPY 1h | divergencia_alcista | compra | 857 | 52.5 % |
| XAU/USD 1h | divergencia_bajista | venta | 828 | 52.4 % |
| GBP/USD 1h | tres_soldados | compra | 222 | 52.3 % |
| EUR/USD 5m | doble_techo | venta | 492 | 52.2 % |
| GBP/USD 15m | tres_soldados | compra | 90 | 52.2 % |
| XAU/USD 1h | ruptura_maximo_20 | compra | 963 | 52.2 % |
| XAU/USD 15m | tres_cuervos | venta | 48 | 52.1 % |
| USD/JPY 15m | tres_soldados | compra | 50 | 52.0 % |
