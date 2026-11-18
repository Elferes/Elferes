"""Biblioteca de estrategias del scalper.

Cada estrategia recibe velas CERRADAS (antiguas → recientes, dicts con epoch/open/high/low/close),
la configuración y un sesgo opcional ("compra"/"venta") y devuelve None o una señal:
    {"estrategia", "direccion", "entrada", "stop", "tp", "atr", "rsi", "contexto"}
Reglas comunes: stop y objetivo en el lado correcto, R/B >= 1.0, y respeta el sesgo si lo hay.
El investigador-estrategias activa o desactiva estrategias en trading/aprendizaje/parametros.json ("estrategias").
"""
import datetime as dt

import scalper as S


def bollinger(c, n=20, k=2.0):
    v = c[-n:]
    m = sum(v) / len(v)
    d = (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5
    return m - k * d, m, m + k * d


def _base(velas):
    c = [v["close"] for v in velas]
    return c, S.ema(c, 9), S.ema(c, 21), S.ema(c, 50), S.rsi(c), S.atr(velas)


def _senal(nombre, direccion, entrada, stop, tp, a, r, velas, sesgo, extra=None):
    if sesgo and sesgo != direccion:
        return None
    largo = direccion == "compra"
    if (largo and not stop < entrada < tp) or (not largo and not tp < entrada < stop):
        return None
    if abs(tp - entrada) < abs(entrada - stop):  # R/B mínimo 1
        return None
    ctx = {"hora_utc": dt.datetime.fromtimestamp(velas[-1]["epoch"], dt.timezone.utc).strftime("%H:%M")}
    ctx.update(extra or {})
    return {"estrategia": nombre, "direccion": direccion, "entrada": entrada, "stop": stop, "tp": tp,
            "atr": a, "rsi": None if r is None else round(r, 1), "contexto": ctx}


def tendencia_retroceso(velas, cfg, sesgo=None):
    """Tendencia (EMA 9/21/50) + retroceso a la EMA21 + vela de reanudación (la estrategia original)."""
    s = S.senal(velas, cfg, sesgo)
    if s:
        s["estrategia"] = "tendencia_retroceso"
    return s


def ruptura_rango(velas, cfg, sesgo=None, n=12):
    """Compresión de n velas (rango < 2.5 ATR) y ruptura con cuerpo fuerte. Stop en el medio del rango."""
    if len(velas) < 60:
        return None
    c, e9, e21, e50, r, a = _base(velas)
    if not a:
        return None
    caja = velas[-n - 1:-1]
    alto, bajo = max(v["high"] for v in caja), min(v["low"] for v in caja)
    if alto - bajo > 2.5 * a:
        return None
    v = velas[-1]
    cuerpo = abs(v["close"] - v["open"])
    medio = (alto + bajo) / 2
    if v["close"] > alto and cuerpo > 0.5 * a:
        riesgo = v["close"] - medio
        return _senal("ruptura_rango", "compra", v["close"], medio, v["close"] + cfg["atr_objetivo"] / cfg["atr_stop"] * riesgo,
                      a, r, velas, sesgo, {"rango_atr": round((alto - bajo) / a, 2)})
    if v["close"] < bajo and cuerpo > 0.5 * a:
        riesgo = medio - v["close"]
        return _senal("ruptura_rango", "venta", v["close"], medio, v["close"] - cfg["atr_objetivo"] / cfg["atr_stop"] * riesgo,
                      a, r, velas, sesgo, {"rango_atr": round((alto - bajo) / a, 2)})
    return None


def reversion_bollinger(velas, cfg, sesgo=None):
    """Mercado lateral (EMA50 plana): la vela anterior cierra fuera de Bollinger con RSI extremo y la actual vuelve
    dentro. Objetivo: la media de Bollinger. Stop: más allá del extremo + 0.3 ATR."""
    if len(velas) < 60:
        return None
    c, e9, e21, e50, r, a = _base(velas)
    if not a or r is None:
        return None
    if abs(e50[-1] - e50[-11]) > 1.0 * a:  # pendiente de la EMA50 en 10 velas: tendencia, no aplica
        return None
    inf0, med, sup0 = bollinger(c[:-1])
    p, v = velas[-2], velas[-1]
    rsi_prev = S.rsi(c[:-1])
    if p["close"] < inf0 and rsi_prev is not None and rsi_prev < 32 and v["close"] > inf0 and v["close"] > v["open"]:
        stop = min(p["low"], v["low"]) - 0.3 * a
        return _senal("reversion_bollinger", "compra", v["close"], stop, med, a, r, velas, sesgo)
    if p["close"] > sup0 and rsi_prev is not None and rsi_prev > 68 and v["close"] < sup0 and v["close"] < v["open"]:
        stop = max(p["high"], v["high"]) + 0.3 * a
        return _senal("reversion_bollinger", "venta", v["close"], stop, med, a, r, velas, sesgo)
    return None


def cruce_ema(velas, cfg, sesgo=None):
    """EMA9 cruza la EMA21 a favor de la EMA50, con RSI confirmando (> 50 compra, < 50 venta)."""
    if len(velas) < 60:
        return None
    c, e9, e21, e50, r, a = _base(velas)
    if not a or r is None:
        return None
    precio = c[-1]
    if e9[-2] <= e21[-2] and e9[-1] > e21[-1] and precio > e50[-1] and 50 < r < 70:
        return _senal("cruce_ema", "compra", precio, precio - cfg["atr_stop"] * a, precio + cfg["atr_objetivo"] * a,
                      a, r, velas, sesgo)
    if e9[-2] >= e21[-2] and e9[-1] < e21[-1] and precio < e50[-1] and 30 < r < 50:
        return _senal("cruce_ema", "venta", precio, precio + cfg["atr_stop"] * a, precio - cfg["atr_objetivo"] * a,
                      a, r, velas, sesgo)
    return None


def envolvente_nivel(velas, cfg, sesgo=None, n=30):
    """Envolvente alcista en el mínimo de las últimas n velas (o bajista en el máximo). Stop tras la mecha."""
    if len(velas) < 60:
        return None
    c, e9, e21, e50, r, a = _base(velas)
    if not a:
        return None
    p, v = velas[-2], velas[-1]
    zona = velas[-n:]
    minimo, maximo = min(x["low"] for x in zona), max(x["high"] for x in zona)
    alcista = p["close"] < p["open"] and v["close"] > v["open"] and v["close"] >= p["open"] and v["open"] <= p["close"]
    bajista = p["close"] > p["open"] and v["close"] < v["open"] and v["close"] <= p["open"] and v["open"] >= p["close"]
    if alcista and min(p["low"], v["low"]) <= minimo + 0.3 * a:
        stop = min(p["low"], v["low"]) - 0.2 * a
        riesgo = v["close"] - stop
        return _senal("envolvente_nivel", "compra", v["close"], stop, v["close"] + 1.5 * riesgo, a, r, velas, sesgo)
    if bajista and max(p["high"], v["high"]) >= maximo - 0.3 * a:
        stop = max(p["high"], v["high"]) + 0.2 * a
        riesgo = stop - v["close"]
        return _senal("envolvente_nivel", "venta", v["close"], stop, v["close"] - 1.5 * riesgo, a, r, velas, sesgo)
    return None


ESTRATEGIAS = {
    "tendencia_retroceso": tendencia_retroceso,
    "ruptura_rango": ruptura_rango,
    "reversion_bollinger": reversion_bollinger,
    "cruce_ema": cruce_ema,
    "envolvente_nivel": envolvente_nivel,
}


def buscar_senal(velas, cfg, sesgo=None, activas=None):
    """Prueba las estrategias activas en orden y devuelve la primera señal."""
    for nombre in activas or cfg.get("estrategias") or ["tendencia_retroceso"]:
        f = ESTRATEGIAS.get(nombre)
        s = f(velas, cfg, sesgo) if f else None
        if s:
            return s
    return None
