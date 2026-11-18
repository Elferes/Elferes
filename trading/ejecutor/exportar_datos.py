#!/usr/bin/env python3
"""Exporta gráficas de Deriv (velas + indicadores) a trading/datos/ para que los agentes las lean.

Temporalidades: 15 min, 1 h, diaria (de Deriv) y semanal, mensual y anual (agregadas desde la diaria).
Para cada una guarda un resumen técnico (tendencia, EMAs, RSI, MACD, ATR, soportes y resistencias,
máximos y mínimos de periodos anteriores, variaciones) y las últimas velas.

Uso: python3 trading/ejecutor/exportar_datos.py            (necesita DERIV_TOKEN y DERIV_APP_ID)
"""
import asyncio
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import deriv_ejecutor as D  # noqa: E402
import scalper as S  # noqa: E402

ACTIVOS = {
    "EUR/USD": "frxEURUSD", "GBP/USD": "frxGBPUSD", "USD/JPY": "frxUSDJPY", "AUD/USD": "frxAUDUSD",
    "XAU/USD": "frxXAUUSD", "BTC/USD": "cryBTCUSD", "ETH/USD": "cryETHUSD",
    "US 500": "OTC_SPC", "US Tech 100": "OTC_NDX", "Wall Street 30": "OTC_DJI",
}
TEMPORALIDADES = {"15m": (900, 400), "1h": (3600, 500), "diario": (86400, 3650)}
ULTIMAS_VELAS = {"15m": 40, "1h": 48, "diario": 60, "semanal": 52, "mensual": 36, "anual": 15}


def agregar(diarias, clave):
    """Agrupa velas diarias por semana ISO, mes o año."""
    grupos = {}
    for v in diarias:
        d = dt.datetime.fromtimestamp(v["epoch"], dt.timezone.utc).date()
        k = {"semanal": d.isocalendar()[:2], "mensual": (d.year, d.month), "anual": (d.year,)}[clave]
        g = grupos.get(k)
        if g is None:
            grupos[k] = dict(v)
        else:
            g["high"], g["low"], g["close"] = max(g["high"], v["high"]), min(g["low"], v["low"]), v["close"]
    return [grupos[k] for k in sorted(grupos)]


def pivotes(velas, lado=2, n=3):
    """Últimos máximos y mínimos de giro (fractales)."""
    alt, baj = [], []
    for i in range(lado, len(velas) - lado):
        ventana = velas[i - lado:i + lado + 1]
        if velas[i]["high"] == max(x["high"] for x in ventana):
            alt.append(velas[i]["high"])
        if velas[i]["low"] == min(x["low"] for x in ventana):
            baj.append(velas[i]["low"])
    return alt[-n:], baj[-n:]


def resumen(velas):
    if len(velas) < 3:
        return {"velas": len(velas), "nota": "historial insuficiente"}
    c = [v["close"] for v in velas]
    precio = c[-1]
    em = {n: S.ema(c, n)[-1] for n in (20, 50, 200) if len(c) >= n}
    macd = [a - b for a, b in zip(S.ema(c, 12), S.ema(c, 26))]
    hist = macd[-1] - S.ema(macd, 9)[-1]
    alt, baj = pivotes(velas)
    if 20 in em and 50 in em:
        tendencia = ("alcista" if precio > em[20] > em[50] else "bajista" if precio < em[20] < em[50] else "lateral")
    else:
        tendencia = "alcista" if c[-1] > c[0] else "bajista"
    var = lambda k: round((precio / c[-1 - k] - 1) * 100, 2) if len(c) > k else None  # noqa: E731
    r = S.rsi(c)
    a = S.atr(velas)
    return {
        "precio": precio, "tendencia": tendencia,
        "ema": {f"ema{n}": round(v, 6) for n, v in em.items()},
        "precio_vs_ema200": None if 200 not in em else ("encima" if precio > em[200] else "debajo"),
        "rsi14": None if r is None else round(r, 1),
        "macd_hist": round(hist, 6), "macd_sesgo": "alcista" if hist > 0 else "bajista",
        "atr14": None if a is None else round(a, 6), "atr14_pct": None if a is None else round(a / precio * 100, 3),
        "max_20": max(v["high"] for v in velas[-20:]), "min_20": min(v["low"] for v in velas[-20:]),
        "vela_anterior": {k: velas[-2][k] for k in ("open", "high", "low", "close")},
        "resistencias_recientes": alt, "soportes_recientes": baj,
        "variacion_pct": {"1": var(1), "5": var(5), "20": var(20)},
        "velas": len(velas),
    }


async def historico(api, sym, granularidad, n, paginas=12):
    """Pide velas hacia atrás por páginas (Deriv limita cuántas devuelve por consulta)."""
    velas = await api.velas(sym, granularidad, n)
    for _ in range(paginas):
        if len(velas) >= n or not velas:
            break
        antes = await api.velas(sym, granularidad, n - len(velas), end=velas[0]["epoch"] - 1)
        antes = [v for v in antes if v["epoch"] < velas[0]["epoch"]]
        if not antes:
            break
        velas = antes + velas
    return velas


async def exportar(api, fecha, carpeta):
    indice = {"generado_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "fecha": fecha,
              "activos": {}, "errores": {}}
    for activo, sym in ACTIVOS.items():
        try:
            series = {}
            for tf, (g, n) in TEMPORALIDADES.items():
                series[tf] = await historico(api, sym, g, n)
            for tf in ("semanal", "mensual", "anual"):
                series[tf] = agregar(series["diario"], tf)
        except Exception as e:  # símbolo no disponible, etc.
            indice["errores"][activo] = f"{type(e).__name__}: {e}"
            continue
        datos = {"activo": activo, "simbolo_deriv": sym, "generado_utc": indice["generado_utc"],
                 "temporalidades": {}}
        for tf, velas in series.items():
            datos["temporalidades"][tf] = {
                "resumen": resumen(velas),
                "ultimas_velas": [{"t": dt.datetime.fromtimestamp(v["epoch"], dt.timezone.utc).strftime("%Y-%m-%d %H:%M"),
                                   **{k: v[k] for k in ("open", "high", "low", "close")}}
                                  for v in velas[-ULTIMAS_VELAS[tf]:]],
            }
        archivo = carpeta / f"{sym}.json"
        archivo.write_text(json.dumps(datos, ensure_ascii=False, indent=1))
        indice["activos"][activo] = {"simbolo": sym, "archivo": str(archivo.relative_to(D.RAIZ.parent)),
                                     "precio": datos["temporalidades"]["15m"]["resumen"].get("precio"),
                                     "tendencias": {tf: datos["temporalidades"][tf]["resumen"].get("tendencia")
                                                    for tf in datos["temporalidades"]}}
    return indice


async def main():
    fecha = dt.datetime.now(D.ZONA).date().isoformat()
    carpeta = D.RAIZ / "datos" / fecha
    carpeta.mkdir(parents=True, exist_ok=True)
    api = D.Deriv(os.environ.get("DERIV_TOKEN", "").strip(), os.environ.get("DERIV_APP_ID", "").strip())
    await api.conectar()
    indice = await exportar(api, fecha, carpeta)
    await api.ws.close()
    (carpeta / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1))
    (D.RAIZ / "datos" / "ultimo.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1))
    print(json.dumps({k: v["tendencias"] for k, v in indice["activos"].items()}, ensure_ascii=False, indent=1))
    print("errores:", indice["errores"])
    return 0 if indice["activos"] else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
