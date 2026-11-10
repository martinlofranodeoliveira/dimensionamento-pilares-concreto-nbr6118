from __future__ import annotations

import unittest
from fractions import Fraction

from pilares_concreto_nbr6118.models import (
    GeometriaPilar,
    EsforcosPilar,
    PropriedadesMateriais,
    PreferenciasDetalhamento,
    ProjetoPilar,
)


class TestModels(unittest.TestCase):
    def test_geometria_pilar_valida(self) -> None:
        geo = GeometriaPilar(
            largura_b_cm=Fraction(20, 1),
            comprimento_h_cm=Fraction(40, 1),
            altura_livre_l_cm=Fraction(300, 1),
            coeficiente_flambagem_alpha=Fraction(1, 1),
        )
        self.assertEqual(geo.largura_b_cm, Fraction(20, 1))
        self.assertEqual(geo.comprimento_h_cm, Fraction(40, 1))
        self.assertEqual(geo.altura_livre_l_cm, Fraction(300, 1))

    def test_geometria_pilar_invalida(self) -> None:
        with self.assertRaises(ValueError):
            GeometriaPilar(
                largura_b_cm=Fraction(-10, 1),
                comprimento_h_cm=Fraction(40, 1),
                altura_livre_l_cm=Fraction(300, 1),
            )
        with self.assertRaises(ValueError):
            GeometriaPilar(
                largura_b_cm=Fraction(20, 1),
                comprimento_h_cm=Fraction(40, 1),
                altura_livre_l_cm=Fraction(0, 1),
            )
        with self.assertRaises(ValueError):
            GeometriaPilar(
                largura_b_cm=Fraction(20, 1),
                comprimento_h_cm=Fraction(40, 1),
                altura_livre_l_cm=Fraction(300, 1),
                coeficiente_flambagem_alpha=Fraction(-1, 1),
            )

    def test_esforcos_pilar_valido(self) -> None:
        esf = EsforcosPilar(
            forca_normal_nk_kn=Fraction(500, 1),
            momento_topo_mk_topo_knm=Fraction(15, 1),
            momento_base_mk_base_knm=Fraction(10, 1),
            eixo_flexao="h",
        )
        self.assertEqual(esf.forca_normal_nk_kn, Fraction(500, 1))
        self.assertEqual(esf.eixo_flexao, "h")

    def test_esforcos_pilar_invalido(self) -> None:
        with self.assertRaises(ValueError):
            EsforcosPilar(forca_normal_nk_kn=Fraction(0, 1))
        with self.assertRaises(ValueError):
            EsforcosPilar(
                forca_normal_nk_kn=Fraction(500, 1),
                eixo_flexao="z",
            )

    def test_materiais_validos_e_invalidos(self) -> None:
        mat = PropriedadesMateriais(classe_concreto_fck=30, tipo_aco="CA_50", classe_agressividade="CAA_III")
        self.assertEqual(mat.classe_concreto_fck, 30)

        with self.assertRaises(ValueError):
            PropriedadesMateriais(classe_concreto_fck=60)  # Fora do Grupo I
        with self.assertRaises(ValueError):
            PropriedadesMateriais(tipo_aco="CA_25")
        with self.assertRaises(ValueError):
            PropriedadesMateriais(classe_agressividade="CAA_V")
        with self.assertRaises(ValueError):
            PropriedadesMateriais(cobrimento_nominal_cm=Fraction(-1, 1))

    def test_preferencias_detalhamento(self) -> None:
        pref = PreferenciasDetalhamento(distribuicao_armadura="QUATRO_FACES")
        self.assertEqual(pref.distribuicao_armadura, "QUATRO_FACES")
        with self.assertRaises(ValueError):
            PreferenciasDetalhamento(distribuicao_armadura="INVALIDA")

    def test_projeto_completo(self) -> None:
        p = ProjetoPilar(
            geometria=GeometriaPilar(Fraction(20, 1), Fraction(40, 1), Fraction(300, 1)),
            esforcos=EsforcosPilar(Fraction(600, 1)),
            identificacao="Pilar P1",
        )
        self.assertEqual(p.identificacao, "Pilar P1")


    def test_cobrimento_nominal_customizado(self) -> None:
        mat = PropriedadesMateriais(cobrimento_nominal_cm=Fraction(45, 10))
        self.assertEqual(mat.cobrimento_nominal_cm, Fraction(45, 10))

    def test_esforcos_compressao_pura(self) -> None:
        esf = EsforcosPilar(forca_normal_nk_kn=Fraction(1000, 1))
        self.assertEqual(esf.momento_topo_mk_topo_knm, Fraction(0, 1))
        self.assertEqual(esf.momento_base_mk_base_knm, Fraction(0, 1))


if __name__ == "__main__":
    unittest.main()
