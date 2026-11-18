# Ejecutor automático en Deriv (cuenta demo)

Cada mañana el orquestador escribe `trading/planes/AAAA-MM-DD.json`. Al subirlo al repositorio,
GitHub Actions (`.github/workflows/ejecutor-deriv.yml`) arranca `deriv_ejecutor.py`, que:

1. Se conecta a Deriv y **se niega a operar si la cuenta no es demo** (salvo `DERIV_PERMITIR_REAL=si`).
2. Vigila cada operación con velas de 15 min de Deriv y entra solo cuando se cumple el gatillo.
3. Abre **dos contratos Multiplier** de media posición cada uno, con stop loss y take profit
   ya colocados en Deriv: A sale en TP1 y B en TP2. Si A cobra y el precio vuelve a la entrada, cierra B.
4. Arriesga como máximo el **1% del saldo** por operación (máximo 3 a la vez). Si en el día pierde un **3%**, cierra todo y para.
5. Cierra todo a la hora límite del plan y guarda el resultado en `trading/ejecuciones/AAAA-MM-DD.json`.

## Scalper (operaciones rápidas)
`scalper.py` (`.github/workflows/scalper-deriv.yml`) arranca con el mismo plan y opera **velas de 5 min**
en EUR/USD, GBP/USD, XAU/USD y BTC/USD hasta las 16:30 UTC (11:30 Bogotá).
- **Señal:** tendencia (EMA 9/21/50) más retroceso a la EMA21 y RSI.
- **Salidas:** stop a 1.2 × ATR, objetivo a 1.8 × ATR, y cierre a los 30 min si no toca ninguno.
- **Límites:**
  - Riesgo 0.25 % por operación, máximo 2 abiertas y 6 en el día.
  - Para si pierde el 1 % del saldo o 3 operaciones seguidas.
  - Para al ganar la meta diaria: 30 USD, o la variable de Actions `META_DIARIA_USD`.
- Respeta el sesgo del plan y los horarios de noticias (`eventos_alto_impacto_utc`).
- Resultado en `trading/ejecuciones/AAAA-MM-DD-scalping.json`.

## Configuración (una sola vez)
1. En Deriv (cuenta **demo**): *Configuración de cuenta → Token de API* → crea un token con permisos **Read** y **Trade**.
2. En GitHub: repositorio → *Settings → Secrets and variables → Actions → New repository secret*,
   con nombre `DERIV_TOKEN` y el token como valor.
3. Prueba: pestaña *Actions → Ejecutor Deriv (demo) → Run workflow*, con la rama de trabajo y el modo `verificar`.
   El registro debe mostrar "Conectado a Deriv: cuenta DEMO …".

## Formato del plan
```json
{
  "fecha": "2026-11-18",
  "operaciones": [
    {
      "activo": "EUR/USD", "simbolo_deriv": "frxEURUSD", "direccion": "venta",
      "gatillo": "retesteo_abajo", "nivel": 1.1000,
      "stop": 1.1025, "tp1": 1.0960, "tp2": 1.0935,
      "valido_hasta_utc": "2026-11-18T18:00:00Z", "cerrar_antes_utc": "2026-11-18T18:30:00Z",
      "confianza": 3
    }
  ]
}
```
- `direccion`: `compra` o `venta`.
- `gatillo`:
  - `mercado`: entra ya.
  - `ruptura_arriba` / `ruptura_abajo`: entra cuando una vela de 15 min cierra por encima / por debajo de `nivel`.
  - `retesteo_abajo` (venta): el precio sube a `nivel` y una vela de 15 min cierra por debajo.
  - `retesteo_arriba` (compra): el precio baja a `nivel` y una vela de 15 min cierra por encima.
- Símbolos de Deriv frecuentes:
  - Forex: `frxEURUSD`, `frxGBPUSD`, `frxUSDJPY`, `frxAUDUSD`.
  - Oro: `frxXAUUSD`.
  - Cripto: `cryBTCUSD`, `cryETHUSD`.
  - El ejecutor comprueba en Deriv si el símbolo admite Multipliers; si no, omite la operación.

## Límites
- Un job de GitHub dura como máximo 6 h. El ejecutor cierra todo a las 5 h 40 min de haber empezado.
- Los Multipliers de Deriv cobran comisión y spread, así que el resultado real es algo peor que el teórico.
- No es asesoría financiera. Úsalo en demo hasta tener al menos 4–6 semanas de historial positivo.
