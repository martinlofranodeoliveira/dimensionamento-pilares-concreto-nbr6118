from __future__ import annotations

import os
import tempfile
import unittest
from fractions import Fraction

from pilares_concreto_nbr6118.models import (
    GeometriaPilar,
    EsforcosPilar,
    PropriedadesMateriais,
    PreferenciasDetalhamento,
    ProjetoPilar,
)
from pilares_concreto_nbr6118.calculator import dimensionar_pilar_concreto
from pilares_concreto_nbr6118.codecs import (
    serializar_fracao,
    deserializar_fracao,
    serializar_projeto,
    deserializar_projeto,
    serializar_resultado,
    carregar_json_canonico,
    salvar_json_canonico,
    verificar_profundidade,
)


class TestCodecs(unittest.TestCase):
    def test_serializar_deserializar_fracao(self) -> None:
        f = Fraction(3, 4)
        d = serializar_fracao(f)
        self.assertEqual(d, {"num": 3, "den": 4})
        f2 = deserializar_fracao(d)
        self.assertEqual(f, f2)

    def test_deserializar_fracao_formatos_diversos(self) -> None:
        self.assertEqual(deserializar_fracao(5), Fraction(5, 1))
        self.assertEqual(deserializar_fracao("7/2"), Fraction(7, 2))
        self.assertEqual(deserializar_fracao("12"), Fraction(12, 1))
        self.assertEqual(deserializar_fracao(Fraction(1, 3)), Fraction(1, 3))

        with self.assertRaises(ValueError):
            deserializar_fracao(3.14)
        with self.assertRaises(ZeroDivisionError):
            deserializar_fracao({"num": 5, "den": 0})

    def test_rejeitar_float_no_json(self) -> None:
        json_com_float = '{"largura": 20.5}'
        with self.assertRaises(ValueError) as ctx:
            carregar_json_canonico(json_com_float)
        self.assertIn("Ponto flutuante proibido", str(ctx.exception))

    def test_rejeitar_bom_no_json(self) -> None:
        with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
            tmp.write(b"\xef\xbb\xbf{\"identificacao\": \"Pilar\"}")
            caminho = tmp.name

        try:
            with self.assertRaises(ValueError) as ctx:
                carregar_json_canonico(caminho)
            self.assertIn("Byte Order Mark (BOM)", str(ctx.exception))
        finally:
            if os.path.exists(caminho):
                os.unlink(caminho)

    def test_rejeitar_chaves_duplicadas(self) -> None:
        json_dup = '{"largura": 20, "largura": 25}'
        with self.assertRaises(ValueError) as ctx:
            carregar_json_canonico(json_dup)
        self.assertIn("Chave duplicada", str(ctx.exception))

    def test_profundidade_maxima(self) -> None:
        # Montar estrutura aninhada > 32
        d: dict = {"base": 1}
        for _ in range(35):
            d = {"next": d}
        with self.assertRaises(ValueError) as ctx:
            verificar_profundidade(d)
        self.assertIn("Profundidade de aninhamento excessiva", str(ctx.exception))

    def test_salvar_e_carregar_arquivo_canonico(self) -> None:
        p = ProjetoPilar(
            geometria=GeometriaPilar(Fraction(20, 1), Fraction(40, 1), Fraction(300, 1)),
            esforcos=EsforcosPilar(Fraction(600, 1)),
            identificacao="Pilar P12",
        )
        res = dimensionar_pilar_concreto(p)

        with tempfile.TemporaryDirectory() as tmpdir:
            arq_proj = os.path.join(tmpdir, "projeto.json")
            arq_res = os.path.join(tmpdir, "resultado.json")

            salvar_json_canonico(arq_proj, p)
            salvar_json_canonico(arq_res, res)

            dados_proj = carregar_json_canonico(arq_proj)
            p_reconst = deserializar_projeto(dados_proj)

            self.assertEqual(p.identificacao, p_reconst.identificacao)
            self.assertEqual(p.geometria.largura_b_cm, p_reconst.geometria.largura_b_cm)
            self.assertEqual(p.esforcos.forca_normal_nk_kn, p_reconst.esforcos.forca_normal_nk_kn)

            dados_res = carregar_json_canonico(arq_res)
            self.assertTrue(dados_res["atende_geral"])
            self.assertIn("esbeltez", dados_res)


if __name__ == "__main__":
    unittest.main()
