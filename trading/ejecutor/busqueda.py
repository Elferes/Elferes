#!/usr/bin/env python3
"""Búsqueda sistemática de estrategias rentables, con protecciones contra el autoengaño.

Para cada activo × temporalidad × estrategia base:
  1. Calcula la señal base en cada vela (ventana de VENTANA velas, igual que en vivo).
  2. Prueba variantes = base + filtros (tendencia SMA200, sesión, volatilidad) + salida (1R, 1.5R, 2R).
  3. ELIGE la mejor variante SOLO con el 70 % antiguo (entrenamiento).
  4. La juzga en el 30 % reciente (prueba ciega), exigiendo que las dos mitades de la prueba ganen.
  5. Repite TODO con los precios desordenados al azar (permutación de rendimientos): lo que "gane" ahí es suerte, y
     da la tasa de falsos positivos esperada.
  6. Junta las ganadoras en una cartera y mide su curva en la prueba ciega.
Salida: trading/estrategias/busqueda/AAAA-MM-DD.json y trading/estrategias/BUSQUEDA.md
"""
import argparse
import datetime as dt
import itertools
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import backtest as B  # noqa: E402
import deriv_ejecutor as D  # noqa: E402
import estrategias as E  # noqa: E402
import exportar_datos as X  # noqa: E402
import scalper as S  # noqa: E402

VENTANA = 250
ACTIVOS = {"EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X", "AUD/USD": "AUDUSD=X",
           "XAU/USD": "GC=F", "BTC/USD": "BTC-USD", "US 500": "^GSPC", "US Tech 100": "^NDX"}
COSTE_PCT = dict(B.COSTE_PCT, **{"AUD/USD": 0.00015, "US Tech 100": 0.0002})
MAX_VELAS = {"15m": 8, "1h": 12, "4h": 10, "1d": 10}
FILTROS_COMBOS = [(), ("tendencia200",), ("sesion_lny",), ("sesion_ny",), ("vol_alta",), ("vol_baja",),
                  ("tendencia200", "sesion_lny"), ("tendencia200", "vol_alta"), ("tendencia200", "vol_baja")]
CRITERIO = {"min_ops_prueba": 30, "min_esperanza": 0.10, "min_pf": 1.2, "min_ops_entreno": 50, "min_esp_entreno": 0.05,
            "min_t_prueba": 2.0, "min_t_entreno": 1.5}


def velas_tf(activo, tf):
    if tf == "1d":
        return X.yahoo(ACTIVOS[activo], "1d", "max")[-6000:]
    if tf == "15m":
        return X.yahoo(ACTIVOS[activo], "15m", "60d")
    h = X.yahoo(ACTIVOS[activo], "1h", "730d")
    if tf == "1h":
        return h
    grupos = {}
    for v in h:  # 4h agregada desde 1h
        k = v["epoch"] // 14400
        g = grupos.get(k)
        if g is None:
            grupos[k] = dict(v, epoch=k * 14400)
        else:
            g["high"], g["low"], g["close"] = max(g["high"], v["high"]), min(g["low"], v["low"]), v["close"]
    return [grupos[k] for k in sorted(grupos)]


def permutar(velas, semilla):
    """Mismos rendimientos y rangos de vela, pero en orden aleatorio: destruye cualquier patrón real."""
    rnd = random.Random(semilla)
    piezas = []
    for i in range(1, len(velas)):
        p0, v = velas[i - 1]["close"], velas[i]
        piezas.append((v["open"] / p0, v["high"] / p0, v["low"] / p0, v["close"] / p0))
    rnd.shuffle(piezas)
    out, p = [dict(velas[0])], velas[0]["close"]
    for (o, h, l, c), v in zip(piezas, velas[1:]):
        out.append({"epoch": v["epoch"], "open": p * o, "high": p * h, "low": p * l, "close": p * c})
        p = p * c
    return out


def evaluar_serie(velas, activo, tf, cfg, registrar_variantes=False):
    n, corte = len(velas), int(len(velas) * 0.7)
    t0 = time.time()
    ventanas = lambda i: velas[max(0, i + 1 - VENTANA):i + 1]  # noqa: E731
    feats = [None] * n
    for i in range(60, n):
        feats[i] = E.rasgos(ventanas(i))
    elegidas, probadas = [], 0
    for base, fbase in E.ESTRATEGIAS.items():
        sigs = [None] * n
        for i in range(60, n):
            sigs[i] = fbase(ventanas(i), cfg, None)
        if not any(sigs):
            continue
        mejor = None
        for filtros, salida in itertools.product(FILTROS_COMBOS, E.SALIDAS):
            probadas += 1
            ops = B.simular_fn(velas, lambda i: E.aplicar(sigs[i], filtros, salida, feats[i]),
                               COSTE_PCT[activo], MAX_VELAS[tf])
            ent = B.metricas([o for o in ops if o["i"] < corte])
            if ent.get("operaciones", 0) >= CRITERIO["min_ops_entreno"] and \
                    (mejor is None or ent["esperanza_r"] > mejor["entrenamiento"]["esperanza_r"]):
                mejor = {"filtros": filtros, "salida": salida, "entrenamiento": ent, "ops": ops}
        if not mejor:
            continue
        pru_ops = [o for o in mejor["ops"] if o["i"] >= corte]
        mitad = corte + (n - corte) // 2
        pru = B.metricas(pru_ops)
        m1 = B.metricas([o for o in pru_ops if o["i"] < mitad])
        m2 = B.metricas([o for o in pru_ops if o["i"] >= mitad])
        ok = (pru.get("operaciones", 0) >= CRITERIO["min_ops_prueba"]
              and pru["esperanza_r"] >= CRITERIO["min_esperanza"] and (pru.get("profit_factor") or 0) >= CRITERIO["min_pf"]
              and mejor["entrenamiento"]["esperanza_r"] >= CRITERIO["min_esp_entreno"]
              and pru.get("t_stat", 0) >= CRITERIO["min_t_prueba"]
              and mejor["entrenamiento"].get("t_stat", 0) >= CRITERIO["min_t_entreno"]
              and m1.get("total_r", 0) > 0 and m2.get("total_r", 0) > 0)
        elegidas.append({
            "activo": activo, "tf": tf, "base": base, "variante": E.nombre_variante(base, mejor["filtros"], mejor["salida"]),
            "entrenamiento": mejor["entrenamiento"], "prueba": pru, "prueba_mitad1": m1, "prueba_mitad2": m2,
            "aprobada": ok, "ops_prueba": [(velas[o["i"]]["epoch"], o["r"]) for o in pru_ops] if ok else []})
    return elegidas, probadas, round(time.time() - t0, 1)


def senales_serie(velas, cfg):
    """Señales base de todas las estrategias y rasgos, vela a vela (lo caro, se calcula una vez)."""
    n = len(velas)
    ventanas = lambda i: velas[max(0, i + 1 - VENTANA):i + 1]  # noqa: E731
    feats = [None] * n
    for i in range(60, n):
        feats[i] = E.rasgos(ventanas(i))
    sigs = {}
    for base, fbase in E.ESTRATEGIAS.items():
        sigs[base] = [None] * n
        for i in range(60, n):
            sigs[base][i] = fbase(ventanas(i), cfg, None)
    return feats, sigs


def evaluar_agrupado(series, tf):
    """Una misma regla en TODOS los activos a la vez. series: {activo: (velas, feats, sigs)}.

    Elige la variante con el entrenamiento conjunto y la juzga con la prueba conjunta. Así una regla tiene
    que funcionar en muchos mercados (más creíble) y acumula muchas más operaciones (más poder estadístico).
    """
    elegidas, probadas = [], 0
    for base in E.ESTRATEGIAS:
        mejor = None
        for filtros, salida in itertools.product(FILTROS_COMBOS, E.SALIDAS):
            probadas += 1
            ent, pru, m1, m2, por_activo = [], [], [], [], {}
            for activo, (velas, feats, sigs) in series.items():
                n = len(velas)
                corte, mitad = int(n * 0.7), int(n * 0.7) + (n - int(n * 0.7)) // 2
                sg = sigs[base]
                ops = B.simular_fn(velas, lambda i: E.aplicar(sg[i], filtros, salida, feats[i]),
                                   COSTE_PCT[activo], MAX_VELAS[tf])
                for o in ops:
                    (ent if o["i"] < corte else pru).append(o)
                    if o["i"] >= corte:
                        (m1 if o["i"] < mitad else m2).append(o)
                        por_activo.setdefault(activo, []).append(o)
            me = B.metricas(ent)
            if me.get("operaciones", 0) >= 100 and (mejor is None or me["esperanza_r"] > mejor["ent"]["esperanza_r"]):
                mejor = {"filtros": filtros, "salida": salida, "ent": me, "pru": pru, "m1": m1, "m2": m2,
                         "por_activo": por_activo}
        if not mejor:
            continue
        pru = B.metricas(mejor["pru"])
        m1, m2 = B.metricas(mejor["m1"]), B.metricas(mejor["m2"])
        ok = (pru.get("operaciones", 0) >= CRITERIO["min_ops_prueba"]
              and pru["esperanza_r"] >= CRITERIO["min_esperanza"] and (pru.get("profit_factor") or 0) >= CRITERIO["min_pf"]
              and mejor["ent"]["esperanza_r"] >= CRITERIO["min_esp_entreno"]
              and pru.get("t_stat", 0) >= CRITERIO["min_t_prueba"] and mejor["ent"].get("t_stat", 0) >= CRITERIO["min_t_entreno"]
              and m1.get("total_r", 0) > 0 and m2.get("total_r", 0) > 0)
        elegidas.append({"activo": "TODOS", "tf": tf, "base": base,
                         "variante": E.nombre_variante(base, mejor["filtros"], mejor["salida"]),
                         "entrenamiento": mejor["ent"], "prueba": pru, "prueba_mitad1": m1, "prueba_mitad2": m2,
                         "prueba_por_activo": {a: B.metricas(o) for a, o in mejor["por_activo"].items()},
                         "aprobada": ok, "ops_prueba": []})
    return elegidas, probadas


def cartera(aprobadas):
    ops = sorted((t, r) for a in aprobadas for t, r in a["ops_prueba"])
    if not ops:
        return {}
    m = B.metricas([{"r": r} for _, r in ops])
    dias = max(1, (ops[-1][0] - ops[0][0]) / 86400)
    m["dias"] = round(dias)
    m["r_por_dia"] = round(m["total_r"] / dias, 3)
    m["usd_por_dia_cuenta_100_riesgo_1pct"] = round(m["r_por_dia"] * 1.0, 2)
    return m


def informe(res):
    c = res["criterio"]
    l = [f"# Búsqueda de estrategias — {res['fecha']}", "",
         f"- Variantes probadas: **{res['variantes_probadas']}** (base × filtros × salida) en {len(res['series'])} series.",
         f"- Protocolo: se elige la mejor variante solo con el 70 % antiguo; se aprueba si en el 30 % reciente tiene "
         f"≥ {c['min_ops_prueba']} operaciones, esperanza ≥ +{c['min_esperanza']} R, PF ≥ {c['min_pf']}, entrenamiento ≥ "
         f"+{c['min_esp_entreno']} R, **significancia estadística t ≥ {c['min_t_prueba']} en la prueba** (≈ menos de 5 % de "
         f"probabilidad de ser suerte) y t ≥ {c['min_t_entreno']} en entrenamiento, y **las dos mitades de la prueba en "
         f"positivo**. Costes incluidos.",
         f"- **Aprobadas con datos reales: {len(res['aprobadas'])}** · **Aprobadas con precios desordenados (suerte): "
         f"{res['falsos_positivos']}** de {res['candidatas_permutadas']} candidatas.", ""]
    real = len(res["aprobadas"]) / max(1, res["candidatas_reales"])
    azar = res["falsos_positivos"] / max(1, res["candidatas_permutadas"])
    l += [f"Tasa de aprobación real {real:.1%} frente a {azar:.1%} por azar. "
          + ("**Hay más ganadoras que las esperables por suerte: señal de ventaja real.**" if real > 2 * azar + 0.01
             else "**No hay más ganadoras que las esperables por suerte: tomar con mucha cautela.**"), "",
          "## Estrategias aprobadas (prueba ciega)", "",
          "| Activo | TF | Variante | Entreno (ops, R, t) | Prueba ops | Acierto | Esperanza | t | PF | Máx DD | Mitades (R) |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in sorted(res["aprobadas"], key=lambda x: x["prueba"]["esperanza_r"], reverse=True):
        p, e = a["prueba"], a["entrenamiento"]
        l.append(f"| {a['activo']} | {a['tf']} | `{a['variante']}` | {e['operaciones']}, {e['esperanza_r']:+}, {e['t_stat']} | "
                 f"{p['operaciones']} | {p['acierto_pct']} % | **{p['esperanza_r']:+}** | {p['t_stat']} | {p['profit_factor']} | "
                 f"{p['max_drawdown_r']} | {a['prueba_mitad1'].get('total_r')}, {a['prueba_mitad2'].get('total_r')} |")
    if res.get("modo") == "agrupado":
        l += ["", "## Desglose por activo en la prueba (agrupado)", ""]
        for a in sorted(res["candidatas"], key=lambda x: x["prueba"].get("esperanza_r", -9), reverse=True)[:8]:
            pa = a.get("prueba_por_activo", {})
            l.append(f"- `{a['variante']}` ({a['tf']}, {'APROBADA' if a['aprobada'] else 'no aprobada'}): " + ", ".join(
                f"{k} {v.get('operaciones', 0)} ops {v.get('esperanza_r', 0):+}R" for k, v in pa.items()))
    cart = res["cartera"]
    if cart:
        l += ["", "## Cartera de todas las aprobadas (prueba ciega)", "",
              f"{cart['operaciones']} operaciones en {cart['dias']} días · acierto {cart['acierto_pct']} % · "
              f"esperanza {cart['esperanza_r']:+} R · total {cart['total_r']:+} R · máx. drawdown {cart['max_drawdown_r']} R · "
              f"**{cart['r_por_dia']:+} R/día ≈ {cart['usd_por_dia_cuenta_100_riesgo_1pct']:+} USD/día con 100 USD y 1 % de riesgo**."]
    l += ["", "## Mejores candidatas no aprobadas (las 15 con mejor prueba)", "",
          "| Activo | TF | Variante | Prueba ops | Esperanza | t | PF | Motivo |", "|---|---|---|---|---|---|---|---|"]
    no = sorted([x for x in res["candidatas"] if not x["aprobada"]], key=lambda x: x["prueba"].get("esperanza_r", -9),
                reverse=True)[:15]
    for a in no:
        p = a["prueba"]
        motivo = ("pocas ops" if p.get("operaciones", 0) < c["min_ops_prueba"] else
                  "esperanza/PF bajos" if p.get("esperanza_r", 0) < c["min_esperanza"] else
                  "no significativa (t bajo)" if p.get("t_stat", 0) < c["min_t_prueba"] else "una mitad o el entreno flojos")
        l.append(f"| {a['activo']} | {a['tf']} | `{a['variante']}` | {p.get('operaciones', 0)} | {p.get('esperanza_r', '—')} | "
                 f"{p.get('t_stat', '—')} | "
                 f"{p.get('profit_factor', '—')} | {motivo} |")
    return "\n".join(l) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--activos", default=",".join(ACTIVOS))
    ap.add_argument("--temporalidades", default="15m,1h,4h")
    ap.add_argument("--sin-permutacion", action="store_true")
    ap.add_argument("--agrupado", action="store_true", help="una regla en todos los activos a la vez")
    a = ap.parse_args()
    cfg = S.preparar_config(S.CONFIG, capital=100.0)
    res = {"fecha": dt.datetime.now(D.ZONA).date().isoformat(), "criterio": CRITERIO, "series": [],
           "candidatas": [], "aprobadas": [], "variantes_probadas": 0, "falsos_positivos": 0,
           "candidatas_permutadas": 0, "errores": {}}
    if a.agrupado:
        res["modo"] = "agrupado"
        for tf in [x for x in a.temporalidades.split(",") if x in MAX_VELAS]:
            reales, azar = {}, {}
            for activo in [x for x in a.activos.split(",") if x in ACTIVOS]:
                try:
                    velas = velas_tf(activo, tf)
                except Exception as e:
                    res["errores"][f"{activo} {tf}"] = f"{type(e).__name__}: {e}"
                    continue
                t0 = time.time()
                reales[activo] = (velas, *senales_serie(velas, cfg))
                if not a.sin_permutacion:
                    pv = permutar(velas, hash((activo, tf)) & 0xffff)
                    azar[activo] = (pv, *senales_serie(pv, cfg))
                res["series"].append({"activo": activo, "tf": tf, "velas": len(velas), "segundos": round(time.time() - t0, 1)})
                print(f"{activo:11} {tf:3} {len(velas):6} velas listas", flush=True)
            el, n = evaluar_agrupado(reales, tf)
            res["variantes_probadas"] += n
            res["candidatas"] += el
            res["aprobadas"] += [x for x in el if x["aprobada"]]
            msg = f"== {tf}: aprobadas={[x['variante'] for x in el if x['aprobada']]}"
            if azar:
                elp, _ = evaluar_agrupado(azar, tf)
                res["candidatas_permutadas"] += len(elp)
                res["falsos_positivos"] += sum(x["aprobada"] for x in elp)
                msg += f" | azar aprobadas={sum(x['aprobada'] for x in elp)}/{len(elp)}"
            print(msg, flush=True)
    for activo in ([] if a.agrupado else [x for x in a.activos.split(",") if x in ACTIVOS]):
        for tf in [x for x in a.temporalidades.split(",") if x in MAX_VELAS]:
            try:
                velas = velas_tf(activo, tf)
            except Exception as e:
                res["errores"][f"{activo} {tf}"] = f"{type(e).__name__}: {e}"
                continue
            el, n, seg = evaluar_serie(velas, activo, tf, cfg)
            res["series"].append({"activo": activo, "tf": tf, "velas": len(velas), "segundos": seg})
            res["variantes_probadas"] += n
            res["candidatas"] += el
            res["aprobadas"] += [x for x in el if x["aprobada"]]
            msg = f"{activo:11} {tf:3} {len(velas):6} velas {seg:6}s aprobadas={[x['variante'] for x in el if x['aprobada']]}"
            if not a.sin_permutacion:
                elp, _, _ = evaluar_serie(permutar(velas, hash((activo, tf)) & 0xffff), activo, tf, cfg)
                res["candidatas_permutadas"] += len(elp)
                res["falsos_positivos"] += sum(x["aprobada"] for x in elp)
                msg += f" | azar aprobadas={sum(x['aprobada'] for x in elp)}/{len(elp)}"
            print(msg, flush=True)
    res["candidatas_reales"] = len(res["candidatas"])
    res["cartera"] = cartera(res["aprobadas"])
    carpeta = D.RAIZ / "estrategias" / "busqueda"
    carpeta.mkdir(parents=True, exist_ok=True)
    sufijo = "-agrupado" if a.agrupado else ""
    (carpeta / f"{res['fecha']}{sufijo}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    (D.RAIZ / "estrategias" / f"BUSQUEDA{sufijo.upper()}.md").write_text(informe(res))
    print(informe(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
