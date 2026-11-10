from __future__ import annotations

import unittest
from fractions import Fraction

from pilares_concreto_nbr6118.constants import (
    GAMMA_F,
    LARGURA_MINIMA_PILAR_CM,
    AREA_MINIMA_SECAO_CM2,
)
from pilares_concreto_nbr6118.models import (
    GeometriaPilar,
    EsforcosPilar,
    PropriedadesMateriais,
    PreferenciasDetalhamento,
    ProjetoPilar,
)
from pilares_concreto_nbr6118.calculator import (
    raiz_quadrada_fracao,
    calcular_coeficiente_gamman,
    calcular_esbeltez_pilar,
    calcular_excentricidades_pilar,
    dimensionar_flexo_compressao_pilar,
    detalhar_armaduras_pilar,
    dimensionar_pilar_concreto,
)


class TestCalculator(unittest.TestCase):
    def test_raiz_quadrada_fracao(self) -> None:
        self.assertEqual(raiz_quadrada_fracao(Fraction(0, 1)), Fraction(0, 1))
        self.assertEqual(raiz_quadrada_fracao(Fraction(4, 1)), Fraction(2, 1))
        self.assertEqual(raiz_quadrada_fracao(Fraction(9, 16)), Fraction(3, 4))
        r2 = raiz_quadrada_fracao(Fraction(2, 1))
        # r2^2 deve ser extremamente próximo de 2
        self.assertAlmostEqual(float(r2 ** 2), 2.0, places=5)
        with self.assertRaises(ValueError):
            raiz_quadrada_fracao(Fraction(-4, 1))

    def test_coeficiente_gamman(self) -> None:
        # Para b >= 19 cm: gamma_n = 1.00
        self.assertEqual(calcular_coeficiente_gamman(Fraction(20, 1)), Fraction(1, 1))
        self.assertEqual(calcular_coeficiente_gamman(Fraction(19, 1)), Fraction(1, 1))
        # Para b = 16 cm: gamma_n = 1.95 - 0.05 * 16 = 1.15
        self.assertEqual(calcular_coeficiente_gamman(Fraction(16, 1)), Fraction(115, 100))
        # Para b = 14 cm: gamma_n = 1.95 - 0.05 * 14 = 1.25
        self.assertEqual(calcular_coeficiente_gamman(Fraction(14, 1)), Fraction(125, 100))

    def test_esbeltez_pilar_biapoiado(self) -> None:
        geo = GeometriaPilar(
            largura_b_cm=Fraction(20, 1),
            comprimento_h_cm=Fraction(40, 1),
            altura_livre_l_cm=Fraction(300, 1),
        )
        esf = EsforcosPilar(forca_normal_nk_kn=Fraction(500, 1), eixo_flexao="h")
        res_esb = calcular_esbeltez_pilar(geo, esf)

        self.assertEqual(res_esb.comprimento_efetivo_le_cm, Fraction(300, 1))
        self.assertTrue(res_esb.atende_dimensoes_minimas)
        self.assertTrue(res_esb.e_esbeltez_admissivel)
        # lambda = 300 * sqrt(12) / 40 ~ 300 * 3.4641 / 40 = 25.98
        self.assertAlmostEqual(float(res_esb.indice_esbeltez_lambda), 25.98, places=1)

    def test_pilar_dimensao_insuficiente(self) -> None:
        geo = GeometriaPilar(
            largura_b_cm=Fraction(12, 1),  # menor que 14 cm
            comprimento_h_cm=Fraction(25, 1),  # Ac = 300 cm² < 360 cm²
            altura_livre_l_cm=Fraction(280, 1),
        )
        esf = EsforcosPilar(forca_normal_nk_kn=Fraction(300, 1))
        res_esb = calcular_esbeltez_pilar(geo, esf)
        self.assertFalse(res_esb.atende_dimensoes_minimas)

    def test_excentricidades_dispensa_segunda_ordem(self) -> None:
        geo = GeometriaPilar(Fraction(30, 1), Fraction(50, 1), Fraction(250, 1))
        esf = EsforcosPilar(
            forca_normal_nk_kn=Fraction(800, 1),
            momento_topo_mk_topo_knm=Fraction(10, 1),
            momento_base_mk_base_knm=Fraction(10, 1),
        )
        mat = PropriedadesMateriais(classe_concreto_fck=30)
        esb = calcular_esbeltez_pilar(geo, esf)
        exc, esb_ref = calcular_excentricidades_pilar(geo, esf, mat, esb)

        # Para pilar robusto e curto, lambda <= lambda1 => e2 = 0
        self.assertTrue(esb_ref.dispensa_segunda_ordem)
        self.assertEqual(exc.excentricidade_segunda_ordem_e2_cm, Fraction(0, 1))
        self.assertGreater(exc.excentricidade_acidental_ea_cm, Fraction(15, 10))

    def test_excentricidades_considera_segunda_ordem(self) -> None:
        # Pilar esbelto: b=15 cm, h=30 cm, l=450 cm => lambda elevado
        geo = GeometriaPilar(Fraction(15, 1), Fraction(30, 1), Fraction(450, 1))
        esf = EsforcosPilar(
            forca_normal_nk_kn=Fraction(400, 1),
            momento_topo_mk_topo_knm=Fraction(5, 1),
            momento_base_mk_base_knm=Fraction(0, 1),
        )
        mat = PropriedadesMateriais(classe_concreto_fck=25)
        esb = calcular_esbeltez_pilar(geo, esf)
        exc, esb_ref = calcular_excentricidades_pilar(geo, esf, mat, esb)

        self.assertFalse(esb_ref.dispensa_segunda_ordem)
        self.assertGreater(exc.excentricidade_segunda_ordem_e2_cm, Fraction(0, 1))
        self.assertGreater(exc.momento_calculo_total_msd_knm, Fraction(5, 1))

    def test_dimensionar_flexo_compressao(self) -> None:
        geo = GeometriaPilar(Fraction(20, 1), Fraction(40, 1), Fraction(300, 1))
        esf = EsforcosPilar(forca_normal_nk_kn=Fraction(600, 1))
        mat = PropriedadesMateriais(classe_concreto_fck=25)
        esb = calcular_esbeltez_pilar(geo, esf)
        exc, esb_ref = calcular_excentricidades_pilar(geo, esf, mat, esb)
        flx = dimensionar_flexo_compressao_pilar(geo, esf, mat, exc)

        self.assertGreater(flx.area_aco_adotada_cm2, 0)
        self.assertGreaterEqual(flx.area_aco_adotada_cm2, flx.area_aco_minima_cm2)
        self.assertLessEqual(flx.area_aco_adotada_cm2, flx.area_aco_maxima_cm2)

    def test_detalhar_armaduras(self) -> None:
        geo = GeometriaPilar(Fraction(20, 1), Fraction(40, 1), Fraction(300, 1))
        esf = EsforcosPilar(forca_normal_nk_kn=Fraction(600, 1))
        mat = PropriedadesMateriais(classe_concreto_fck=25)
        pref = PreferenciasDetalhamento()
        esb = calcular_esbeltez_pilar(geo, esf)
        exc, esb_ref = calcular_excentricidades_pilar(geo, esf, mat, esb)
        flx = dimensionar_flexo_compressao_pilar(geo, esf, mat, exc)
        det = detalhar_armaduras_pilar(geo, esf, mat, flx, pref)

        self.assertGreaterEqual(det.quantidade_barras, 4)
        self.assertGreaterEqual(det.bitola_longitudinal_mm, Fraction(10, 1))
        self.assertGreaterEqual(det.bitola_estribo_mm, Fraction(5, 1))
        self.assertLessEqual(det.espacamento_estribos_cm, Fraction(20, 1))
        self.assertGreaterEqual(det.area_aco_efetiva_cm2, flx.area_aco_adotada_cm2)

    def test_pilar_fita_com_gamma_n(self) -> None:
        # b = 16 cm, h = 60 cm => gamma_n = 1.95 - 0.05 * 16 = 1.15
        p = ProjetoPilar(
            geometria=GeometriaPilar(Fraction(16, 1), Fraction(60, 1), Fraction(320, 1)),
            esforcos=EsforcosPilar(Fraction(1100, 1), Fraction(35, 1), Fraction(20, 1)),
            materiais=PropriedadesMateriais(classe_concreto_fck=30, tipo_aco="CA_50", classe_agressividade="CAA_II"),
            identificacao="Pilar-Fita P04",
        )
        res = dimensionar_pilar_concreto(p)
        self.assertEqual(res.esbeltez.coeficiente_majoracao_gamman, Fraction(115, 100))
        self.assertTrue(res.atende_geral)

    def test_pilar_esbeltez_excessiva_reprovado(self) -> None:
        # Coluna extremamente esbelta: b=14 cm, h=14 cm, l=900 cm => lambda >> 200
        p = ProjetoPilar(
            geometria=GeometriaPilar(Fraction(14, 1), Fraction(14, 1), Fraction(900, 1)),
            esforcos=EsforcosPilar(Fraction(200, 1)),
            materiais=PropriedadesMateriais(classe_concreto_fck=20),
            identificacao="Pilar Esbeltez Excessiva",
        )
        res = dimensionar_pilar_concreto(p)
        self.assertFalse(res.conformidades["esbeltez_admissivel"])
        self.assertFalse(res.atende_geral)

    def test_pilar_carga_muito_elevada_armadura_minima_nsd(self) -> None:
        # Carga normal altíssima onde 0.15% Nsd/fyd supera 0.40% Ac
        p = ProjetoPilar(
            geometria=GeometriaPilar(Fraction(30, 1), Fraction(30, 1), Fraction(280, 1)),
            esforcos=EsforcosPilar(Fraction(2500, 1)),
            materiais=PropriedadesMateriais(classe_concreto_fck=40),
            identificacao="Pilar Alta Carga",
        )
        res = dimensionar_pilar_concreto(p)
        # As,min,1 = 0.0015 * Nsd / fyd
        as_min_nsd = Fraction(15, 10000) * (res.excentricidades.forca_normal_calculo_nsd_kn / (Fraction(50, 1) / Fraction(115, 100)))
        self.assertGreaterEqual(res.flexo_compressao.area_aco_minima_cm2, as_min_nsd)

    def test_pilar_momentos_sinais_opostos_alpha_b(self) -> None:
        # M_topo = +20, M_base = -15
        geo = GeometriaPilar(Fraction(20, 1), Fraction(40, 1), Fraction(300, 1))
        esf = EsforcosPilar(
            forca_normal_nk_kn=Fraction(500, 1),
            momento_topo_mk_topo_knm=Fraction(20, 1),
            momento_base_mk_base_knm=Fraction(-15, 1),
        )
        mat = PropriedadesMateriais(classe_concreto_fck=25)
        esb = calcular_esbeltez_pilar(geo, esf)
        exc, esb_ref = calcular_excentricidades_pilar(geo, esf, mat, esb)
        self.assertGreater(exc.excentricidade_total_etot_cm, 0)

    def test_pilar_bitola_sugerida_usuario(self) -> None:
        pref = PreferenciasDetalhamento(bitola_longitudinal_sugerida_mm=Fraction(16, 1))
        p = ProjetoPilar(
            geometria=GeometriaPilar(Fraction(20, 1), Fraction(40, 1), Fraction(300, 1)),
            esforcos=EsforcosPilar(Fraction(600, 1)),
            detalhamento=pref,
            identificacao="Pilar Bitola Sugerida 16mm",
        )
        res = dimensionar_pilar_concreto(p)
        self.assertEqual(res.detalhamento.bitola_longitudinal_mm, Fraction(16, 1))

    def test_concreto_alta_resistencia_c50(self) -> None:
        p = ProjetoPilar(
            geometria=GeometriaPilar(Fraction(25, 1), Fraction(50, 1), Fraction(300, 1)),
            esforcos=EsforcosPilar(Fraction(1500, 1)),
            materiais=PropriedadesMateriais(classe_concreto_fck=50),
            identificacao="Pilar C50",
        )
        res = dimensionar_pilar_concreto(p)
        self.assertTrue(res.atende_geral)
        self.assertEqual(res.materiais.classe_concreto_fck, 50)

    def test_flexao_em_torno_do_eixo_b(self) -> None:
        # Flexão no eixo menor (eixo b)
        p = ProjetoPilar(
            geometria=GeometriaPilar(Fraction(20, 1), Fraction(40, 1), Fraction(300, 1)),
            esforcos=EsforcosPilar(Fraction(600, 1), Fraction(15, 1), Fraction(10, 1), eixo_flexao="b"),
            identificacao="Pilar Flexao Eixo b",
        )
        res = dimensionar_pilar_concreto(p)
        self.assertTrue(res.atende_geral)


if __name__ == "__main__":
    unittest.main()
