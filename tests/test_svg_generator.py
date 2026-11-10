from __future__ import annotations

import unittest
from fractions import Fraction

from pilares_concreto_nbr6118.models import (
    GeometriaPilar,
    EsforcosPilar,
    PropriedadesMateriais,
    ProjetoPilar,
)
from pilares_concreto_nbr6118.calculator import dimensionar_pilar_concreto
from pilares_concreto_nbr6118.svg_generator import gerar_painel_svg


class TestSvgGenerator(unittest.TestCase):
    def test_gerar_painel_svg(self) -> None:
        p = ProjetoPilar(
            geometria=GeometriaPilar(Fraction(20, 1), Fraction(40, 1), Fraction(300, 1)),
            esforcos=EsforcosPilar(Fraction(650, 1), Fraction(20, 1), Fraction(15, 1)),
            materiais=PropriedadesMateriais(classe_concreto_fck=25),
            identificacao="Pilar P12 - Teste SVG",
        )
        res = dimensionar_pilar_concreto(p)
        svg = gerar_painel_svg(res)

        self.assertTrue(svg.startswith("<svg"))
        self.assertIn('viewBox="0 0 1440 900"', svg)
        self.assertIn("LOFRANO TECNOLOGIA", svg)
        self.assertIn("ABNT NBR 6118:2023", svg)
        self.assertIn("Pilar P12 - Teste SVG", svg)
        self.assertIn("1. SEÇÃO TRANSVERSAL E ARMADURAS", svg)
        self.assertIn("2. ANÁLISE DE ESBELTEZ E 2ª ORDEM", svg)
        self.assertIn("3. SÍNTESE DO DIMENSIONAMENTO E ELU", svg)
        self.assertIn("<circle", svg)
        self.assertIn("</svg>", svg)


if __name__ == "__main__":
    unittest.main()
