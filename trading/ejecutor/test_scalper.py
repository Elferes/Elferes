"""Pruebas del scalper: python3 -m unittest trading/ejecutor/test_scalper.py"""
import asyncio
import datetime as dt
import os
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import deriv_ejecutor as D  # noqa: E402
import scalper as S  # noqa: E402


def serie_alcista_con_retroceso():
    """Tendencia alcista, retroceso a la EMA21 y vela de rebote al final."""
    velas, p = [], 100.0
    for i in range(80):
        o = p
        p += 0.12
        velas.append({"epoch": i * 300, "open": o, "high": p + 0.05, "low": o - 0.05, "close": p})
    for i in range(80, 84):  # retroceso
        o = p
        p -= 0.25
        velas.append({"epoch": i * 300, "open": o, "high": o + 0.03, "low": p - 0.2, "close": p})
    o = p
    p += 0.45  # rebote
    velas.append({"epoch": 84 * 300, "open": o, "high": p + 0.02, "low": o - 0.02, "close": p})
    return velas


class Parametros(unittest.TestCase):
    def test_limites(self):
        import json, tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"riesgo_pct": 50, "atr_stop": 2.0, "atr_objetivo": 1.0, "activos": ["EUR/USD"], "x": 1}, f)
        cfg, notas = S.cargar_parametros(S.CONFIG, f.name)
        self.assertEqual(cfg["riesgo_pct"], 2.0)            # recortado al máximo
        self.assertGreaterEqual(cfg["atr_objetivo"], 2.4)   # R/B mínimo 1.2
        self.assertEqual(list(cfg["simbolos"]), ["EUR/USD"])
        self.assertTrue(notas)

    def test_combinaciones(self):
        import json, tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"combinaciones": [{"activo": "US 500", "tf": "1h", "estrategia": "cruce_ema"},
                                         {"activo": "X", "tf": "1h", "estrategia": "cruce_ema"},
                                         {"activo": "EUR/USD", "tf": "2h", "estrategia": "cruce_ema"}]}, f)
        cfg, notas = S.cargar_parametros(S.CONFIG, f.name)
        self.assertEqual(cfg["combinaciones"], [{"activo": "US 500", "tf": "1h", "estrategia": "cruce_ema"}])
        self.assertTrue(notas)

    def test_archivo_del_repo(self):
        ruta = Path(__file__).resolve().parents[1] / "aprendizaje" / "parametros.json"
        cfg, notas = S.cargar_parametros(S.CONFIG, ruta)
        self.assertEqual(notas, [])
        self.assertEqual(cfg["riesgo_pct"], 1.0)
        self.assertEqual(len(cfg["combinaciones"]), 5)


class Senales(unittest.TestCase):
    def test_compra_en_retroceso(self):
        s = S.senal(serie_alcista_con_retroceso(), S.CONFIG)
        self.assertIsNotNone(s)
        self.assertEqual(s["direccion"], "compra")
        self.assertLess(s["stop"], s["entrada"])
        self.assertAlmostEqual((s["tp"] - s["entrada"]) / (s["entrada"] - s["stop"]), 1.5)

    def test_sesgo_contrario_bloquea(self):
        self.assertIsNone(S.senal(serie_alcista_con_retroceso(), S.CONFIG, sesgo="venta"))

    def test_venta_espejo(self):
        v = [{"epoch": x["epoch"], "open": 300 - x["open"], "high": 300 - x["low"], "low": 300 - x["high"],
              "close": 300 - x["close"]} for x in serie_alcista_con_retroceso()]
        s = S.senal(v, S.CONFIG)
        self.assertIsNotNone(s)
        self.assertEqual(s["direccion"], "venta")
        self.assertGreater(s["stop"], s["entrada"])

    def test_pocas_velas(self):
        self.assertIsNone(S.senal(serie_alcista_con_retroceso()[:30], S.CONFIG))

    def test_bloqueo_noticias(self):
        ahora = dt.datetime(2026, 11, 19, 13, 25, tzinfo=dt.timezone.utc)
        self.assertTrue(S.en_bloqueo(ahora, ["2026-11-19T13:30:00Z"], 15))
        self.assertFalse(S.en_bloqueo(ahora, ["2026-11-19T19:00:00Z"], 15))


class DerivFalso:
    """Cada operación abierta gana su objetivo a la segunda consulta."""
    def __init__(self):
        self.cuenta = {"currency": "USD", "is_virtual": True, "loginid": "DOT1"}
        self.ws, self.nueva, self.app_id, self.c, self.n = self, True, "1", {}, 0

    async def close(self): pass
    async def conectar(self): return self.cuenta
    async def saldo(self): return 10000.0
    async def multiplicadores(self, s, t): return [100, 200, 300, 500, 800] if s.startswith("frx") else []
    async def precio(self, s): return serie_alcista_con_retroceso()[-1]["close"]

    async def velas(self, s, g, n=6):
        self.n += 1
        v = serie_alcista_con_retroceso()
        return [dict(x, epoch=x["epoch"] + self.n * 300) for x in v]

    async def comprar(self, s, tipo, stake, m, sl, tp):
        cid = len(self.c) + 1
        self.c[cid] = {"tp": tp, "consultas": 0, "sold": False}
        return {"contract_id": cid}

    async def contrato(self, cid):
        k = self.c[cid]
        k["consultas"] += 1
        if k["consultas"] >= 2 and not k["sold"]:
            k["sold"], k["profit"] = True, k["tp"]
        return {"is_sold": k["sold"], "profit": k.get("profit", 0)}

    async def vender(self, cid): self.c[cid]["sold"] = True


class Flujo(unittest.TestCase):
    def test_para_al_llegar_a_la_meta(self):
        D.Deriv = lambda *a: DerivFalso()
        D.RAIZ = Path(__file__).resolve().parents[2] / ".tmp_test_scalper"
        os.environ["DERIV_TOKEN"] = "x"
        cfg = S.preparar_config(S.CONFIG, capital=100.0) | {"intervalo_s": 0, "fin_utc": "23:59"}
        try:
            self.assertEqual(asyncio.run(S.correr({"fecha": "2099-01-01", "operaciones": []}, "ejecutar", cfg)), 0)
            import json
            datos = json.loads((D.RAIZ / "ejecuciones" / "2099-01-01-scalping.json").read_text())
        finally:
            shutil.rmtree(D.RAIZ, ignore_errors=True)
        r = datos["resumen"]
        self.assertIn("meta diaria", r["motivo_fin"])
        self.assertGreaterEqual(r["resultado_usd"], 3)       # meta = 3 % de 100
        self.assertTrue(r["capital_virtual"])
        op = datos["operaciones"][0]
        self.assertAlmostEqual(op["sl_usd"], 1, delta=0.05)  # 1 % de 100
        self.assertEqual(op["cierre"], "objetivo")
        self.assertAlmostEqual(op["tp_usd"] / op["sl_usd"], 1.5, delta=0.05)


if __name__ == "__main__":
    unittest.main()
