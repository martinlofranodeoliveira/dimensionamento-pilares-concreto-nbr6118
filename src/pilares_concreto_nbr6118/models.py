"""Modelos de dados (dataclasses) para o dimensionamento de pilares de concreto armado.

Operações fundamentadas em Frações exatas (Zero Float).
Norma: ABNT NBR 6118:2023.
LOFRANO TECNOLOGIA.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional

from pilares_concreto_nbr6118.constants import (
    LARGURA_MINIMA_PILAR_CM,
    AREA_MINIMA_SECAO_CM2,
    TABELA_CAA_PILARES,
    TABELA_CONCRETOS_NBR6118,
    TABELA_ACOS_NBR6118,
)


@dataclass(frozen=True)
class GeometriaPilar:
    """Geometria da seção transversal e comprimento de flambagem do pilar."""
    largura_b_cm: Fraction
    comprimento_h_cm: Fraction
    altura_livre_l_cm: Fraction
    coeficiente_flambagem_alpha: Fraction = Fraction(1, 1)

    def __post_init__(self) -> None:
        if self.largura_b_cm <= 0 or self.comprimento_h_cm <= 0 or self.altura_livre_l_cm <= 0:
            raise ValueError("As dimensões e comprimento do pilar devem ser estritamente positivos.")
        if self.coeficiente_flambagem_alpha <= 0:
            raise ValueError("O coeficiente de flambagem deve ser estritamente positivo.")


@dataclass(frozen=True)
class EsforcosPilar:
    """Esforços solicitantes característicos atuantes no pilar."""
    forca_normal_nk_kn: Fraction
    momento_topo_mk_topo_knm: Fraction = Fraction(0, 1)
    momento_base_mk_base_knm: Fraction = Fraction(0, 1)
    eixo_flexao: str = "h"  # Flexão em torno do eixo de menor inércia ("h") ou maior ("b")

    def __post_init__(self) -> None:
        if self.forca_normal_nk_kn <= 0:
            raise ValueError("A força normal característica Nk deve ser estritamente positiva (compressão).")
        if self.eixo_flexao not in ("h", "b"):
            raise ValueError("O eixo de flexão deve ser 'h' (em torno de h) ou 'b' (em torno de b).")


@dataclass(frozen=True)
class PropriedadesMateriais:
    """Propriedades dos materiais estruturais e ambiente."""
    classe_concreto_fck: int = 25
    tipo_aco: str = "CA_50"
    classe_agressividade: str = "CAA_II"
    cobrimento_nominal_cm: Optional[Fraction] = None

    def __post_init__(self) -> None:
        if self.classe_concreto_fck not in TABELA_CONCRETOS_NBR6118:
            raise ValueError(f"Classe de concreto C{self.classe_concreto_fck} não suportada. Concretos do Grupo I: 20 a 50 MPa.")
        if self.tipo_aco not in TABELA_ACOS_NBR6118:
            raise ValueError(f"Tipo de aço '{self.tipo_aco}' inválido. Utilize CA_50 ou CA_60.")
        if self.classe_agressividade not in TABELA_CAA_PILARES:
            raise ValueError(f"Classe de agressividade '{self.classe_agressividade}' inválida. Utilize CAA_I, CAA_II, CAA_III ou CAA_IV.")
        if self.cobrimento_nominal_cm is not None and self.cobrimento_nominal_cm <= 0:
            raise ValueError("O cobrimento nominal deve ser estritamente positivo.")


@dataclass(frozen=True)
class PreferenciasDetalhamento:
    """Preferências do projetista para o detalhamento das armaduras."""
    bitola_longitudinal_sugerida_mm: Optional[Fraction] = None
    bitola_estribo_sugerida_mm: Optional[Fraction] = None
    distribuicao_armadura: str = "SIMETRICA_DUAS_FACES"  # ou "QUATRO_FACES"

    def __post_init__(self) -> None:
        if self.distribuicao_armadura not in ("SIMETRICA_DUAS_FACES", "QUATRO_FACES"):
            raise ValueError("A distribuição de armadura deve ser 'SIMETRICA_DUAS_FACES' ou 'QUATRO_FACES'.")


@dataclass(frozen=True)
class ProjetoPilar:
    """Entrada completa para dimensionamento de pilar segundo a NBR 6118."""
    geometria: GeometriaPilar
    esforcos: EsforcosPilar
    materiais: PropriedadesMateriais = field(default_factory=PropriedadesMateriais)
    detalhamento: PreferenciasDetalhamento = field(default_factory=PreferenciasDetalhamento)
    identificacao: str = "Pilar Sem Identificação"


@dataclass(frozen=True)
class ResultadoEsbeltezPilar:
    """Resultados da análise geométrica e verificação de esbeltez."""
    comprimento_efetivo_le_cm: Fraction
    raio_giracao_i_cm: Fraction
    indice_esbeltez_lambda: Fraction
    coeficiente_majoracao_gamman: Fraction
    esbeltez_limite_lambda1: Fraction
    dispensa_segunda_ordem: bool
    e_esbeltez_admissivel: bool  # lambda <= 200
    atende_dimensoes_minimas: bool  # b >= 14 cm e Ac >= 360 cm²


@dataclass(frozen=True)
class ResultadoExcentricidadesPilar:
    """Resultados das excentricidades de 1ª ordem, acidental e 2ª ordem local."""
    forca_normal_calculo_nsd_kn: Fraction
    excentricidade_primeira_ordem_e1_cm: Fraction
    excentricidade_acidental_ea_cm: Fraction
    excentricidade_segunda_ordem_e2_cm: Fraction
    excentricidade_total_etot_cm: Fraction
    momento_calculo_total_msd_knm: Fraction
    curvatura_aproximada_1_r: Fraction


@dataclass(frozen=True)
class ResultadoFlexoCompressaoPilar:
    """Resultados do dimensionamento à flexo-compressão normal no ELU."""
    area_concreto_ac_cm2: Fraction
    forca_adimensional_nu: Fraction
    momento_adimensional_mu: Fraction
    taxa_mecanica_omega: Fraction
    area_aco_calculada_cm2: Fraction
    area_aco_minima_cm2: Fraction
    area_aco_maxima_cm2: Fraction
    area_aco_adotada_cm2: Fraction
    taxa_armadura_geometrica_pct: Fraction


@dataclass(frozen=True)
class ResultadoDetalhamentoPilar:
    """Resultados do arranjo e detalhamento das armaduras longitudinais e transversais."""
    bitola_longitudinal_mm: Fraction
    quantidade_barras: int
    area_aco_efetiva_cm2: Fraction
    espacamento_livre_barras_cm: Fraction
    bitola_estribo_mm: Fraction
    espacamento_estribos_cm: Fraction
    cobrimento_adotado_cm: Fraction
    altura_util_d_cm: Fraction


@dataclass(frozen=True)
class ResultadoProjetoPilar:
    """Consolidação integral do dimensionamento e verificações do pilar."""
    identificacao: str
    geometria: GeometriaPilar
    esforcos: EsforcosPilar
    materiais: PropriedadesMateriais
    esbeltez: ResultadoEsbeltezPilar
    excentricidades: ResultadoExcentricidadesPilar
    flexo_compressao: ResultadoFlexoCompressaoPilar
    detalhamento: ResultadoDetalhamentoPilar
    atende_geral: bool
    conformidades: Dict[str, bool]
    avisos: List[str] = field(default_factory=list)
