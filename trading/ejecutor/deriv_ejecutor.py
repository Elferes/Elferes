#!/usr/bin/env python3
"""Ejecutor automático del plan diario en Deriv (solo cuenta DEMO salvo permiso explícito).

Lee trading/planes/AAAA-MM-DD.json (lo escribe el orquestador cada mañana), espera la
condición de entrada de cada operación con velas de 15 min de Deriv y abre contratos
Multiplier con stop loss y take profit ya colocados en el servidor de Deriv.

Gestión por operación:
  * Se abren DOS contratos con media posición cada uno: A sale en TP1, B sale en TP2.
  * Cuando A cobra TP1, si el precio vuelve a la entrada se cierra B (stop a "break-even").
  * Riesgo total por operación = riesgo_pct del saldo (1% por defecto).
  * Todo se cierra a la hora `cerrar_antes_utc` o al acercarse el límite del job de GitHub.
  * Freno diario: si la pérdida realizada llega a perdida_max_dia_pct (3%), se cierra todo y para.

Variables de entorno:
  DERIV_TOKEN           token de Deriv (obligatorio). Si empieza por "pat_" se usa la API nueva
                        (api.derivws.com, con App ID + OTP); si no, la API antigua (ws.derivws.com).
  DERIV_APP_ID          App ID de Deriv. API nueva: el de tu app registrada en developers.deriv.com
                        (obligatorio). API antigua: por defecto 1089.
  DERIV_PERMITIR_REAL   "si" para permitir una cuenta real (por defecto se rechaza)

Uso:
  python3 trading/ejecutor/deriv_ejecutor.py --modo verificar     # conecta y comprueba, sin operar
  python3 trading/ejecutor/deriv_ejecutor.py --modo ejecutar      # opera el plan de hoy
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
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[1]  # carpeta trading/
WS_URL = "wss://ws.derivws.com/websockets/v3?app_id={app_id}"  # API antigua
REST_URL = "https://api.derivws.com/trading/v1/options"         # API nueva (tokens pat_)
ZONA = ZoneInfo("America/Bogota")
GATILLOS = {"mercado", "ruptura_arriba", "ruptura_abajo", "retesteo_arriba", "retesteo_abajo"}

CONFIG = {
    "riesgo_pct": 1.0,            # % del saldo arriesgado por operación
    "max_operaciones": 3,         # operaciones abiertas a la vez como máximo
    "perdida_max_dia_pct": 3.0,   # freno diario
    "rb_minimo_tp2": 1.5,         # R/B mínimo hasta TP2 con el precio real de entrada
    "tolerancia_toque": 0.0003,   # 0.03 %: cuánto cerca del nivel cuenta como "tocado"
    "granularidad": 900,          # velas de 15 min
    "intervalo_s": 20,            # cada cuánto revisar
    "limite_job_s": 5 * 3600 + 40 * 60,  # GitHub corta a las 6 h; cerramos antes
    "stake_minimo": 1.0,
}


# --------------------------------------------------------------------------- lógica pura
def es_largo(direccion):
    return direccion.lower() in ("compra", "long", "comprar", "buy")


def rb(direccion, entrada, stop, tp):
    riesgo = (entrada - stop) if es_largo(direccion) else (stop - entrada)
    premio = (tp - entrada) if es_largo(direccion) else (entrada - tp)
    return None if riesgo <= 0 else premio / riesgo


def dimensionar(entrada, stop, riesgo_usd, multiplicadores, stake_minimo=1.0):
    """Elige multiplicador y stake para que tocar el stop cueste ~riesgo_usd.

    Ganancia/pérdida de un Multiplier = stake * m * variación% del precio.
    Deriv exige stop_loss <= stake, por eso m <= entrada / |entrada - stop|.
    Devuelve (multiplicador, stake_total) o None si no es posible.
    """
    d = abs(entrada - stop) / entrada
    if d <= 0 or riesgo_usd <= 0:
        return None
    nocional = riesgo_usd / d
    validos = [m for m in sorted(multiplicadores) if m <= 1 / d]
    if not validos:
        return None
    m = validos[-1]  # el mayor permitido = menos capital inmovilizado
    stake = round(nocional / m, 2)
    if stake / 2 < stake_minimo:
        return None
    return m, stake


def monto(stake, m, entrada, precio):
    return round(stake * m * abs(precio - entrada) / entrada, 2)


def validar_operacion(op):
    req = ["activo", "simbolo_deriv", "direccion", "gatillo", "nivel", "stop", "tp1", "tp2",
           "valido_hasta_utc", "cerrar_antes_utc"]
    faltan = [k for k in req if k not in op]
    if faltan:
        return f"faltan campos {faltan}"
    if op["gatillo"] not in GATILLOS:
        return f"gatillo desconocido {op['gatillo']}"
    n, s, t1, t2 = op["nivel"], op["stop"], op["tp1"], op["tp2"]
    ok = (s < n < t1 <= t2) if es_largo(op["direccion"]) else (s > n > t1 >= t2)
    if not ok:
        return "niveles incoherentes con la dirección (stop / nivel / tp1 / tp2)"
    return None


def evaluar_gatillo(op, velas, estado, tolerancia):
    """velas: lista de dicts {epoch, open, high, low, close} ya CERRADAS, en orden.

    estado guarda 'tocado' y 'ultima_epoch' entre llamadas. Devuelve True si hay que entrar.
    """
    g, nivel = op["gatillo"], float(op["nivel"])
    if g == "mercado":
        return True
    nuevas = [v for v in velas if v["epoch"] > estado.get("ultima_epoch", 0)]
    for v in nuevas:
        estado["ultima_epoch"] = v["epoch"]
        if g == "retesteo_abajo" and v["high"] >= nivel * (1 - tolerancia):
            estado["tocado"] = True
        if g == "retesteo_arriba" and v["low"] <= nivel * (1 + tolerancia):
            estado["tocado"] = True
        dispara = {
            "ruptura_arriba": v["close"] > nivel,
            "ruptura_abajo": v["close"] < nivel,
            "retesteo_abajo": estado.get("tocado") and v["close"] < nivel,
            "retesteo_arriba": estado.get("tocado") and v["close"] > nivel,
        }[g]
        if dispara:
            return True
    return False


def parse_utc(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


# --------------------------------------------------------------------------- cliente Deriv
class DerivError(Exception):
    pass


class Deriv:
    def __init__(self, token, app_id):
        self.token, self.app_id, self.ws, self.rid = token, app_id, None, 0
        self.nueva = token.startswith("pat_")
        self.cuenta = None

    # ---- API nueva: REST con Bearer + Deriv-App-ID, luego WebSocket con OTP de un solo uso
    def _rest(self, metodo, ruta, cuerpo=None):
        import urllib.error
        import urllib.request
        req = urllib.request.Request(REST_URL + ruta, method=metodo,
                                     data=None if cuerpo is None else json.dumps(cuerpo).encode(),
                                     headers={"Authorization": f"Bearer {self.token}",
                                              "Deriv-App-ID": self.app_id,
                                              "Content-Type": "application/json",
                                              "User-Agent": "elferes-ejecutor/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            raise DerivError(f"HTTP {e.code} en {metodo} {ruta}: {e.read().decode(errors='replace')[:400]}")

    @staticmethod
    def _lista(r):
        d = r.get("data", r) if isinstance(r, dict) else r
        if isinstance(d, dict):
            d = d.get("accounts", [d])
        return d if isinstance(d, list) else []

    async def _conectar_nueva(self):
        import websockets
        if not self.app_id or self.app_id == "1089":
            raise DerivError("La API nueva necesita DERIV_APP_ID (App ID de tu app en developers.deriv.com)")
        cuentas = self._lista(await asyncio.to_thread(self._rest, "GET", "/accounts"))
        if not cuentas:
            raise DerivError("La API no devolvió cuentas de Options")
        demo = [c for c in cuentas if str(c.get("account_type", "")).lower() == "demo"]
        c = (demo or cuentas)[0]
        otp = await asyncio.to_thread(self._rest, "POST", f"/accounts/{c['account_id']}/otp")
        url = (otp.get("data") or {}).get("url") or otp.get("url")
        if not url:
            raise DerivError(f"Respuesta OTP sin url: {str(otp)[:200]}")
        self.ws = await websockets.connect(url, ping_interval=30, open_timeout=30)
        moneda = c.get("currency")
        moneda = moneda if isinstance(moneda, str) and len(moneda) == 3 else "USD"
        self.cuenta = {"loginid": c.get("account_id"), "currency": moneda,
                       "balance": c.get("balance"), "is_virtual": str(c.get("account_type", "")).lower() == "demo",
                       "cuentas_disponibles": [(x.get("account_id"), x.get("account_type")) for x in cuentas]}
        return self.cuenta

    async def conectar(self):
        import websockets
        if self.nueva:
            return await self._conectar_nueva()
        self.ws = await websockets.connect(WS_URL.format(app_id=self.app_id or "1089"),
                                           ping_interval=30, open_timeout=30)
        self.cuenta = (await self._call({"authorize": self.token}))["authorize"]
        return self.cuenta

    async def _call(self, msg):
        self.rid += 1
        msg = dict(msg, req_id=self.rid)
        await self.ws.send(json.dumps(msg))
        while True:
            r = json.loads(await asyncio.wait_for(self.ws.recv(), 60))
            if r.get("req_id") == self.rid:
                break
        if "error" in r:
            err = r["error"]
            det = f" | detalles: {json.dumps(err.get('details'), ensure_ascii=False)[:300]}" if err.get("details") else ""
            raise DerivError(f"{err.get('code')}: {err.get('message')}{det}")
        return r

    async def call(self, msg):
        """Llamada con reconexión automática (hasta 3 intentos)."""
        for intento in range(3):
            try:
                return await self._call(msg)
            except DerivError:
                raise
            except Exception:
                if intento == 2:
                    raise
                await asyncio.sleep(5 * (intento + 1))
                await self.conectar()

    async def saldo(self):
        try:
            return float((await self.call({"balance": 1}))["balance"]["balance"])
        except DerivError:
            if not self.nueva:
                raise
            cuentas = self._lista(await asyncio.to_thread(self._rest, "GET", "/accounts"))
            c = next(x for x in cuentas if x.get("account_id") == self.cuenta["loginid"])
            return float(c["balance"])

    async def multiplicadores(self, simbolo, tipo):
        r = await self.call({"contracts_for": simbolo})
        for c in r["contracts_for"]["available"]:
            if c.get("contract_type") == tipo and c.get("multiplier_range"):
                return [int(m) for m in c["multiplier_range"]]
        return []

    async def velas(self, simbolo, granularidad, n=6):
        r = await self.call({"ticks_history": simbolo, "style": "candles", "granularity": granularidad,
                             "count": n, "end": "latest"})
        ahora = time.time()
        return [{k: float(v[k]) for k in ("open", "high", "low", "close")} | {"epoch": int(v["epoch"])}
                for v in r["candles"] if int(v["epoch"]) + granularidad <= ahora]

    async def precio(self, simbolo):
        r = await self.call({"ticks_history": simbolo, "style": "ticks", "count": 1, "end": "latest"})
        return float(r["history"]["prices"][-1])

    async def comprar(self, simbolo, tipo, stake, m, stop_loss, take_profit):
        """Cotiza (proposal) y compra con el id de la cotización.

        Prueba variantes de campos porque la API nueva de Deriv renombró algunos
        (symbol -> underlying_symbol) y puede no aceptar la moneda explícita.
        """
        base = {"amount": stake, "basis": "stake", "contract_type": tipo, "multiplier": m,
                "limit_order": {"stop_loss": stop_loss, "take_profit": take_profit}}
        errores = []
        for campo_simbolo in ("underlying_symbol", "symbol"):
            for con_moneda in (True, False):
                p = dict(base, **{campo_simbolo: simbolo})
                if con_moneda:
                    p["currency"] = self.cuenta["currency"]
                try:
                    prop = (await self.call(dict({"proposal": 1}, **p)))["proposal"]
                except DerivError as e:
                    errores.append(f"proposal[{campo_simbolo}, moneda={con_moneda}] -> {e}")
                    continue
                r = await self.call({"buy": prop["id"], "price": float(prop.get("ask_price", stake))})
                return r["buy"]
        raise DerivError("No se pudo cotizar: " + " || ".join(errores))

    async def contrato(self, cid):
        return (await self.call({"proposal_open_contract": 1, "contract_id": cid}))["proposal_open_contract"]

    async def vender(self, cid):
        try:
            return (await self.call({"sell": cid, "price": 0}))["sell"]
        except DerivError as e:  # ya cerrado por SL/TP
            return {"error": str(e)}


# --------------------------------------------------------------------------- ejecución
class Registro:
    def __init__(self, fecha):
        self.ruta = RAIZ / "ejecuciones" / f"{fecha}.json"
        self.datos = {"fecha": fecha, "eventos": [], "operaciones": [], "resumen": {}}

    def evento(self, texto, **extra):
        e = {"hora_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "texto": texto} | extra
        print(f"[{e['hora_utc']}] {texto}", extra or "", flush=True)
        self.datos["eventos"].append(e)
        self.guardar()

    def guardar(self):
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.ruta.write_text(json.dumps(self.datos, ensure_ascii=False, indent=2))


async def abrir(api, op, cfg, reg):
    sym, largo = op["simbolo_deriv"], es_largo(op["direccion"])
    tipo = "MULTUP" if largo else "MULTDOWN"
    precio = await api.precio(sym)
    if (largo and not (op["stop"] < precio < op["tp1"])) or (not largo and not (op["tp1"] < precio < op["stop"])):
        reg.evento(f"{op['activo']}: precio {precio} fuera de la zona útil, no se entra")
        return None
    r = rb(op["direccion"], precio, op["stop"], op["tp2"])
    if r is None or r < cfg["rb_minimo_tp2"]:
        reg.evento(f"{op['activo']}: R/B real hasta TP2 = {r and round(r, 2)} < {cfg['rb_minimo_tp2']}, no se entra")
        return None
    riesgo_usd = await api.saldo() * cfg["riesgo_pct"] / 100
    mults = await api.multiplicadores(sym, tipo)
    tam = dimensionar(precio, op["stop"], riesgo_usd, mults, cfg["stake_minimo"])
    if not tam:
        reg.evento(f"{op['activo']}: no se puede dimensionar (multiplicadores {mults}, riesgo {riesgo_usd:.2f})")
        return None
    m, stake = tam
    medio = round(stake / 2, 2)
    sl = min(monto(medio, m, precio, op["stop"]), medio)
    patas = []
    for nombre, tp in (("A", op["tp1"]), ("B", op["tp2"])):
        c = await api.comprar(sym, tipo, medio, m, sl, monto(medio, m, precio, tp))
        patas.append({"pata": nombre, "contract_id": c["contract_id"], "abierto": True})
    t = {"activo": op["activo"], "simbolo": sym, "tipo": tipo, "precio_ref": precio, "multiplicador": m,
         "stake_por_pata": medio, "stop_loss_usd_por_pata": sl, "riesgo_usd": round(2 * sl, 2),
         "patas": patas, "break_even": False, "resultado_usd": 0.0, "op": op}
    reg.datos["operaciones"].append(t)
    reg.evento(f"{op['activo']}: ABIERTA {tipo} x{m}, 2 x {medio} {api.cuenta['currency']}, riesgo {2 * sl:.2f}")
    return t


async def vigilar(api, t, reg):
    """Actualiza el estado de una operación abierta. Devuelve True si sigue abierta."""
    largo = t["tipo"] == "MULTUP"
    for p in t["patas"]:
        if not p["abierto"]:
            continue
        c = await api.contrato(p["contract_id"])
        p["entrada"] = float(c.get("entry_spot") or t["precio_ref"])
        if c.get("is_sold"):
            p["abierto"], p["profit"] = False, float(c.get("profit", 0))
            t["resultado_usd"] = round(t["resultado_usd"] + p["profit"], 2)
            reg.evento(f"{t['activo']}: pata {p['pata']} cerrada, resultado {p['profit']:+.2f}")
            if p["pata"] == "A" and p["profit"] > 0:
                t["break_even"] = True
    b = t["patas"][1]
    if t["break_even"] and b["abierto"]:
        precio = await api.precio(t["simbolo"])
        if (largo and precio <= b["entrada"]) or (not largo and precio >= b["entrada"]):
            await api.vender(b["contract_id"])
            reg.evento(f"{t['activo']}: precio volvió a la entrada tras TP1, se cierra la pata B")
    return any(p["abierto"] for p in t["patas"])


async def cerrar_todo(api, abiertas, reg, motivo):
    for t in abiertas:
        for p in t["patas"]:
            if p["abierto"]:
                await api.vender(p["contract_id"])
        await vigilar(api, t, reg)
    if abiertas:
        reg.evento(f"Cierre de todas las posiciones: {motivo}")


async def ejecutar(plan, modo, cfg):
    reg = Registro(plan["fecha"])
    token = os.environ.get("DERIV_TOKEN", "").strip()
    if not token:
        reg.evento("Falta el secreto DERIV_TOKEN; no se puede operar")
        return 1
    api = Deriv(token, os.environ.get("DERIV_APP_ID", "").strip())
    reg.evento(f"API de Deriv: {'nueva (api.derivws.com, token pat_)' if api.nueva else 'antigua (ws.derivws.com)'}"
               f", App ID {'configurado' if api.app_id else 'NO configurado'}")
    try:
        cuenta = await api.conectar()
    except Exception as e:
        reg.evento(f"No se pudo conectar a Deriv: {type(e).__name__}: {e}")
        return 1
    es_demo = bool(cuenta.get("is_virtual"))
    reg.evento(f"Conectado a Deriv: cuenta {'DEMO' if es_demo else 'REAL'} {cuenta.get('loginid')}, "
               f"saldo {cuenta.get('balance')} {cuenta.get('currency')}")
    if not es_demo and os.environ.get("DERIV_PERMITIR_REAL", "").lower() != "si":
        reg.evento("La cuenta NO es demo y DERIV_PERMITIR_REAL no es 'si': no se opera")
        return 1

    if modo == "prueba":
        return await operacion_prueba(api, reg)

    ops = []
    for op in plan.get("operaciones", []):
        err = validar_operacion(op)
        if err:
            reg.evento(f"{op.get('activo', '?')}: descartada del plan ({err})")
            continue
        tipo = "MULTUP" if es_largo(op["direccion"]) else "MULTDOWN"
        try:
            mults = await api.multiplicadores(op["simbolo_deriv"], tipo)
            if modo == "verificar":
                v = await api.velas(op["simbolo_deriv"], cfg["granularidad"])
                reg.evento(f"{op['activo']}: velas de 15 min OK, último cierre {v[-1]['close'] if v else '—'}")
        except Exception as e:
            reg.evento(f"{op['activo']}: error consultando Deriv ({type(e).__name__}: {e})")
            continue
        if not mults:
            reg.evento(f"{op['activo']}: Deriv no ofrece {tipo} en {op['simbolo_deriv']}, se omite")
            continue
        reg.evento(f"{op['activo']}: listo ({op['gatillo']} en {op['nivel']}, multiplicadores {mults})")
        ops.append({"op": op, "estado": {}, "hecho": False})

    if modo == "verificar" or not ops:
        reg.datos["resumen"] = {"modo": modo, "operaciones_validas": len(ops)}
        reg.evento("Verificación terminada" if modo == "verificar" else "No hay operaciones ejecutables hoy")
        await api.ws.close()
        return 0

    saldo_inicial = await api.saldo()
    inicio, abiertas, realizado = time.time(), [], 0.0
    while True:
        ahora = dt.datetime.now(dt.timezone.utc)
        limite_job = time.time() - inicio > cfg["limite_job_s"]
        frenado = realizado <= -saldo_inicial * cfg["perdida_max_dia_pct"] / 100

        # cerrar por hora, por límite del job o por freno diario
        for t in list(abiertas):
            if limite_job or frenado or ahora >= parse_utc(t["op"]["cerrar_antes_utc"]):
                await cerrar_todo(api, [t], reg, "límite del job" if limite_job else
                                  "freno diario" if frenado else "hora de cierre")
                abiertas.remove(t)
                realizado += t["resultado_usd"]

        # vigilar abiertas
        for t in list(abiertas):
            if not await vigilar(api, t, reg):
                abiertas.remove(t)
                realizado += t["resultado_usd"]

        # buscar entradas
        pendientes = [o for o in ops if not o["hecho"] and ahora < parse_utc(o["op"]["valido_hasta_utc"])]
        for o in ops:
            if not o["hecho"] and ahora >= parse_utc(o["op"]["valido_hasta_utc"]):
                o["hecho"] = True
                reg.evento(f"{o['op']['activo']}: no se activó antes de {o['op']['valido_hasta_utc']}, cancelada")
        if not (limite_job or frenado):
            for o in pendientes:
                if len(abiertas) >= cfg["max_operaciones"]:
                    break
                velas = await api.velas(o["op"]["simbolo_deriv"], cfg["granularidad"])
                if evaluar_gatillo(o["op"], velas, o["estado"], cfg["tolerancia_toque"]):
                    o["hecho"] = True
                    t = await abrir(api, o["op"], cfg, reg)
                    if t:
                        abiertas.append(t)

        if not abiertas and (limite_job or frenado or not [o for o in ops if not o["hecho"]]):
            break
        await asyncio.sleep(cfg["intervalo_s"])

    reg.datos["resumen"] = {
        "modo": modo, "saldo_inicial": saldo_inicial, "saldo_final": await api.saldo(),
        "resultado_usd": round(sum(t["resultado_usd"] for t in reg.datos["operaciones"]), 2),
        "operaciones_abiertas": len(reg.datos["operaciones"]),
    }
    reg.evento(f"Fin de la jornada: resultado {reg.datos['resumen']['resultado_usd']:+.2f}")
    await api.ws.close()
    return 0


async def operacion_prueba(api, reg, simbolo="frxEURUSD", stake=10.0, mult=100, sl=5.0, tp=5.0):
    """Abre UNA compra pequeña de prueba y la deja abierta para que el usuario la vea y la cierre."""
    precio = await api.precio(simbolo)
    try:
        c = await api.comprar(simbolo, "MULTUP", stake, mult, sl, tp)
    except DerivError as e:
        reg.evento(f"PRUEBA fallida: {e}")
        return 1
    reg.datos["operaciones"].append({"prueba": True, "simbolo": simbolo, "contract_id": c.get("contract_id"),
                                     "precio_ref": precio, "stake": stake, "multiplicador": mult,
                                     "stop_loss_usd": sl, "take_profit_usd": tp})
    reg.evento(f"PRUEBA abierta: COMPRA {simbolo} x{mult}, stake {stake} USD, precio ~{precio}, "
               f"stop loss -{sl} USD, take profit +{tp} USD, contrato {c.get('contract_id')}. "
               "Queda abierta para cerrarla a mano en Deriv.")
    await api.ws.close()
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modo", choices=["verificar", "ejecutar", "prueba"], default="verificar")
    ap.add_argument("--fecha", default="", help="AAAA-MM-DD (por defecto, hoy en Bogotá)")
    args = ap.parse_args()
    fecha = args.fecha or dt.datetime.now(ZONA).date().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        sys.exit("fecha inválida")
    ruta = RAIZ / "planes" / f"{fecha}.json"
    if args.modo == "prueba" and not ruta.exists():
        return asyncio.run(ejecutar({"fecha": fecha, "operaciones": []}, "prueba", CONFIG))
    if not ruta.exists():
        print(f"No hay plan para {fecha} ({ruta}); nada que hacer.")
        return 0
    return asyncio.run(ejecutar(json.loads(ruta.read_text()), args.modo, CONFIG))


if __name__ == "__main__":
    sys.exit(main())
