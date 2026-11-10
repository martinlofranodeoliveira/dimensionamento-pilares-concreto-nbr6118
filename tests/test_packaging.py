from __future__ import annotations

import os
import unittest
from pathlib import Path


class TestPackaging(unittest.TestCase):
    def setUp(self) -> None:
        self.raiz = Path(__file__).resolve().parent.parent

    def test_py_typed_existe(self) -> None:
        marcador = self.raiz / "src" / "pilares_concreto_nbr6118" / "py.typed"
        self.assertTrue(marcador.exists(), "O marcador PEP 561 py.typed deve estar presente.")

    def test_license_existe(self) -> None:
        licenca = self.raiz / "LICENSE"
        self.assertTrue(licenca.exists(), "O arquivo LICENSE deve estar presente na raiz.")
        conteudo = licenca.read_text(encoding="utf-8")
        self.assertIn("MIT License", conteudo)
        self.assertIn("LOFRANO TECNOLOGIA", conteudo)

    def test_pyproject_valido(self) -> None:
        pyproject = self.raiz / "pyproject.toml"
        self.assertTrue(pyproject.exists(), "O arquivo pyproject.toml deve estar presente.")
        conteudo = pyproject.read_text(encoding="utf-8")
        self.assertIn("dimensionamento-pilares-concreto-nbr6118", conteudo)
        self.assertIn("pilares-concreto = \"pilares_concreto_nbr6118.cli:main\"", conteudo)

    def test_exemplos_existem(self) -> None:
        ex1 = self.raiz / "examples" / "pilar_intermediario_esbeltez_moderada.json"
        ex2 = self.raiz / "examples" / "pilar_canto_alta_carga_fita.json"
        self.assertTrue(ex1.exists())
        self.assertTrue(ex2.exists())


if __name__ == "__main__":
    unittest.main()
