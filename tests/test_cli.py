from __future__ import annotations

import os
import tempfile
import unittest
from fractions import Fraction

from pilares_concreto_nbr6118.cli import main, parse_fracao_cli


class TestCLI(unittest.TestCase):
    def test_parse_fracao_cli(self) -> None:
        self.assertEqual(parse_fracao_cli("20"), Fraction(20, 1))
        self.assertEqual(parse_fracao_cli("20.5"), Fraction(205, 10))
        self.assertEqual(parse_fracao_cli("20,5"), Fraction(205, 10))
        self.assertEqual(parse_fracao_cli("3/4"), Fraction(3, 4))
        self.assertEqual(parse_fracao_cli("-15"), Fraction(-15, 1))

    def test_cli_versao(self) -> None:
        codigo = main(["versao"])
        self.assertEqual(codigo, 0)

    def test_cli_tabelas(self) -> None:
        codigo = main(["tabelas"])
        self.assertEqual(codigo, 0)

    def test_cli_materiais(self) -> None:
        codigo = main(["materiais"])
        self.assertEqual(codigo, 0)

    def test_cli_sem_subcomando(self) -> None:
        codigo = main([])
        self.assertEqual(codigo, 0)

    def test_cli_dimensionar_arquivo_exemplo(self) -> None:
        codigo = main(["dimensionar", "-a", "examples/pilar_intermediario_esbeltez_moderada.json"])
        self.assertEqual(codigo, 0)

    def test_cli_dimensionar_argumentos_diretos(self) -> None:
        codigo = main([
            "dimensionar",
            "--b", "20",
            "--h", "40",
            "--l", "300",
            "--nk", "650",
            "--mk-topo", "20",
            "--mk-base", "15",
            "--fck", "25",
            "--caa", "CAA_II",
        ])
        self.assertEqual(codigo, 0)

    def test_cli_dimensionar_sem_carga(self) -> None:
        codigo = main(["dimensionar"])
        self.assertEqual(codigo, 1)

    def test_cli_dimensionar_gerar_todas_saidas(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            arq_txt = os.path.join(tmpdir, "memorial.txt")
            arq_json = os.path.join(tmpdir, "resultado.json")
            arq_csv = os.path.join(tmpdir, "planilha.csv")
            arq_svg = os.path.join(tmpdir, "painel.svg")

            codigo = main([
                "dimensionar",
                "-a", "examples/pilar_intermediario_esbeltez_moderada.json",
                "--relatorio", arq_txt,
                "--json-saida", arq_json,
                "--csv", arq_csv,
                "--svg", arq_svg,
            ])
            self.assertEqual(codigo, 0)
            self.assertTrue(os.path.exists(arq_txt))
            self.assertTrue(os.path.exists(arq_json))
            self.assertTrue(os.path.exists(arq_csv))
            self.assertTrue(os.path.exists(arq_svg))


if __name__ == "__main__":
    unittest.main()
