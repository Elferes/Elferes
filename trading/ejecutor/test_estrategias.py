"""Pruebas de estrategias, patrones y backtest: python3 -m unittest trading/ejecutor/test_estrategias.py"""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import backtest as B  # noqa: E402
import estrategias as E  # noqa: E402
import patrones as P  # noqa: E402
import scalper as S  # noqa: E402
from test_scalper import serie_alcista_con_retroceso  # noqa: E402

CFG = S.preparar_config(S.CONFIG, capital=100.0)


def aleatoria(n=3000, semilla=1, paso=300):
    random.seed(semilla)
    p, v = 100.0, []
    for i in range(n):
        o = p
        p *= 1 + random.gauss(0, 0.002)
        v.append({"epoch": 1700000000 + i * paso, "open": o, "high": max(o, p) * (1 + abs(random.gauss(0, 0.0008))),
                  "low": min(o, p) * (1 - abs(random.gauss(0, 0.0008))), "close": p})
    return v


class Estrategias(unittest.TestCase):
    def test_senales_coherentes(self):
        for nombre, f in E.ESTRATEGIAS.items():
            v = aleatoria(paso=3600 if nombre == "ruptura_asiatica" else 300)
            n = 0
            for i in range(60, len(v)):
                s = f(v[i - 119 if i >= 119 else 0:i + 1], CFG)
                if not s:
                    continue
                n += 1
                largo = s["direccion"] == "compra"
                self.assertTrue(s["stop"] < s["entrada"] < s["tp"] if largo else s["tp"] < s["entrada"] < s["stop"], nombre)
                self.assertGreaterEqual(abs(s["tp"] - s["entrada"]) + 1e-12, abs(s["entrada"] - s["stop"]) * 0.99, nombre)
                self.assertEqual(s["estrategia"], nombre)
            self.assertGreater(n, 0, f"{nombre} nunca dio señal")

    def test_variantes(self):
        f = E.obtener("rsi2_reversion|tendencia200,vol_alta|obj2r")
        self.assertIsNotNone(f)
        self.assertIsNone(E.obtener("rsi2_reversion|inventado|base"))
        v, n = aleatoria(), 0
        for i in range(250, len(v)):
            s = f(v[i - 249:i + 1], CFG)
            if s:
                n += 1
                riesgo = abs(s["entrada"] - s["stop"])
                self.assertAlmostEqual(abs(s["tp"] - s["entrada"]), 2 * riesgo)
                self.assertEqual(s["estrategia"], "rsi2_reversion|tendencia200,vol_alta|obj2r")
        self.assertGreater(n, 0)

    def test_sesgo(self):
        v = serie_alcista_con_retroceso()
        self.assertEqual(E.buscar_senal(v, CFG)["direccion"], "compra")
        self.assertIsNone(E.buscar_senal(v, CFG, "venta", ["tendencia_retroceso"]))

    def test_sin_ventaja_en_mercado_aleatorio(self):
        # sin costes, la esperanza en un paseo aleatorio debe rondar 0 (si no, hay trampa/lookahead)
        v = aleatoria(4000, 7)
        for nombre, f in E.ESTRATEGIAS.items():
            m = B.metricas(B.simular(v, f, CFG, 0.0, 6))
            if m["operaciones"] >= 50:
                self.assertLess(abs(m["esperanza_r"]), 0.25, nombre)


class Patrones(unittest.TestCase):
    def test_envolvente(self):
        base = aleatoria(60, 2)
        p0 = base[-1]["close"]
        base += [{"epoch": 1, "open": p0, "high": p0 * 1.001, "low": p0 * 0.990, "close": p0 * 0.991},
                 {"epoch": 2, "open": p0 * 0.990, "high": p0 * 1.004, "low": p0 * 0.989, "close": p0 * 1.003}]
        nombres = [d["patron"] for d in P.detectar(base)]
        self.assertIn("envolvente_alcista", nombres)

    def test_rsi_serie(self):
        c = [x["close"] for x in aleatoria(400, 4)]
        rs = P.rsi_serie(c)
        for k in (20, 200, 399):
            self.assertAlmostEqual(rs[k], S.rsi(c[:k + 1]), places=6)

    def test_metricas(self):
        m = B.metricas([{"r": 1.5}, {"r": -1}, {"r": -1}, {"r": 1.5}])
        self.assertEqual(m["acierto_pct"], 50.0)
        self.assertAlmostEqual(m["esperanza_r"], 0.25)
        self.assertEqual(m["profit_factor"], 1.5)



class TestContextoDiario(unittest.TestCase):
    def test_sin_mirar_el_futuro(self):
        import datetime as dt
        t0 = int(dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc).timestamp())
        d = [{"epoch": t0 + i * 86400, "open": 100 + i, "high": 102 + i, "low": 99 + i, "close": 101 + i - 2 * (i % 2)}
             for i in range(10)]
        ctx = E.contexto_diario(d)
        for i in range(1, 10):
            f = dt.datetime.fromtimestamp(d[i]["epoch"], dt.timezone.utc).date()
            self.assertEqual(ctx[f]["d_alcista"], d[i - 1]["close"] > d[i - 1]["open"])
        s = {"direccion": "compra", "entrada": 1, "stop": 0.9, "tp": 1.2}
        self.assertFalse(E.FILTROS["d_tend"](s, {"d_sobre200": None}))
        self.assertTrue(E.FILTROS["d_retroceso"](s, {"d_sobre200": True, "d_rsi2": 10}))
        self.assertFalse(E.FILTROS["d_retroceso"](s, {"d_sobre200": True, "d_rsi2": 60}))

if __name__ == "__main__":
    unittest.main()
