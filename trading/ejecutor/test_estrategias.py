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


def aleatoria(n=3000, semilla=1):
    random.seed(semilla)
    p, v = 100.0, []
    for i in range(n):
        o = p
        p *= 1 + random.gauss(0, 0.002)
        v.append({"epoch": 1700000000 + i * 300, "open": o, "high": max(o, p) * 1.0007,
                  "low": min(o, p) * 0.9993, "close": p})
    return v


class Estrategias(unittest.TestCase):
    def test_senales_coherentes(self):
        v = aleatoria()
        for nombre, f in E.ESTRATEGIAS.items():
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


if __name__ == "__main__":
    unittest.main()
