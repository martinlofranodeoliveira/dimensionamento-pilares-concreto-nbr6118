from __future__ import annotations

"""Pacote de dimensionamento analítico, verificação estrutural e detalhamento de pilares de concreto armado.

Norma regulamentadora: ABNT NBR 6118:2023.
Desenvolvido por LOFRANO TECNOLOGIA.
Aritmética 100% exata (Zero Float) com Frações e inteiros.
"""

__version__ = "1.0.0"
__author__ = "Martin Lofrano de Oliveira / LOFRANO TECNOLOGIA"
__license__ = "MIT"

from pilares_concreto_nbr6118.constants import (
    GAMMA_C,
    GAMMA_S,
    GAMMA_F,
    ES_KN_CM2,
    LARGURA_MINIMA_PILAR_CM,
    AREA_MINIMA_SECAO_CM2,
    ESBELTEZ_MAXIMA_ADMISSIVEL,
    TABELA_CAA_PILARES,
    TABELA_CONCRETOS_NBR6118,
    TABELA_ACOS_NBR6118,
    TABELA_BITOLAS_LONGITUDINAIS,
    TABELA_BITOLAS_ESTRIBOS,
)
from pilares_concreto_nbr6118.models import (
    GeometriaPilar,
    EsforcosPilar,
    PropriedadesMateriais,
    PreferenciasDetalhamento,
    ProjetoPilar,
    ResultadoEsbeltezPilar,
    ResultadoExcentricidadesPilar,
    ResultadoFlexoCompressaoPilar,
    ResultadoDetalhamentoPilar,
    ResultadoProjetoPilar,
)
from pilares_concreto_nbr6118.calculator import (
    dimensionar_pilar_concreto,
    calcular_esbeltez_pilar,
    calcular_excentricidades_pilar,
    dimensionar_flexo_compressao_pilar,
    detalhar_armaduras_pilar,
    raiz_quadrada_fracao,
)
from pilares_concreto_nbr6118.exporters import (
    exportar_csv,
    gerar_relatorio_memorial,
    formatar_fracao_decimal,
)
from pilares_concreto_nbr6118.svg_generator import gerar_painel_svg

__all__ = [
    "__version__",
    "GAMMA_C",
    "GAMMA_S",
    "GAMMA_F",
    "ES_KN_CM2",
    "LARGURA_MINIMA_PILAR_CM",
    "AREA_MINIMA_SECAO_CM2",
    "ESBELTEZ_MAXIMA_ADMISSIVEL",
    "TABELA_CAA_PILARES",
    "TABELA_CONCRETOS_NBR6118",
    "TABELA_ACOS_NBR6118",
    "TABELA_BITOLAS_LONGITUDINAIS",
    "TABELA_BITOLAS_ESTRIBOS",
    "GeometriaPilar",
    "EsforcosPilar",
    "PropriedadesMateriais",
    "PreferenciasDetalhamento",
    "ProjetoPilar",
    "ResultadoEsbeltezPilar",
    "ResultadoExcentricidadesPilar",
    "ResultadoFlexoCompressaoPilar",
    "ResultadoDetalhamentoPilar",
    "ResultadoProjetoPilar",
    "dimensionar_pilar_concreto",
    "calcular_esbeltez_pilar",
    "calcular_excentricidades_pilar",
    "dimensionar_flexo_compressao_pilar",
    "detalhar_armaduras_pilar",
    "raiz_quadrada_fracao",
    "exportar_csv",
    "gerar_relatorio_memorial",
    "formatar_fracao_decimal",
    "gerar_painel_svg",
]
