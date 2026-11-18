#!/usr/bin/env python3
"""Backtest de estrategias y fiabilidad de patrones con historial (Yahoo Finance desde GitHub Actions).

Para cada activo y temporalidad:
  * simula cada estrategia de estrategias.py vela a vela: entra al cierre de la vela de señal, sale por stop,
    objetivo o tiempo (max_velas). Si stop y objetivo caen en la misma vela, cuenta el STOP (conservador).
    Descuenta un coste (spread y comisión) en R.
  * separa el historial en entrenamiento (70 %) y prueba (30 %) para evitar engañarse con el sobreajuste.
  * mide la fiabilidad de cada patrón de patrones.py: % de veces que el precio avanzó 1 ATR a favor
    antes que 1 ATR en contra en las 12 velas siguientes.
Salida: trading/estrategias/resultados/AAAA-MM-DD.json y trading/estrategias/RANKING.md

Uso: python3 trading/ejecutor/backtest.py [--activos EUR/USD,BTC/USD] [--temporalidades 5m,15m,1h]
"""
import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import deriv_ejecutor as D  # noqa: E402
import estrategias as E  # noqa: E402
import exportar_datos as X  # noqa: E402
import patrones as P  # noqa: E402
import scalper as S  # noqa: E402

ACTIVOS = {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X", "XAU/USD": "GC=F",
           "BTC/USD": "BTC-USD", "US 500": "^GSPC"}
TEMPORALIDADES = {"5m": ("5m", "60d"), "15m": ("15m", "60d"), "1h": ("1h", "730d")}
COSTE_PCT = {"EUR/USD": 0.00012, "GBP/USD": 0.00015, "USD/JPY": 0.00012, "XAU/USD": 0.00025,
             "BTC/USD": 0.0006, "US 500": 0.0002}  # spread + comisión aproximados, en fracción del precio
VENTANA = 120


def simular(velas, estrategia, cfg, coste_pct, max_velas, ventana=None):
    w = ventana or VENTANA
    return simular_fn(velas, lambda i: estrategia(velas[max(0, i + 1 - w):i + 1], cfg), coste_pct, max_velas)


def simular_fn(velas, senal_en, coste_pct, max_velas, inicio=60):
    """Simula operando la señal senal_en(i) al cierre de la vela i (una operación a la vez)."""
    ops, i, n = [], inicio, len(velas)
    while i < n - 1:
        s = senal_en(i)
        if not s:
            i += 1
            continue
        largo = s["direccion"] == "compra"
        riesgo = abs(s["entrada"] - s["stop"])
        if riesgo <= 0:
            i += 1
            continue
        resultado, salida_i = None, min(i + max_velas, n - 1)
        for j in range(i + 1, min(i + max_velas, n - 1) + 1):
            v = velas[j]
            toca_stop = v["low"] <= s["stop"] if largo else v["high"] >= s["stop"]
            toca_tp = v["high"] >= s["tp"] if largo else v["low"] <= s["tp"]
            if toca_stop:
                resultado, salida_i = -1.0, j
                break
            if toca_tp:
                resultado, salida_i = abs(s["tp"] - s["entrada"]) / riesgo, j
                break
        if resultado is None:  # cierre por tiempo
            cierre = velas[salida_i]["close"]
            resultado = ((cierre - s["entrada"]) if largo else (s["entrada"] - cierre)) / riesgo
        resultado -= coste_pct * s["entrada"] / riesgo
        ops.append({"i": i, "r": round(resultado, 3), "direccion": s["direccion"],
                    "hora": dt.datetime.fromtimestamp(velas[i]["epoch"], dt.timezone.utc).hour})
        i = salida_i + 1  # una operación a la vez
    return ops


def metricas(ops):
    if not ops:
        return {"operaciones": 0}
    rs = [o["r"] for o in ops]
    gan = [r for r in rs if r > 0]
    per = [-r for r in rs if r <= 0]
    eq, pico, dd = 0.0, 0.0, 0.0
    for r in rs:
        eq += r
        pico = max(pico, eq)
        dd = max(dd, pico - eq)
    media = sum(rs) / len(rs)
    desv = (sum((r - media) ** 2 for r in rs) / max(1, len(rs) - 1)) ** 0.5
    t = media / (desv / len(rs) ** 0.5) if desv > 0 else 0.0
    return {"operaciones": len(rs), "acierto_pct": round(100 * len(gan) / len(rs), 1), "t_stat": round(t, 2),
            "esperanza_r": round(sum(rs) / len(rs), 3), "total_r": round(sum(rs), 2),
            "profit_factor": round(sum(gan) / sum(per), 2) if per and sum(per) > 0 else None,
            "max_drawdown_r": round(dd, 2)}


def fiabilidad_patrones(velas, horizonte=12):
    stats = {}
    for i, patron, sesgo in P.eventos(velas, paso=1):
        a = S.atr(velas[max(0, i - 30):i + 1])
        if not a or i + 1 >= len(velas):
            continue
        p0, gano = velas[i]["close"], None
        for v in velas[i + 1:i + 1 + horizonte]:
            arriba, abajo = v["high"] >= p0 + a, v["low"] <= p0 - a
            if arriba and abajo:
                gano = False  # conservador
                break
            if arriba or abajo:
                gano = arriba if sesgo == "compra" else abajo
                break
        if gano is None:
            continue
        s = stats.setdefault(patron, {"casos": 0, "aciertos": 0, "sesgo": sesgo})
        s["casos"] += 1
        s["aciertos"] += int(gano)
    for s in stats.values():
        s["fiabilidad_pct"] = round(100 * s["aciertos"] / s["casos"], 1)
    return stats


def veredicto(prueba):
    m = prueba
    if m.get("operaciones", 0) < 20:
        return "pocos datos"
    if m["esperanza_r"] >= 0.10 and (m.get("profit_factor") or 0) >= 1.2:
        return "APTA"
    if m["esperanza_r"] > 0:
        return "marginal"
    return "descartar"


def correr(activos, temporalidades, cfg):
    hoy = dt.datetime.now(D.ZONA).date().isoformat()
    res = {"generado_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "fecha": hoy,
           "parametros_version": cfg.get("version_parametros"), "resultados": [], "patrones": {}, "errores": {}}
    for activo in activos:
        for tf in temporalidades:
            intervalo, rango = TEMPORALIDADES[tf]
            try:
                velas = X.yahoo(ACTIVOS[activo], intervalo, rango)
            except Exception as e:
                res["errores"][f"{activo} {tf}"] = f"{type(e).__name__}: {e}"
                continue
            corte = int(len(velas) * 0.7)
            max_velas = {"5m": 6, "15m": 8, "1h": 12}[tf]
            for nombre, f in E.ESTRATEGIAS.items():
                t0 = time.time()
                ops = simular(velas, f, cfg, COSTE_PCT[activo], max_velas)
                ent, pru = [o for o in ops if o["i"] < corte], [o for o in ops if o["i"] >= corte]
                fila = {"activo": activo, "temporalidad": tf, "estrategia": nombre, "velas": len(velas),
                        "desde": dt.datetime.fromtimestamp(velas[0]["epoch"], dt.timezone.utc).strftime("%Y-%m-%d"),
                        "entrenamiento": metricas(ent), "prueba": metricas(pru), "total": metricas(ops),
                        "segundos": round(time.time() - t0, 1)}
                fila["veredicto"] = veredicto(fila["prueba"])
                res["resultados"].append(fila)
                print(f"{activo:8} {tf:4} {nombre:20} prueba={fila['prueba']} -> {fila['veredicto']}", flush=True)
            res["patrones"][f"{activo} {tf}"] = fiabilidad_patrones(velas)
    return res


def ranking_md(res):
    lin = [f"# Ranking de estrategias y patrones — {res['fecha']}", "",
           "Generado por `backtest.py`. **Prueba** = el 30 % más reciente del historial, no usado para elegir nada.",
           "**APTA**: ≥ 20 operaciones en prueba, esperanza ≥ +0.10 R y profit factor ≥ 1.2 (ya con costes).", "",
           "## Estrategias (ordenadas por esperanza en la prueba)", "",
           "| Activo | TF | Estrategia | Ops prueba | Acierto | Esperanza (R) | Profit factor | Máx. DD (R) | Veredicto |",
           "|---|---|---|---|---|---|---|---|---|"]
    filas = sorted(res["resultados"], key=lambda f: f["prueba"].get("esperanza_r", -9), reverse=True)
    for f in filas:
        p = f["prueba"]
        lin.append(f"| {f['activo']} | {f['temporalidad']} | {f['estrategia']} | {p.get('operaciones', 0)} | "
                   f"{p.get('acierto_pct', '—')} % | {p.get('esperanza_r', '—')} | {p.get('profit_factor', '—')} | "
                   f"{p.get('max_drawdown_r', '—')} | {f['veredicto']} |")
    lin += ["", "## Patrones más fiables (≥ 30 casos; avanzar 1 ATR a favor antes que 1 ATR en contra, 12 velas)", "",
            "| Activo y TF | Patrón | Sesgo | Casos | Fiabilidad |", "|---|---|---|---|---|"]
    pats = [(k, p, s) for k, d in res["patrones"].items() for p, s in d.items() if s["casos"] >= 30]
    for k, p, s in sorted(pats, key=lambda x: x[2]["fiabilidad_pct"], reverse=True)[:40]:
        lin.append(f"| {k} | {p} | {s['sesgo']} | {s['casos']} | {s['fiabilidad_pct']} % |")
    if res["errores"]:
        lin += ["", "## Errores", ""] + [f"- {k}: {v}" for k, v in res["errores"].items()]
    return "\n".join(lin) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--activos", default=",".join(ACTIVOS))
    ap.add_argument("--temporalidades", default=",".join(TEMPORALIDADES))
    a = ap.parse_args()
    cfg = S.preparar_config(S.CONFIG, capital=100.0)
    res = correr([x for x in a.activos.split(",") if x in ACTIVOS],
                 [x for x in a.temporalidades.split(",") if x in TEMPORALIDADES], cfg)
    carpeta = D.RAIZ / "estrategias" / "resultados"
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / f"{res['fecha']}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    (D.RAIZ / "estrategias" / "RANKING.md").write_text(ranking_md(res))
    print(f"\nAPTAS: {[(f['activo'], f['temporalidad'], f['estrategia']) for f in res['resultados'] if f['veredicto'] == 'APTA']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
