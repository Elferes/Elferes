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


# ----------------------------------------------------------------------------------------------- nuevas (v2)
def rsi2_reversion(velas, cfg, sesgo=None):
    """Connors: RSI(2) extremo (< 10 o > 90) → reversión de corto plazo. Stop y objetivo a 1 ATR."""
    if len(velas) < 60:
        return None
    c = [v["close"] for v in velas]
    r2, a = S.rsi(c, 2), S.atr(velas)
    if r2 is None or not a:
        return None
    p = c[-1]
    if r2 < 10:
        return _senal("rsi2_reversion", "compra", p, p - a, p + a, a, r2, velas, sesgo)
    if r2 > 90:
        return _senal("rsi2_reversion", "venta", p, p + a, p - a, a, r2, velas, sesgo)
    return None


def donchian(velas, cfg, sesgo=None, n=20):
    """Tortugas: cierre por encima del máximo (o debajo del mínimo) de las n velas anteriores."""
    if len(velas) < 60:
        return None
    c, e9, e21, e50, r, a = _base(velas)
    if not a:
        return None
    prev = velas[-n - 1:-1]
    alto, bajo, p = max(v["high"] for v in prev), min(v["low"] for v in prev), c[-1]
    if p > alto and c[-2] <= alto:
        return _senal("donchian", "compra", p, p - cfg["atr_stop"] * a, p + cfg["atr_objetivo"] * a, a, r, velas, sesgo)
    if p < bajo and c[-2] >= bajo:
        return _senal("donchian", "venta", p, p + cfg["atr_stop"] * a, p - cfg["atr_objetivo"] * a, a, r, velas, sesgo)
    return None


def _keltner(velas, n=20, k=1.5):
    c = [v["close"] for v in velas]
    m = S.ema(c, n)[-1]
    a = S.atr(velas[-(n + 15):]) or 0
    return m - k * a, m, m + k * a


def squeeze(velas, cfg, sesgo=None):
    """Bollinger dentro de Keltner (compresión) en la vela anterior y ruptura del canal de Keltner ahora."""
    if len(velas) < 60:
        return None
    c, e9, e21, e50, r, a = _base(velas)
    if not a:
        return None
    bi, _, bs = bollinger(c[:-1])
    ki, _, ks = _keltner(velas[:-1])
    if not (bs < ks and bi > ki):
        return None
    ki2, _, ks2 = _keltner(velas)
    p = c[-1]
    if p > ks2:
        return _senal("squeeze", "compra", p, p - cfg["atr_stop"] * a, p + cfg["atr_objetivo"] * a, a, r, velas, sesgo)
    if p < ki2:
        return _senal("squeeze", "venta", p, p + cfg["atr_stop"] * a, p - cfg["atr_objetivo"] * a, a, r, velas, sesgo)
    return None


def inside_bar(velas, cfg, sesgo=None):
    """Vela madre + vela interior; entrada cuando la vela actual cierra fuera del rango de la madre."""
    if len(velas) < 60:
        return None
    c, e9, e21, e50, r, a = _base(velas)
    if not a:
        return None
    m, ib, v = velas[-3], velas[-2], velas[-1]
    if not (ib["high"] < m["high"] and ib["low"] > m["low"]) or m["high"] - m["low"] > 2.5 * a:
        return None
    p = v["close"]
    if p > m["high"]:
        stop = m["low"]
        return _senal("inside_bar", "compra", p, stop, p + 1.5 * (p - stop), a, r, velas, sesgo)
    if p < m["low"]:
        stop = m["high"]
        return _senal("inside_bar", "venta", p, stop, p - 1.5 * (stop - p), a, r, velas, sesgo)
    return None


def macd_giro(velas, cfg, sesgo=None):
    """El histograma del MACD cruza cero a favor de la EMA50."""
    if len(velas) < 60:
        return None
    c, e9, e21, e50, r, a = _base(velas)
    if not a:
        return None
    macd = [x - y for x, y in zip(S.ema(c, 12), S.ema(c, 26))]
    sig = S.ema(macd, 9)
    h1, h0 = macd[-1] - sig[-1], macd[-2] - sig[-2]
    p = c[-1]
    if h0 <= 0 < h1 and p > e50[-1]:
        return _senal("macd_giro", "compra", p, p - cfg["atr_stop"] * a, p + cfg["atr_objetivo"] * a, a, r, velas, sesgo)
    if h0 >= 0 > h1 and p < e50[-1]:
        return _senal("macd_giro", "venta", p, p + cfg["atr_stop"] * a, p - cfg["atr_objetivo"] * a, a, r, velas, sesgo)
    return None


def _figura(velas, nombres):
    import patrones as P
    vs = velas[-120:]
    a = S.atr(vs)
    if not a:
        return None, None
    for nombre, sesgo_f, _, nivel in P.figuras(vs, a):
        if nombre in nombres and nivel is not None:
            return (nombre, sesgo_f, nivel), a
    return None, a


def doble_techo_suelo(velas, cfg, sesgo=None):
    """Doble suelo → compra con stop bajo el nivel; doble techo → venta. Objetivo 1.5R."""
    if len(velas) < 60:
        return None
    fig, a = _figura(velas, ("doble_suelo", "doble_techo"))
    if not fig:
        return None
    _, dirc, nivel = fig
    p = velas[-1]["close"]
    stop = nivel - 0.3 * a if dirc == "compra" else nivel + 0.3 * a
    tp = p + 1.5 * (p - stop) if dirc == "compra" else p - 1.5 * (stop - p)
    return _senal("doble_techo_suelo", dirc, p, stop, tp, a, None, velas, sesgo)


def divergencia_rsi(velas, cfg, sesgo=None):
    """Divergencia de RSI en los dos últimos giros → operar el giro. Stop tras el extremo, objetivo 1.5R."""
    if len(velas) < 60:
        return None
    fig, a = _figura(velas, ("divergencia_alcista", "divergencia_bajista"))
    if not fig:
        return None
    _, dirc, nivel = fig
    p = velas[-1]["close"]
    stop = nivel - 0.3 * a if dirc == "compra" else nivel + 0.3 * a
    tp = p + 1.5 * (p - stop) if dirc == "compra" else p - 1.5 * (stop - p)
    return _senal("divergencia_rsi", dirc, p, stop, tp, a, None, velas, sesgo)


def ruptura_asiatica(velas, cfg, sesgo=None):
    """Rango de la sesión asiática (00–07 UTC) del día; ruptura entre 07 y 11 UTC. Stop en el medio del rango."""
    if len(velas) < 60:
        return None
    hoy = dt.datetime.fromtimestamp(velas[-1]["epoch"], dt.timezone.utc)
    if not 7 <= hoy.hour < 11:
        return None
    asia = [v for v in velas if dt.datetime.fromtimestamp(v["epoch"], dt.timezone.utc).date() == hoy.date()
            and dt.datetime.fromtimestamp(v["epoch"], dt.timezone.utc).hour < 7]
    if len(asia) < 4:
        return None
    a = S.atr(velas)
    alto, bajo = max(v["high"] for v in asia), min(v["low"] for v in asia)
    medio, p, p0 = (alto + bajo) / 2, velas[-1]["close"], velas[-2]["close"]
    if not a or alto - bajo > 4 * a:
        return None
    if p > alto >= p0:
        return _senal("ruptura_asiatica", "compra", p, medio, p + 1.5 * (p - medio), a, None, velas, sesgo)
    if p < bajo <= p0:
        return _senal("ruptura_asiatica", "venta", p, medio, p - 1.5 * (medio - p), a, None, velas, sesgo)
    return None


def pin_nivel(velas, cfg, sesgo=None, n=30):
    """Martillo en el mínimo de n velas (o estrella fugaz en el máximo). Stop tras la mecha, objetivo 1.5R."""
    if len(velas) < 60:
        return None
    import patrones as P
    a = S.atr(velas)
    if not a:
        return None
    nombres = [x[0] for x in P.velas_japonesas(velas[-10:], a)]
    v, zona = velas[-1], velas[-n:]
    if "martillo" in nombres and v["low"] <= min(x["low"] for x in zona) + 0.2 * a:
        stop = v["low"] - 0.2 * a
        return _senal("pin_nivel", "compra", v["close"], stop, v["close"] + 1.5 * (v["close"] - stop), a, None, velas, sesgo)
    if "estrella_fugaz" in nombres and v["high"] >= max(x["high"] for x in zona) - 0.2 * a:
        stop = v["high"] + 0.2 * a
        return _senal("pin_nivel", "venta", v["close"], stop, v["close"] - 1.5 * (stop - v["close"]), a, None, velas, sesgo)
    return None


# ----------------------------------------------------------------------------------------------- fusión
def rasgos(velas):
    """Rasgos de la ventana que usan los filtros (calculados igual en backtest y en vivo)."""
    c = [v["close"] for v in velas]
    tr = [max(v["high"] - v["low"], abs(v["high"] - velas[i - 1]["close"]), abs(v["low"] - velas[i - 1]["close"]))
          for i, v in enumerate(velas) if i > 0]
    atrs = [sum(tr[i - 13:i + 1]) / 14 for i in range(13, len(tr))]
    ult = sorted(atrs[-100:])
    return {"sma200": sum(c[-200:]) / 200 if len(c) >= 200 else None,
            "atr": atrs[-1] if atrs else None,
            "atr_mediana": ult[len(ult) // 2] if len(ult) >= 50 else None,
            "hora": dt.datetime.fromtimestamp(velas[-1]["epoch"], dt.timezone.utc).hour}


FILTROS = {
    "tendencia200": lambda s, f: f["sma200"] is not None and (s["direccion"] == "compra") == (s["entrada"] > f["sma200"]),
    "sesion_lny": lambda s, f: 7 <= f["hora"] < 16,
    "sesion_ny": lambda s, f: 13 <= f["hora"] < 20,
    "vol_alta": lambda s, f: bool(f["atr_mediana"]) and f["atr"] > f["atr_mediana"],
    "vol_baja": lambda s, f: bool(f["atr_mediana"]) and f["atr"] <= f["atr_mediana"],
}
SALIDAS = {"base": None, "obj1r": 1.0, "obj1.5r": 1.5, "obj2r": 2.0}


def aplicar(s, filtros, salida, f):
    """Aplica filtros y salida a una señal base (sin modificar la original)."""
    if not s:
        return None
    for nombre in filtros:
        if not FILTROS[nombre](s, f):
            return None
    s = dict(s)
    k = SALIDAS.get(salida)
    if k:
        riesgo = abs(s["entrada"] - s["stop"])
        s["tp"] = s["entrada"] + k * riesgo if s["direccion"] == "compra" else s["entrada"] - k * riesgo
    return s


def nombre_variante(base, filtros=(), salida="base"):
    return f"{base}|{','.join(filtros)}|{salida}" if (filtros or salida != "base") else base


def obtener(nombre):
    """'base' o 'base|filtro1,filtro2|salida' → función(velas, cfg, sesgo) o None."""
    partes = nombre.split("|")
    base = ESTRATEGIAS.get(partes[0])
    filtros = [x for x in (partes[1].split(",") if len(partes) > 1 and partes[1] else [])]
    salida = partes[2] if len(partes) > 2 else "base"
    if not base or any(x not in FILTROS for x in filtros) or salida not in SALIDAS:
        return None
    if not filtros and salida == "base":
        return base

    def f(velas, cfg, sesgo=None):
        s = aplicar(base(velas, cfg, None), filtros, salida, rasgos(velas))
        if s and sesgo and s["direccion"] != sesgo:
            return None
        if s:
            s["estrategia"] = nombre
        return s
    return f


ESTRATEGIAS = {
    "tendencia_retroceso": tendencia_retroceso,
    "ruptura_rango": ruptura_rango,
    "reversion_bollinger": reversion_bollinger,
    "cruce_ema": cruce_ema,
    "envolvente_nivel": envolvente_nivel,
    "rsi2_reversion": rsi2_reversion,
    "donchian": donchian,
    "squeeze": squeeze,
    "inside_bar": inside_bar,
    "macd_giro": macd_giro,
    "doble_techo_suelo": doble_techo_suelo,
    "divergencia_rsi": divergencia_rsi,
    "ruptura_asiatica": ruptura_asiatica,
    "pin_nivel": pin_nivel,
}


def buscar_senal(velas, cfg, sesgo=None, activas=None):
    """Prueba las estrategias activas en orden y devuelve la primera señal."""
    for nombre in activas or cfg.get("estrategias") or ["tendencia_retroceso"]:
        f = obtener(nombre)
        s = f(velas, cfg, sesgo) if f else None
        if s:
            return s
    return None
