# Elferes — Agentes de análisis

## 📈 Trading intradía (acciones, cripto y divisas)
Tres agentes especialistas investigan cada día **noticias, acción del precio e indicadores** (EMA, RSI, MACD, ATR)
y un orquestador entrega el plan del día con **precio de entrada, stop loss y precios de salida (TP1/TP2)**.

- Instrucciones del orquestador: [trading/AGENTE_TRADING.md](trading/AGENTE_TRADING.md)
- Agentes: [.claude/agents/](.claude/agents/) — `analista-acciones`, `analista-cripto`, `analista-divisas`
- Indicadores técnicos: `python3 trading/indicadores.py NVDA BTC-USD EURUSD=X`
- Planes diarios: [trading/reportes/](trading/reportes/) · Historial: [trading/reportes/HISTORIAL.md](trading/reportes/HISTORIAL.md)

> No es asesoría financiera. Usa siempre stop loss y arriesga como máximo el 1% del capital por operación.

## ⚽ Apuestas deportivas (combinada cuota ≥ 10)
- Instrucciones del agente: [AGENTE.md](AGENTE.md)
- Reportes diarios: [reportes/](reportes/) · Historial: [reportes/HISTORIAL.md](reportes/HISTORIAL.md)

> Las apuestas implican riesgo. Una cuota 10 tiene ~10% de probabilidad implícita. Juega con responsabilidad.
