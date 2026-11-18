"""Detector de patrones en gráficas (velas japonesas y figuras chartistas).

detectar(velas) -> lista de {"patron", "tipo", "sesgo", "nivel", "descripcion"} sobre las últimas velas.
eventos(velas)  -> recorre todo el historial y devuelve (indice, patron, sesgo) para medir su fiabilidad.
"""
import scalper as S


def _cuerpo(v):
    return abs(v["close"] - v["open"])


def _rango(v):
    return max(v["high"] - v["low"], 1e-12)


def velas_japonesas(vs, a):
    """Patrones en la última vela (o las dos o tres últimas)."""
    out = []
    v, p = vs[-1], vs[-2]
    sup = v["high"] - max(v["open"], v["close"])
    inf = min(v["open"], v["close"]) - v["low"]
    if _cuerpo(v) <= 0.1 * _rango(v) and _rango(v) > 0.3 * a:
        out.append(("doji", "neutral", "indecisión: cuerpo mínimo"))
    if inf >= 2 * _cuerpo(v) and sup <= 0.5 * _cuerpo(v) + 0.1 * _rango(v) and _rango(v) > 0.6 * a:
        out.append(("martillo", "compra", "mecha inferior larga: rechazo de precios bajos"))
    if sup >= 2 * _cuerpo(v) and inf <= 0.5 * _cuerpo(v) + 0.1 * _rango(v) and _rango(v) > 0.6 * a:
        out.append(("estrella_fugaz", "venta", "mecha superior larga: rechazo de precios altos"))
    if p["close"] < p["open"] and v["close"] > v["open"] and v["close"] >= p["open"] and v["open"] <= p["close"]:
        out.append(("envolvente_alcista", "compra", "la vela alcista envuelve a la bajista anterior"))
    if p["close"] > p["open"] and v["close"] < v["open"] and v["close"] <= p["open"] and v["open"] >= p["close"]:
        out.append(("envolvente_bajista", "venta", "la vela bajista envuelve a la alcista anterior"))
    if v["high"] < p["high"] and v["low"] > p["low"]:
        out.append(("inside_bar", "neutral", "vela interior: compresión, esperar ruptura del rango de la anterior"))
    if len(vs) >= 7 and _rango(v) == min(_rango(x) for x in vs[-7:]):
        out.append(("nr7", "neutral", "rango más estrecho de 7 velas: suele preceder a un movimiento fuerte"))
    if len(vs) >= 3:
        t = vs[-3:]
        if all(x["close"] > x["open"] for x in t) and t[0]["close"] < t[1]["close"] < t[2]["close"] \
                and all(_cuerpo(x) > 0.5 * _rango(x) for x in t):
            out.append(("tres_soldados", "compra", "tres velas alcistas fuertes seguidas"))
        if all(x["close"] < x["open"] for x in t) and t[0]["close"] > t[1]["close"] > t[2]["close"] \
                and all(_cuerpo(x) > 0.5 * _rango(x) for x in t):
            out.append(("tres_cuervos", "venta", "tres velas bajistas fuertes seguidas"))
    return out


def _pivotes(vs, lado=3):
    alt, baj = [], []
    for i in range(lado, len(vs) - lado):
        w = vs[i - lado:i + lado + 1]
        if vs[i]["high"] == max(x["high"] for x in w):
            alt.append(i)
        if vs[i]["low"] == min(x["low"] for x in w):
            baj.append(i)
    return alt, baj


def figuras(vs, a):
    out = []
    c = [v["close"] for v in vs]
    alt, baj = _pivotes(vs)
    precio = c[-1]
    # doble techo / doble suelo: dos giros parecidos (±0.5 ATR), separados >= 5 velas, precio aún cerca
    if len(alt) >= 2 and alt[-1] - alt[-2] >= 5:
        h1, h2 = vs[alt[-2]]["high"], vs[alt[-1]]["high"]
        if abs(h1 - h2) <= 0.5 * a and precio < min(h1, h2) and precio > min(h1, h2) - 3 * a:
            out.append(("doble_techo", "venta", f"dos máximos en ~{max(h1, h2):.6g}", max(h1, h2)))
    if len(baj) >= 2 and baj[-1] - baj[-2] >= 5:
        l1, l2 = vs[baj[-2]]["low"], vs[baj[-1]]["low"]
        if abs(l1 - l2) <= 0.5 * a and precio > max(l1, l2) and precio < max(l1, l2) + 3 * a:
            out.append(("doble_suelo", "compra", f"dos mínimos en ~{min(l1, l2):.6g}", min(l1, l2)))
    # triángulo / compresión: máximos de giro decrecientes y mínimos crecientes
    if len(alt) >= 3 and len(baj) >= 3:
        ha = [vs[i]["high"] for i in alt[-3:]]
        lb = [vs[i]["low"] for i in baj[-3:]]
        if ha[0] > ha[1] > ha[2] and lb[0] < lb[1] < lb[2]:
            out.append(("triangulo", "neutral", f"compresión entre {lb[2]:.6g} y {ha[2]:.6g}: esperar ruptura", None))
    # ruptura del rango de 20 velas
    if len(vs) >= 22:
        alto = max(v["high"] for v in vs[-21:-1])
        bajo = min(v["low"] for v in vs[-21:-1])
        if precio > alto:
            out.append(("ruptura_maximo_20", "compra", f"cierra por encima del máximo de 20 velas ({alto:.6g})", alto))
        if precio < bajo:
            out.append(("ruptura_minimo_20", "venta", f"cierra por debajo del mínimo de 20 velas ({bajo:.6g})", bajo))
    # divergencias de RSI en los dos últimos giros
    rs = rsi_serie(c)
    if len(alt) >= 2 and None not in (rs[alt[-1]], rs[alt[-2]]):
        i1, i2 = alt[-2], alt[-1]
        if vs[i2]["high"] > vs[i1]["high"] and rs[i2] < rs[i1] - 2 and len(vs) - i2 <= 10:
            out.append(("divergencia_bajista", "venta", "precio hace máximo más alto y el RSI más bajo", vs[i2]["high"]))
    if len(baj) >= 2 and None not in (rs[baj[-1]], rs[baj[-2]]):
        i1, i2 = baj[-2], baj[-1]
        if vs[i2]["low"] < vs[i1]["low"] and rs[i2] > rs[i1] + 2 and len(vs) - i2 <= 10:
            out.append(("divergencia_alcista", "compra", "precio hace mínimo más bajo y el RSI más alto", vs[i2]["low"]))
    return out


def rsi_serie(c, n=14):
    """RSI de Wilder para cada vela en O(n); None mientras no hay datos suficientes."""
    out = [None] * len(c)
    if len(c) <= n:
        return out
    g = [max(c[i] - c[i - 1], 0) for i in range(1, len(c))]
    p = [max(c[i - 1] - c[i], 0) for i in range(1, len(c))]
    ag, ap = sum(g[:n]) / n, sum(p[:n]) / n
    out[n] = 100.0 if ap == 0 else 100 - 100 / (1 + ag / ap)
    for i in range(n, len(g)):
        ag, ap = (ag * (n - 1) + g[i]) / n, (ap * (n - 1) + p[i]) / n
        out[i + 1] = 100.0 if ap == 0 else 100 - 100 / (1 + ag / ap)
    return out


def detectar(velas):
    """Patrones activos al final de la serie."""
    if len(velas) < 30:
        return []
    vs = velas[-120:]
    a = S.atr(vs) or _rango(vs[-1])
    res = [{"patron": p, "tipo": "vela", "sesgo": s, "nivel": None, "descripcion": d} for p, s, d in velas_japonesas(vs, a)]
    res += [{"patron": p, "tipo": "figura", "sesgo": s, "nivel": n, "descripcion": d} for p, s, d, n in figuras(vs, a)]
    return res


def eventos(velas, ventana=120, paso=1):
    """Todas las apariciones de patrones con sesgo en el historial: [(indice, patron, sesgo)]."""
    out = []
    for i in range(max(30, ventana // 2), len(velas), paso):
        for d in detectar(velas[max(0, i + 1 - ventana):i + 1]):
            if d["sesgo"] in ("compra", "venta"):
                out.append((i, d["patron"], d["sesgo"]))
    return out
