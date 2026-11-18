"""Pruebas del ejecutor con un Deriv simulado: python3 -m unittest trading/ejecutor/test_ejecutor.py"""
import asyncio
import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import deriv_ejecutor as E  # noqa: E402

OP = {"activo": "EUR/USD", "simbolo_deriv": "frxEURUSD", "direccion": "venta", "gatillo": "retesteo_abajo",
      "nivel": 1.1000, "stop": 1.1025, "tp1": 1.0960, "tp2": 1.0935,
      "valido_hasta_utc": "2099-01-01T18:00:00Z", "cerrar_antes_utc": "2099-01-01T18:30:00Z"}


def vela(e, o, h, l, c):
    return {"epoch": e, "open": o, "high": h, "low": l, "close": c}


class Logica(unittest.TestCase):
    def test_rb(self):
        self.assertAlmostEqual(E.rb("venta", 1.1, 1.1025, 1.0935), 2.6, places=6)
        self.assertAlmostEqual(E.rb("compra", 100, 98, 105), 2.5)

    def test_dimensionar_riesgo_exacto(self):
        m, stake = E.dimensionar(1.1, 1.1025, 100, [50, 100, 200, 300, 500])
        self.assertEqual(m, 300)  # 500 > 1.1/0.0025 = 440 no permitido
        self.assertAlmostEqual(E.monto(stake, m, 1.1, 1.1025), 100, delta=0.05)
        self.assertLessEqual(E.monto(stake / 2, m, 1.1, 1.1025), stake / 2)

    def test_dimensionar_imposible(self):
        self.assertIsNone(E.dimensionar(100, 99, 1, [100, 200]))      # stake < mínimo
        self.assertIsNone(E.dimensionar(100, 50, 100, [5, 10]))       # stop demasiado lejos

    def test_validar(self):
        self.assertIsNone(E.validar_operacion(OP))
        self.assertIn("incoherentes", E.validar_operacion(OP | {"direccion": "compra"}))
        self.assertIn("gatillo", E.validar_operacion(OP | {"gatillo": "x"}))

    def test_retesteo_abajo(self):
        est = {}
        self.assertFalse(E.evaluar_gatillo(OP, [vela(1, 1.097, 1.098, 1.096, 1.0975)], est, 0.0003))
        self.assertFalse(E.evaluar_gatillo(OP, [vela(2, 1.0975, 1.1001, 1.097, 1.1003)], est, 0.0003))
        self.assertTrue(est["tocado"])
        self.assertTrue(E.evaluar_gatillo(OP, [vela(2, 0, 0, 0, 0), vela(3, 1.1, 1.1005, 1.098, 1.0990)], est, 0.0003))

    def test_ruptura_y_mercado(self):
        op = OP | {"gatillo": "ruptura_arriba", "direccion": "compra", "nivel": 100, "stop": 98, "tp1": 103, "tp2": 105}
        self.assertFalse(E.evaluar_gatillo(op, [vela(1, 99, 100.5, 98, 99.9)], {}, 0))
        self.assertTrue(E.evaluar_gatillo(op, [vela(1, 99, 101, 98, 100.2)], {}, 0))
        self.assertTrue(E.evaluar_gatillo(OP | {"gatillo": "mercado"}, [], {}, 0))


class DerivFalso:
    """Simula un mercado que sube a 1.1000, rechaza y cae hasta TP1 y luego vuelve a la entrada."""
    def __init__(self):
        self.cuenta = {"currency": "USD", "is_virtual": 1, "loginid": "VRTC1", "balance": 10000}
        self.paso, self.contratos, self.ws = 0, {}, self
        self.nueva, self.app_id = True, "123"
        self.precios = [1.0995, 1.0990, 1.0975, 1.0959, 1.0985, 1.0992, 1.0992]

    async def close(self): pass
    async def conectar(self): return self.cuenta
    async def saldo(self): return 10000.0
    async def multiplicadores(self, s, t): return [50, 100, 200, 300, 500]

    async def velas(self, s, g, n=6):
        self.paso += 1
        return [vela(1, 1.097, 1.1002, 1.097, 1.1001), vela(2, 1.1001, 1.1004, 1.0985, 1.0990)]

    def _p(self):
        return self.precios[min(self.paso, len(self.precios) - 1)]

    async def precio(self, s):
        return self._p()

    async def comprar(self, s, tipo, stake, m, sl, tp):
        cid = len(self.contratos) + 1
        self.contratos[cid] = {"stake": stake, "m": m, "sl": sl, "tp": tp, "entry": self._p(), "sold": False}
        return {"contract_id": cid}

    async def contrato(self, cid):
        abiertos = [k for k, v in self.contratos.items() if not v["sold"]]
        if cid == min(abiertos, default=cid):  # el precio avanza una vez por vuelta del bucle
            self.paso += 1
            if self.paso > 100:
                raise RuntimeError("bucle sin fin en la simulación")
        for c in self.contratos.values():  # SL/TP se ejecutan en el servidor
            pnl = c["stake"] * c["m"] * (c["entry"] - self._p()) / c["entry"]
            if not c["sold"] and (pnl >= c["tp"] or pnl <= -c["sl"]):
                c["sold"], c["profit"] = True, round(max(min(pnl, c["tp"]), -c["sl"]), 2)
        c = self.contratos[cid]
        return {"entry_spot": c["entry"], "is_sold": int(c["sold"]), "profit": c.get("profit", 0)}

    async def vender(self, cid):
        c = self.contratos[cid]
        if not c["sold"]:
            c["sold"] = True
            c["profit"] = round(c["stake"] * c["m"] * (c["entry"] - self._p()) / c["entry"], 2)
        return {}


class Flujo(unittest.TestCase):
    def test_jornada_completa(self):
        falso = DerivFalso()
        E.Deriv = lambda *a: falso
        E.RAIZ = Path(__file__).resolve().parents[2] / ".tmp_test"
        cfg = E.CONFIG | {"intervalo_s": 0}
        plan = {"fecha": "2099-01-01", "operaciones": [OP]}
        import os
        os.environ["DERIV_TOKEN"] = "falso"
        self.assertEqual(asyncio.run(E.ejecutar(plan, "ejecutar", cfg)), 0)
        res = (E.RAIZ / "ejecuciones" / "2099-01-01.json").read_text()
        import json, shutil
        datos = json.loads(res)
        shutil.rmtree(E.RAIZ)
        t = datos["operaciones"][0]
        self.assertAlmostEqual(t["riesgo_usd"], 100, delta=1)       # 1% de 10.000
        self.assertGreater(t["patas"][0]["profit"], 0)              # A cobró TP1
        self.assertTrue(t["break_even"])
        self.assertGreater(datos["resumen"]["resultado_usd"], 0)
        textos = " ".join(e["texto"] for e in datos["eventos"])
        self.assertIn("se cierra la pata B", textos)


if __name__ == "__main__":
    unittest.main()
