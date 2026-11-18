#!/usr/bin/env python3
"""Indicadores técnicos para trading intradía (solo librería estándar).

Uso:
    python3 trading/indicadores.py AAPL BTC-USD EURUSD=X
    python3 trading/indicadores.py --intervalo 1h --rango 1mo NVDA

Símbolos (formato Yahoo Finance):
    Acciones: AAPL, NVDA, TSLA, SPY      Cripto: BTC-USD, ETH-USD, SOL-USD
    Divisas:  EURUSD=X, GBPUSD=X, USDJPY=X, USDMXN=X     Oro: GC=F

Calcula: EMA 9/21/50/200, RSI 14, MACD (12,26,9), ATR 14, Bandas de Bollinger,
pivotes clásicos del día anterior y máximos/mínimos recientes (soportes y resistencias).
Si la red bloquea Yahoo Finance, el agente debe obtener estos datos con búsquedas web.
"""
import argparse
import json
import sys
import urllib.request

URL = "https://query1.finance.yahoo.com/v8/finance/chart/{s}?range={r}&interval={i}"


def descargar(simbolo, rango, intervalo):
    req = urllib.request.Request(URL.format(s=simbolo, r=rango, i=intervalo),
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.load(resp)["chart"]["result"][0]
    q = data["indicators"]["quote"][0]
    velas = [(t, o, h, l, c) for t, o, h, l, c in
             zip(data["timestamp"], q["open"], q["high"], q["low"], q["close"])
             if None not in (o, h, l, c)]
    return velas


def ema(valores, n):
    k, out = 2 / (n + 1), []
    for v in valores:
        out.append(v if not out else v * k + out[-1] * (1 - k))
    return out


def rsi(cierres, n=14):
    if len(cierres) <= n:
        return None
    ganancias = [max(cierres[i] - cierres[i - 1], 0) for i in range(1, len(cierres))]
    perdidas = [max(cierres[i - 1] - cierres[i], 0) for i in range(1, len(cierres))]
    g, p = sum(ganancias[:n]) / n, sum(perdidas[:n]) / n
    for i in range(n, len(ganancias)):
        g = (g * (n - 1) + ganancias[i]) / n
        p = (p * (n - 1) + perdidas[i]) / n
    return 100.0 if p == 0 else 100 - 100 / (1 + g / p)


def atr(velas, n=14):
    trs = [max(h - l, abs(h - velas[i - 1][4]), abs(l - velas[i - 1][4]))
           for i, (_, _, h, l, _) in enumerate(velas) if i > 0]
    if len(trs) < n:
        return None
    a = sum(trs[:n]) / n
    for tr in trs[n:]:
        a = (a * (n - 1) + tr) / n
    return a


def analizar(simbolo, rango, intervalo):
    velas = descargar(simbolo, rango, intervalo)
    diarias = descargar(simbolo, "3mo", "1d")
    cierres = [v[4] for v in velas]
    precio = cierres[-1]

    macd_linea = [a - b for a, b in zip(ema(cierres, 12), ema(cierres, 26))]
    senal = ema(macd_linea, 9)
    ult20 = cierres[-20:]
    media20 = sum(ult20) / len(ult20)
    desv = (sum((c - media20) ** 2 for c in ult20) / len(ult20)) ** 0.5

    # Pivotes clásicos con la última vela diaria cerrada
    _, _, h, l, c = diarias[-2]
    pp = (h + l + c) / 3
    emas = {n: ema(cierres, n)[-1] for n in (9, 21, 50, 200) if len(cierres) >= n}

    tendencia = "alcista" if emas.get(21, precio) > emas.get(50, precio) and precio > emas.get(21, precio) \
        else "bajista" if emas.get(21, precio) < emas.get(50, precio) and precio < emas.get(21, precio) \
        else "lateral"

    r = lambda x: None if x is None else round(x, 6 if precio < 10 else 2)
    return {
        "simbolo": simbolo,
        "intervalo": intervalo,
        "precio": r(precio),
        "tendencia": tendencia,
        "ema": {f"ema{n}": r(v) for n, v in emas.items()},
        "rsi14": r(rsi(cierres)),
        "macd": {"linea": r(macd_linea[-1]), "senal": r(senal[-1]),
                 "histograma": r(macd_linea[-1] - senal[-1])},
        "atr14": r(atr(velas)),
        "atr14_diario": r(atr(diarias)),
        "bollinger": {"superior": r(media20 + 2 * desv), "media": r(media20),
                      "inferior": r(media20 - 2 * desv)},
        "pivotes": {"R2": r(pp + (h - l)), "R1": r(2 * pp - l), "PP": r(pp),
                    "S1": r(2 * pp - h), "S2": r(pp - (h - l))},
        "max_reciente": r(max(v[2] for v in velas[-50:])),
        "min_reciente": r(min(v[3] for v in velas[-50:])),
        "max_dia_anterior": r(h), "min_dia_anterior": r(l),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("simbolos", nargs="+")
    ap.add_argument("--intervalo", default="1h", help="5m, 15m, 1h, 1d (por defecto 1h)")
    ap.add_argument("--rango", default="1mo", help="5d, 1mo, 3mo (por defecto 1mo)")
    args = ap.parse_args()
    fallos = 0
    for s in args.simbolos:
        try:
            print(json.dumps(analizar(s, args.rango, args.intervalo), ensure_ascii=False, indent=2))
        except Exception as e:  # red bloqueada, símbolo inválido, etc.
            fallos += 1
            print(json.dumps({"simbolo": s, "error": str(e),
                              "accion": "obtener datos con WebSearch"}, ensure_ascii=False))
    sys.exit(1 if fallos == len(args.simbolos) else 0)


if __name__ == "__main__":
    main()
