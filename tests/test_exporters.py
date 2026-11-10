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
from pilares_concreto_nbr6118.exporters import (
    formatar_fracao_decimal,
    sanitizar_campo_csv,
    gerar_relatorio_memorial,
    exportar_csv,
)


class TestExporters(unittest.TestCase):
    def test_formatar_fracao_decimal(self) -> None:
        self.assertEqual(formatar_fracao_decimal(Fraction(5, 1), 2), "5,00")
        self.assertEqual(formatar_fracao_decimal(Fraction(1, 2), 2), "0,50")
        self.assertEqual(formatar_fracao_decimal(Fraction(1, 4), 1), "0,3")  # 0.25 arredonda para 0.3
        self.assertEqual(formatar_fracao_decimal(Fraction(1, 3), 2), "0,33")
        self.assertEqual(formatar_fracao_decimal(Fraction(-7, 2), 1), "-3,5")
        self.assertEqual(formatar_fracao_decimal(Fraction(10, 1), 0), "10")

    def test_sanitizar_campo_csv(self) -> None:
        self.assertEqual(sanitizar_campo_csv("=1+1"), "'=1+1")
        self.assertEqual(sanitizar_campo_csv("+SUM(A1:A5)"), "'+SUM(A1:A5)")
        self.assertEqual(sanitizar_campo_csv("-100"), "'-100")
        self.assertEqual(sanitizar_campo_csv("@CMD"), "'@CMD")
        self.assertEqual(sanitizar_campo_csv("\tTAB"), "'\tTAB")
        self.assertEqual(sanitizar_campo_csv("Texto Seguro"), "Texto Seguro")

    def test_gerar_relatorio_memorial(self) -> None:
        p = ProjetoPilar(
            geometria=GeometriaPilar(Fraction(20, 1), Fraction(40, 1), Fraction(300, 1)),
            esforcos=EsforcosPilar(Fraction(650, 1), Fraction(20, 1), Fraction(15, 1)),
            materiais=PropriedadesMateriais(classe_concreto_fck=25),
            identificacao="Pilar P12 - Memorial",
        )
        res = dimensionar_pilar_concreto(p)
        relatorio = gerar_relatorio_memorial(res)

        self.assertIn("LOFRANO TECNOLOGIA", relatorio)
        self.assertIn("ABNT NBR 6118:2023", relatorio)
        self.assertIn("Pilar P12 - Memorial", relatorio)
        self.assertIn("1. CARACTERÍSTICAS GEOMÉTRICAS E MATERIAIS", relatorio)
        self.assertIn("2. ANÁLISE DE ESBELTEZ E EFEITOS DE 2ª ORDEM LOCAIS", relatorio)
        self.assertIn("3. DIMENSIONAMENTO À FLEXO-COMPRESSÃO NORMAL NO ELU", relatorio)
        self.assertIn("4. DETALHAMENTO DAS ARMADURAS NORMATIVAS", relatorio)
        self.assertIn("APROVADO", relatorio)

    def test_exportar_csv(self) -> None:
        p = ProjetoPilar(
            geometria=GeometriaPilar(Fraction(20, 1), Fraction(40, 1), Fraction(300, 1)),
            esforcos=EsforcosPilar(Fraction(600, 1)),
            identificacao="Pilar CSV",
        )
        res = dimensionar_pilar_concreto(p)
        csv_texto = exportar_csv(res)

        self.assertIn("PARAMETRO,VALOR,UNIDADE", csv_texto)
        self.assertIn("Identificacao,Pilar CSV,", csv_texto)
        self.assertIn('Largura b,"20,0",cm', csv_texto)
        self.assertIn('Comprimento h,"40,0",cm', csv_texto)


if __name__ == "__main__":
    unittest.main()
