#!/usr/bin/env python3
"""Scalper intradía en Deriv (operaciones rápidas, velas de 5 min). Solo cuenta DEMO salvo permiso.

Estrategia (tendencia + retroceso), evaluada en cada vela de 5 min cerrada:
  * Tendencia: precio > EMA50 y EMA9 > EMA21 → solo compras; al revés → solo ventas.
  * Retroceso: alguna de las 3 velas anteriores tocó la EMA21.
  * Gatillo: la vela cerrada vuelve a cerrar a favor de la tendencia, por encima (compra) o debajo (venta) de la EMA9,
    con RSI14 entre 45 y 70 (compra) o entre 30 y 55 (venta).
  * Stop = 1.2 × ATR14 y objetivo = 1.8 × ATR14 (1.5R). Si en 30 min no toca ninguno, se cierra.
  * Si el plan del día trae dirección para ese activo, solo opera en esa dirección.
  * No abre 15 min antes ni después de los eventos de alto impacto del plan ("eventos_alto_impacto_utc").

Gestión de riesgo (CONFIG):
  * riesgo por operación 0.25 % del saldo, máximo 2 abiertas y 6 en el día, 1 por activo;
  * para el día si pierde 1 % o 3 operaciones seguidas, o si gana la META_DIARIA_USD (30 por defecto).

Uso:
  python3 trading/ejecutor/scalper.py --modo verificar   # conecta y calcula señales, sin operar
  python3 trading/ejecutor/scalper.py --modo ejecutar
"""
import argparse
import asyncio
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import deriv_ejecutor as D  # noqa: E402

CONFIG = {
    "simbolos": {"EUR/USD": "frxEURUSD", "GBP/USD": "frxGBPUSD", "XAU/USD": "frxXAUUSD", "BTC/USD": "cryBTCUSD"},
    "riesgo_pct": 0.25,
    "max_abiertas": 2,
    "max_operaciones_dia": 6,
    "perdida_max_dia_pct": 1.0,
    "max_perdidas_seguidas": 3,
    "meta_diaria_usd": float(os.environ.get("META_DIARIA_USD", "30") or 30),
    "granularidad": 300,           # velas de 5 min
    "atr_stop": 1.2,
    "atr_objetivo": 1.8,
    "max_velas_abierta": 6,        # 30 min
    "bloqueo_noticias_min": 15,
    "fin_utc": "16:30",            # fin de la ventana Londres–Nueva York
    "intervalo_s": 15,
    "limite_job_s": 5 * 3600 + 40 * 60,
    "stake_minimo": 1.0,
}


# --------------------------------------------------------------------------- indicadores
def ema(v, n):
    k, out = 2 / (n + 1), []
    for x in v:
        out.append(x if not out else x * k + out[-1] * (1 - k))
    return out


def rsi(c, n=14):
    if len(c) <= n:
        return None
    g = [max(c[i] - c[i - 1], 0) for i in range(1, len(c))]
    p = [max(c[i - 1] - c[i], 0) for i in range(1, len(c))]
    ag, ap = sum(g[:n]) / n, sum(p[:n]) / n
    for i in range(n, len(g)):
        ag, ap = (ag * (n - 1) + g[i]) / n, (ap * (n - 1) + p[i]) / n
    return 100.0 if ap == 0 else 100 - 100 / (1 + ag / ap)


def atr(velas, n=14):
    tr = [max(v["high"] - v["low"], abs(v["high"] - velas[i - 1]["close"]), abs(v["low"] - velas[i - 1]["close"]))
          for i, v in enumerate(velas) if i > 0]
    if len(tr) < n:
        return None
    a = sum(tr[:n]) / n
    for x in tr[n:]:
        a = (a * (n - 1) + x) / n
    return a


def senal(velas, cfg, sesgo=None):
    """velas cerradas (antiguas → recientes). Devuelve dict de operación o None."""
    if len(velas) < 60:
        return None
    c = [v["close"] for v in velas]
    e9, e21, e50 = ema(c, 9), ema(c, 21), ema(c, 50)
    r, a = rsi(c), atr(velas)
    if r is None or not a:
        return None
    v, precio = velas[-1], c[-1]
    toco21 = lambda k: velas[k]["low"] <= e21[k] <= velas[k]["high"]  # noqa: E731
    retroceso = any(toco21(k) for k in (-2, -3, -4))
    largo = precio > e50[-1] and e9[-1] > e21[-1] and v["close"] > v["open"] and precio > e9[-1] and 45 <= r <= 70
    corto = precio < e50[-1] and e9[-1] < e21[-1] and v["close"] < v["open"] and precio < e9[-1] and 30 <= r <= 55
    if not retroceso or not (largo or corto):
        return None
    direccion = "compra" if largo else "venta"
    if sesgo and sesgo != direccion:
        return None
    s = 1 if largo else -1
    return {"direccion": direccion, "entrada": precio, "stop": precio - s * cfg["atr_stop"] * a,
            "tp": precio + s * cfg["atr_objetivo"] * a, "atr": a, "rsi": round(r, 1)}


def en_bloqueo(ahora, eventos, minutos):
    return any(abs((ahora - D.parse_utc(e)).total_seconds()) <= minutos * 60 for e in eventos)


# --------------------------------------------------------------------------- ejecución
async def abrir(api, simbolo, activo, s, cfg, reg):
    tipo = "MULTUP" if s["direccion"] == "compra" else "MULTDOWN"
    precio = await api.precio(simbolo)
    largo = s["direccion"] == "compra"
    if (largo and not s["stop"] < precio < s["tp"]) or (not largo and not s["tp"] < precio < s["stop"]):
        reg.evento(f"{activo}: el precio ({precio}) ya salió de la zona de la señal, no se entra")
        return None
    riesgo_usd = await api.saldo() * cfg["riesgo_pct"] / 100
    tam = D.dimensionar(precio, s["stop"], riesgo_usd, await api.multiplicadores(simbolo, tipo), cfg["stake_minimo"] * 2)
    if not tam:
        reg.evento(f"{activo}: señal {s['direccion']} pero no se puede dimensionar (riesgo {riesgo_usd:.2f})")
        return None
    m, stake = tam
    sl = min(D.monto(stake, m, precio, s["stop"]), stake)
    tp = D.monto(stake, m, precio, s["tp"])
    try:
        c = await api.comprar(simbolo, tipo, stake, m, sl, tp)
    except D.DerivError as e:
        reg.evento(f"{activo}: no se pudo abrir ({e})")
        return None
    t = {"activo": activo, "simbolo": simbolo, "tipo": tipo, "contract_id": c["contract_id"], "precio_ref": precio,
         "stop": s["stop"], "tp": s["tp"], "multiplicador": m, "stake": stake, "sl_usd": sl, "tp_usd": tp,
         "rsi": s["rsi"], "abierta_epoch": time.time(), "abierto": True, "profit": 0.0}
    reg.datos["operaciones"].append(t)
    reg.evento(f"{activo}: ABIERTA {s['direccion'].upper()} x{m} stake {stake} | entrada ~{precio:.5g} "
               f"stop {s['stop']:.5g} objetivo {s['tp']:.5g} | riesgo {sl:.2f} / premio {tp:.2f} USD")
    return t


async def vigilar(api, t, cfg, reg, forzar=False):
    c = await api.contrato(t["contract_id"])
    vencida = time.time() - t["abierta_epoch"] > cfg["max_velas_abierta"] * cfg["granularidad"]
    if not c.get("is_sold") and (forzar or vencida):
        await api.vender(t["contract_id"])
        c = await api.contrato(t["contract_id"])
        reg.evento(f"{t['activo']}: cerrada por {'fin de jornada' if forzar else 'tiempo (30 min)'}")
    if c.get("is_sold"):
        t["abierto"], t["profit"] = False, float(c.get("profit", 0))
        reg.evento(f"{t['activo']}: resultado {t['profit']:+.2f} USD")
    return t["abierto"]


async def correr(plan, modo, cfg):
    fecha = plan["fecha"]
    reg = D.Registro(fecha)
    reg.ruta = D.RAIZ / "ejecuciones" / f"{fecha}-scalping.json"
    token = os.environ.get("DERIV_TOKEN", "").strip()
    if not token:
        reg.evento("Falta el secreto DERIV_TOKEN")
        return 1
    api = D.Deriv(token, os.environ.get("DERIV_APP_ID", "").strip())
    try:
        cuenta = await api.conectar()
    except Exception as e:
        reg.evento(f"No se pudo conectar a Deriv: {type(e).__name__}: {e}")
        return 1
    reg.evento(f"Scalper conectado: cuenta {'DEMO' if cuenta.get('is_virtual') else 'REAL'} {cuenta.get('loginid')}")
    if not cuenta.get("is_virtual") and os.environ.get("DERIV_PERMITIR_REAL", "").lower() != "si":
        reg.evento("La cuenta NO es demo: no se opera")
        return 1

    sesgos = {o.get("simbolo_deriv"): ("compra" if D.es_largo(o.get("direccion", "")) else "venta")
              for o in plan.get("operaciones", []) if o.get("simbolo_deriv")}
    eventos = plan.get("eventos_alto_impacto_utc", [])
    simbolos = {}
    for activo, sym in cfg["simbolos"].items():
        try:
            ok = await api.multiplicadores(sym, "MULTUP")
        except D.DerivError as e:
            ok, _ = [], reg.evento(f"{activo}: error al consultar ({e})")
        if ok:
            simbolos[activo] = sym
    reg.evento(f"Activos: {', '.join(simbolos) or 'ninguno'} | sesgos del plan: {sesgos or 'ninguno'} | "
               f"eventos: {eventos or 'ninguno'} | meta {cfg['meta_diaria_usd']} USD")

    if modo == "verificar":
        for activo, sym in simbolos.items():
            v = await api.velas(sym, cfg["granularidad"], 120)
            s = senal(v, cfg, sesgos.get(sym))
            reg.evento(f"{activo}: {len(v)} velas de 5 min, señal ahora: {s['direccion'] if s else 'ninguna'}")
        reg.evento("Verificación del scalper terminada")
        await api.ws.close()
        return 0

    saldo0 = await api.saldo()
    fin = dt.datetime.combine(dt.datetime.now(dt.timezone.utc).date(),
                              dt.time.fromisoformat(cfg["fin_utc"]), dt.timezone.utc)
    inicio, abiertas, ultima, total, seguidas, realizado = time.time(), [], {}, 0, 0, 0.0
    motivo = None
    while True:
        ahora = dt.datetime.now(dt.timezone.utc)
        for t in list(abiertas):
            if not await vigilar(api, t, cfg, reg):
                abiertas.remove(t)
                realizado += t["profit"]
                seguidas = seguidas + 1 if t["profit"] < 0 else 0
        if realizado >= cfg["meta_diaria_usd"]:
            motivo = f"meta diaria alcanzada ({realizado:+.2f} USD)"
        elif realizado <= -saldo0 * cfg["perdida_max_dia_pct"] / 100:
            motivo = f"pérdida máxima del día ({realizado:+.2f} USD)"
        elif seguidas >= cfg["max_perdidas_seguidas"]:
            motivo = f"{seguidas} pérdidas seguidas"
        elif total >= cfg["max_operaciones_dia"]:
            motivo = "máximo de operaciones del día"
        elif ahora >= fin or time.time() - inicio > cfg["limite_job_s"]:
            motivo = "fin de la ventana de trading"
        if motivo:
            if ahora >= fin or time.time() - inicio > cfg["limite_job_s"]:
                for t in abiertas:
                    await vigilar(api, t, cfg, reg, forzar=True)
                    realizado += t["profit"]
                abiertas = []
            if not abiertas:
                break
        elif not en_bloqueo(ahora, eventos, cfg["bloqueo_noticias_min"]) and len(abiertas) < cfg["max_abiertas"]:
            for activo, sym in simbolos.items():
                if len(abiertas) >= cfg["max_abiertas"] or any(t["simbolo"] == sym for t in abiertas):
                    continue
                v = await api.velas(sym, cfg["granularidad"], 120)
                if not v or v[-1]["epoch"] == ultima.get(sym):
                    continue
                ultima[sym] = v[-1]["epoch"]
                s = senal(v, cfg, sesgos.get(sym))
                if s:
                    t = await abrir(api, sym, activo, s, cfg, reg)
                    if t:
                        abiertas.append(t)
                        total += 1
        await asyncio.sleep(cfg["intervalo_s"])

    gan = [t for t in reg.datos["operaciones"] if t["profit"] > 0]
    reg.datos["resumen"] = {"modo": modo, "operaciones": len(reg.datos["operaciones"]), "ganadoras": len(gan),
                            "resultado_usd": round(realizado, 2), "motivo_fin": motivo}
    reg.evento(f"Fin del scalping ({motivo}): {len(reg.datos['operaciones'])} operaciones, "
               f"{len(gan)} ganadoras, resultado {realizado:+.2f} USD")
    await api.ws.close()
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modo", choices=["verificar", "ejecutar"], default="verificar")
    ap.add_argument("--fecha", default="")
    a = ap.parse_args()
    fecha = a.fecha or dt.datetime.now(D.ZONA).date().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        sys.exit("fecha inválida")
    ruta = D.RAIZ / "planes" / f"{fecha}.json"
    plan = json.loads(ruta.read_text()) if ruta.exists() else {"fecha": fecha, "operaciones": []}
    return asyncio.run(correr(plan, a.modo, CONFIG))


if __name__ == "__main__":
    sys.exit(main())
