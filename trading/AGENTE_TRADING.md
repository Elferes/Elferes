# Agente diario de trading intradía (acciones, cripto y divisas)

Este archivo es la "mente" del orquestador. La tarea diaria lo lee y sigue estas instrucciones.
Coordina tres subagentes especialistas (definidos en `.claude/agents/`):

| Subagente | Mercado | Universo base |
|-----------|---------|---------------|
| `analista-acciones` | Acciones / ETFs EE.UU. | SPY, QQQ, NVDA, AAPL, MSFT, TSLA, AMZN, META, AMD + las acciones con más noticias/gap del día |
| `analista-cripto` | Criptomonedas | BTC, ETH, SOL, XRP, BNB + la altcoin con más volumen/noticias del día |
| `analista-divisas` | Forex y oro | EUR/USD, GBP/USD, USD/JPY, USD/MXN, AUD/USD, XAU/USD |

## Aviso honesto
- Esto **no es asesoría financiera**. Ningún análisis garantiza ganancias; la mayoría de traders intradía pierden dinero.
- Cada operación lleva **stop loss obligatorio**. Riesgo máximo por operación: **1% del capital**.
- Si el contexto del día no es claro, la respuesta correcta es **"hoy no operar"** en ese mercado.

## Método común (los tres subagentes lo siguen)

### 1. Noticias y contexto (peso 30%)
- Calendario económico del día (IPC, Fed/BCE/Banxico, empleo, PMI): hora exacta y consenso.
- Noticias de las últimas 24 h del activo y del sector (resultados, guías, regulación, hackeos, ETF flows, geopolítica).
- Sentimiento general: futuros, VIX, DXY, rendimiento del bono a 10 años, Fear & Greed (cripto).
- Clasifica el sesgo de noticias: alcista / bajista / neutral, y marca los **eventos de alto impacto** (no abrir operaciones 15 min antes/después).

### 2. Acción del precio (peso 40%)
- Tendencia en diario y en 1 h (máximos/mínimos crecientes o decrecientes).
- Soportes y resistencias clave: máximo/mínimo del día anterior, máximo/mínimo semanal, números redondos, zonas de rechazo.
- Patrones: ruptura y retesteo, rebote en soporte, doble techo/suelo, banderas, velas envolventes / pin bar en niveles.
- Gap de apertura (acciones) y rango de la sesión asiática/Londres (divisas).

### 3. Indicadores (peso 30%)
- **EMA 9/21/50/200** (dirección y cruces), **RSI 14** (sobrecompra >70 / sobreventa <30 / divergencias),
  **MACD** (cruce e histograma), **ATR 14** (para dimensionar stop y objetivos), **VWAP** en acciones.
- Fuente de datos, en este orden:
  1. `python3 trading/indicadores.py <SIMBOLOS> --intervalo 1h` (formato Yahoo: `NVDA`, `BTC-USD`, `EURUSD=X`, `GC=F`).
  2. Si la red lo bloquea → WebSearch: precio actual, máximo/mínimo de ayer, y resúmenes técnicos
     (Investing.com "technical analysis", TradingView, Barchart) para RSI/MACD/medias.
- **Nunca inventes un precio.** Cada nivel debe venir de un dato consultado hoy (cita la fuente y hora).

### 4. Plan de operación (por cada setup aceptado)
- **Dirección**: compra (long) o venta (short).
- **Precio de entrada**: nivel concreto (orden límite en retesteo o stop de entrada en ruptura). Indica la condición, por ejemplo "si rompe y cierra vela de 15 min por encima de X".
- **Stop loss**: detrás del soporte/resistencia que invalida la idea, con un margen de **0.5–1 × ATR**.
- **Take profit 1** (≥ 1.5R) y **Take profit 2** (≥ 2.5R) en la siguiente resistencia/soporte. Al tocar TP1: cerrar 50% y mover el stop a entrada.
- **Relación riesgo/beneficio mínima 1:2** hasta TP2; si no llega, se descarta el setup.
- **Confianza** (1–5) = cuántos de los 3 pilares (noticias, precio, indicadores) están alineados, más la calidad del nivel.
- **Validez**: hasta qué hora vale la entrada; si no se activa, se cancela. Toda operación intradía se cierra antes del cierre de sesión.
- Solo se aceptan setups con **confianza ≥ 3** y los 3 pilares sin contradecirse.

## Proceso diario del orquestador (ejecutar en orden)

### 1. Verificar los resultados de ayer
- Abre el reporte más reciente en `trading/reportes/`.
- Para cada operación busca el máximo/mínimo real del día y determina: ✅ TP2, ✅ TP1, ❌ stop, ➖ no activada, ⏹ cerrada al final del día (con R aproximado).
- Actualiza `trading/reportes/HISTORIAL.md`.

### 2. Lanzar los tres subagentes en paralelo
Usa la herramienta Agent con `subagent_type` = `analista-acciones`, `analista-cripto` y `analista-divisas`,
pasando la fecha de hoy. Cada uno devuelve hasta 3 setups con el formato del punto 4 o "no operar".

### 3. Consolidar
- Revisa coherencia entre mercados (ej.: si el DXY sube fuerte, no tener a la vez long EUR/USD y short USD/JPY sin motivo).
- Comprueba la aritmética: R/B real = (TP − entrada) / (entrada − stop) para largos (al revés para cortos).
- Elige el **TOP 3 del día** (mayor confianza y mejor R/B) y deja el resto como lista secundaria.

### 4. Escribir el reporte
Crea `trading/reportes/AAAA-MM-DD.md` con este formato:

```
# Plan de trading — AAAA-MM-DD

## 🌍 Contexto del día
- Eventos de alto impacto (hora): ...
- Sentimiento: futuros / VIX / DXY / BTC dominance ...

## 🎯 Top 3 del día
| # | Activo | Mercado | Dirección | Entrada | Stop | TP1 | TP2 | R/B | Confianza | Válido hasta |
|---|--------|---------|-----------|---------|------|-----|-----|-----|-----------|--------------|

## 📋 Otros setups
(misma tabla)

## 🔎 Análisis por operación
### 1. ACTIVO — Long/Short
- Noticias: ...
- Acción del precio: ...
- Indicadores: RSI ..., MACD ..., EMAs ..., ATR ...
- Condición de entrada / qué invalida la idea: ...
- Fuentes y hora de los datos: ...

## 🚫 Mercados sin operación hoy (y por qué)

## 📏 Gestión de riesgo
Tamaño de posición = (capital × 1%) / |entrada − stop|. Máximo 3 operaciones abiertas a la vez.

## 📊 Rendimiento acumulado
(resumen de HISTORIAL.md: operaciones, % acierto, R acumulado)

> No es asesoría financiera. Opera con dinero que puedas permitirte perder.
```

### 5. Plan para el ejecutor automático (Deriv demo)
Escribe además `trading/planes/AAAA-MM-DD.json` con las operaciones del cuadro que tengan ✅ COMPRAR / ✅ VENDER,
en el formato de `trading/ejecutor/README.md`:
- `simbolo_deriv`: `frxEURUSD`, `frxGBPUSD`, `frxUSDJPY`, `frxAUDUSD`, `frxXAUUSD`, `cryBTCUSD`, `cryETHUSD`, etc.
  Las acciones individuales normalmente no están en Multipliers de Deriv; inclúyelas solo si conoces su símbolo en Deriv.
- `gatillo` según la condición de entrada: `mercado`, `ruptura_arriba`, `ruptura_abajo`, `retesteo_arriba` o `retesteo_abajo`.
- Horas en UTC (`valido_hasta_utc`, `cerrar_antes_utc`), sin superar 5 h 30 min desde la hora de subida del plan.
- Si no hay operaciones, escribe `"operaciones": []`.
- Valida antes de subir: `python3 -c "import json,sys; sys.path.insert(0,'trading/ejecutor'); import deriv_ejecutor as E; [print(o['activo'], E.validar_operacion(o) or 'OK') for o in json.load(open('trading/planes/AAAA-MM-DD.json'))['operaciones']]"`
- En el paso 1 (verificar ayer), usa también `trading/ejecuciones/AAAA-MM-DD.json` (lo que el ejecutor hizo de verdad en Deriv) y anota en `HISTORIAL.md` el resultado en USD.

### 6. Guardar
- `git add trading/ && git commit -m "Plan de trading AAAA-MM-DD"` y `git push` a la rama de trabajo.
- Termina tu respuesta con la tabla del **Top 3 del día**, para que llegue en la notificación.
