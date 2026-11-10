from __future__ import annotations

import unittest
from fractions import Fraction

from pilares_concreto_nbr6118.constants import (
    GAMMA_C,
    GAMMA_S,
    GAMMA_F,
    ES_KN_CM2,
    LARGURA_MINIMA_PILAR_CM,
    AREA_MINIMA_SECAO_CM2,
    ESBELTEZ_MAXIMA_ADMISSIVEL,
    RHO_MIN_PILAR_AC,
    RHO_MIN_PILAR_NSD,
    RHO_MAX_PILAR_EMENDA,
    DIAMETRO_MINIMO_LONGITUDINAL_MM,
    DIAMETRO_MINIMO_ESTRIBO_MM,
    TABELA_CAA_PILARES,
    TABELA_CONCRETOS_NBR6118,
    TABELA_ACOS_NBR6118,
    TABELA_BITOLAS_LONGITUDINAIS,
    TABELA_BITOLAS_ESTRIBOS,
)


class TestConstants(unittest.TestCase):
    def test_coeficientes_ponderacao(self) -> None:
        self.assertEqual(GAMMA_C, Fraction(140, 100))
        self.assertEqual(GAMMA_S, Fraction(115, 100))
        self.assertEqual(GAMMA_F, Fraction(140, 100))

    def test_limites_geometricos_pilares(self) -> None:
        self.assertEqual(LARGURA_MINIMA_PILAR_CM, Fraction(14, 1))
        self.assertEqual(AREA_MINIMA_SECAO_CM2, Fraction(360, 1))
        self.assertEqual(ESBELTEZ_MAXIMA_ADMISSIVEL, Fraction(200, 1))

    def test_taxas_armadura_normativa(self) -> None:
        self.assertEqual(RHO_MIN_PILAR_AC, Fraction(4, 1000))       # 0,40% Ac
        self.assertEqual(RHO_MIN_PILAR_NSD, Fraction(15, 10000))    # 0,15% Nsd/fyd
        self.assertEqual(RHO_MAX_PILAR_EMENDA, Fraction(8, 100))    # 8% Ac

    def test_diametros_minimos(self) -> None:
        self.assertEqual(DIAMETRO_MINIMO_LONGITUDINAL_MM, Fraction(10, 1))
        self.assertEqual(DIAMETRO_MINIMO_ESTRIBO_MM, Fraction(5, 1))

    def test_tabela_caa(self) -> None:
        self.assertIn("CAA_I", TABELA_CAA_PILARES)
        self.assertIn("CAA_II", TABELA_CAA_PILARES)
        self.assertIn("CAA_III", TABELA_CAA_PILARES)
        self.assertIn("CAA_IV", TABELA_CAA_PILARES)
        self.assertEqual(TABELA_CAA_PILARES["CAA_II"]["cobrimento_nominal_cm"], Fraction(30, 10))

    def test_tabela_concretos(self) -> None:
        for fck in (20, 25, 30, 35, 40, 45, 50):
            self.assertIn(fck, TABELA_CONCRETOS_NBR6118)
            info = TABELA_CONCRETOS_NBR6118[fck]
            self.assertIsInstance(info["fcd_kN_cm2"], Fraction)
            self.assertGreater(info["fcd_kN_cm2"], 0)

    def test_tabela_bitolas_comerciais(self) -> None:
        self.assertIn("10.0", TABELA_BITOLAS_LONGITUDINAIS)
        self.assertIn("12.5", TABELA_BITOLAS_LONGITUDINAIS)
        self.assertIn("16.0", TABELA_BITOLAS_LONGITUDINAIS)
        self.assertIn("20.0", TABELA_BITOLAS_LONGITUDINAIS)
        self.assertIn("25.0", TABELA_BITOLAS_LONGITUDINAIS)
        self.assertIn("5.0", TABELA_BITOLAS_ESTRIBOS)
        self.assertIn("6.3", TABELA_BITOLAS_ESTRIBOS)


if __name__ == "__main__":
    unittest.main()
