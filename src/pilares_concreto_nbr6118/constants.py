"""Constantes e tabelas normativas para dimensionamento de pilares de concreto armado.

Normas regulamentadoras:
  - ABNT NBR 6118:2023: Projeto de estruturas de concreto - Procedimento.
LOFRANO TECNOLOGIA - Aritmética 100% exata (Zero Float) com Frações.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Dict, Any

# Coeficientes de ponderação das ações e resistências (NBR 6118 Tabela 11.1 e 12.1)
GAMMA_C: Fraction = Fraction(140, 100)  # 1.40
GAMMA_S: Fraction = Fraction(115, 100)  # 1.15
GAMMA_F: Fraction = Fraction(140, 100)  # 1.40

# Módulo de elasticidade do aço estrutural
ES_KN_CM2: Fraction = Fraction(21000, 1)  # 210.000 MPa = 21.000 kN/cm²

# Limites geométricos e normativos de pilares (NBR 6118 item 13.2.3 e 15.8)
LARGURA_MINIMA_PILAR_CM: Fraction = Fraction(14, 1)        # 14 cm
AREA_MINIMA_SECAO_CM2: Fraction = Fraction(360, 1)         # 360 cm²
ESBELTEZ_MAXIMA_ADMISSIVEL: Fraction = Fraction(200, 1)    # lambda <= 200
ESBELTEZ_LIMITE_METODO_PILAR_PADRAO: Fraction = Fraction(90, 1)  # lambda <= 90

# Armaduras mínimas e máximas de pilares (NBR 6118 item 17.3.5.3)
RHO_MIN_PILAR_AC: Fraction = Fraction(4, 1000)             # 0,40% Ac
RHO_MIN_PILAR_NSD: Fraction = Fraction(15, 10000)          # 0,15% Nsd/fyd
RHO_MAX_PILAR_EMENDA: Fraction = Fraction(8, 100)          # 8% Ac (com emenda)
RHO_MAX_PILAR_NORMAL: Fraction = Fraction(4, 100)          # 4% Ac (fora da emenda)

# Diâmetros e limites de detalhamento (NBR 6118 item 18.4)
DIAMETRO_MINIMO_LONGITUDINAL_MM: Fraction = Fraction(10, 1)     # 10 mm
NUMERO_MINIMO_BARRAS_RETANGULAR: int = 4
DIAMETRO_MINIMO_ESTRIBO_MM: Fraction = Fraction(5, 1)           # 5 mm
ESPACAMENTO_MAXIMO_ESTRIBOS_ABSOLUTO_CM: Fraction = Fraction(20, 1)  # 20 cm
ESPACAMENTO_MAXIMO_LONGITUDINAL_EIXOS_CM: Fraction = Fraction(40, 1) # 40 cm
ESPACAMENTO_LIVRE_MINIMO_LONGITUDINAL_CM: Fraction = Fraction(2, 1)  # 2 cm

# Classes de Agressividade Ambiental (CAA) e Cobrimentos Nominais (NBR 6118 Tabelas 6.1 e 7.2)
TABELA_CAA_PILARES: Dict[str, Dict[str, Any]] = {
    "CAA_I": {
        "agressividade": "Fraca (Rural / Submersa)",
        "cobrimento_nominal_cm": Fraction(25, 10),  # 2,5 cm = 25 mm
        "w_lim_mm": Fraction(4, 10),                # 0,40 mm
    },
    "CAA_II": {
        "agressividade": "Moderada (Urbana)",
        "cobrimento_nominal_cm": Fraction(30, 10),  # 3,0 cm = 30 mm
        "w_lim_mm": Fraction(3, 10),                # 0,30 mm
    },
    "CAA_III": {
        "agressividade": "Forte (Marinha / Industrial)",
        "cobrimento_nominal_cm": Fraction(40, 10),  # 4,0 cm = 40 mm
        "w_lim_mm": Fraction(2, 10),                # 0,20 mm
    },
    "CAA_IV": {
        "agressividade": "Muito Forte (Industrial Agressiva / Respingos de Maré)",
        "cobrimento_nominal_cm": Fraction(50, 10),  # 5,0 cm = 50 mm
        "w_lim_mm": Fraction(2, 10),                # 0,20 mm
    },
}

# Classes de Concreto Estrutural NBR 6118 (Grupo I: C20 a C50)
TABELA_CONCRETOS_NBR6118: Dict[int, Dict[str, Any]] = {
    20: {
        "fck_mpa": 20,
        "fcd_kN_cm2": Fraction(20, 1) / (Fraction(10, 1) * GAMMA_C),
        "fctm_mpa": Fraction(221, 100),  # 0,30 * 20^(2/3) ~ 2,21 MPa
        "alpha_c": Fraction(85, 100),
        "lambda_c": Fraction(80, 100),
    },
    25: {
        "fck_mpa": 25,
        "fcd_kN_cm2": Fraction(25, 1) / (Fraction(10, 1) * GAMMA_C),
        "fctm_mpa": Fraction(256, 100),  # 0,30 * 25^(2/3) ~ 2,56 MPa
        "alpha_c": Fraction(85, 100),
        "lambda_c": Fraction(80, 100),
    },
    30: {
        "fck_mpa": 30,
        "fcd_kN_cm2": Fraction(30, 1) / (Fraction(10, 1) * GAMMA_C),
        "fctm_mpa": Fraction(290, 100),  # 0,30 * 30^(2/3) ~ 2,90 MPa
        "alpha_c": Fraction(85, 100),
        "lambda_c": Fraction(80, 100),
    },
    35: {
        "fck_mpa": 35,
        "fcd_kN_cm2": Fraction(35, 1) / (Fraction(10, 1) * GAMMA_C),
        "fctm_mpa": Fraction(321, 100),  # 0,30 * 35^(2/3) ~ 3,21 MPa
        "alpha_c": Fraction(85, 100),
        "lambda_c": Fraction(80, 100),
    },
    40: {
        "fck_mpa": 40,
        "fcd_kN_cm2": Fraction(40, 1) / (Fraction(10, 1) * GAMMA_C),
        "fctm_mpa": Fraction(351, 100),  # 0,30 * 40^(2/3) ~ 3,51 MPa
        "alpha_c": Fraction(85, 100),
        "lambda_c": Fraction(80, 100),
    },
    45: {
        "fck_mpa": 45,
        "fcd_kN_cm2": Fraction(45, 1) / (Fraction(10, 1) * GAMMA_C),
        "fctm_mpa": Fraction(380, 100),  # 0,30 * 45^(2/3) ~ 3,80 MPa
        "alpha_c": Fraction(85, 100),
        "lambda_c": Fraction(80, 100),
    },
    50: {
        "fck_mpa": 50,
        "fcd_kN_cm2": Fraction(50, 1) / (Fraction(10, 1) * GAMMA_C),
        "fctm_mpa": Fraction(407, 100),  # 0,30 * 50^(2/3) ~ 4,07 MPa
        "alpha_c": Fraction(85, 100),
        "lambda_c": Fraction(80, 100),
    },
}

# Aços Estruturais Conforme NBR 6118 / NBR 7480
TABELA_ACOS_NBR6118: Dict[str, Dict[str, Any]] = {
    "CA_50": {
        "nome": "Aço CA-50 (Nervurado)",
        "fyk_mpa": 500,
        "fyk_kN_cm2": Fraction(50, 1),
        "fyd_kN_cm2": Fraction(50, 1) / GAMMA_S,  # 50 / 1.15 = 43.478... kN/cm²
    },
    "CA_60": {
        "nome": "Aço CA-60 (Nervurado)",
        "fyk_mpa": 600,
        "fyk_kN_cm2": Fraction(60, 1),
        "fyd_kN_cm2": Fraction(60, 1) / GAMMA_S,  # 60 / 1.15 = 52.174... kN/cm²
    },
}

# Bitolas Comerciais Padronizadas para Barras Longitudinais (NBR 7480)
# Área = pi * d^2 / 4 com pi aproximado por 314159 / 100000
PI_FRACAO: Fraction = Fraction(314159, 100000)

TABELA_BITOLAS_LONGITUDINAIS: Dict[str, Dict[str, Any]] = {
    "10.0": {
        "diametro_mm": Fraction(10, 1),
        "diametro_cm": Fraction(10, 10),
        "area_cm2": Fraction(785, 1000),    # ~0,785 cm²
    },
    "12.5": {
        "diametro_mm": Fraction(125, 10),
        "diametro_cm": Fraction(125, 100),
        "area_cm2": Fraction(1227, 1000),   # ~1,227 cm²
    },
    "16.0": {
        "diametro_mm": Fraction(16, 1),
        "diametro_cm": Fraction(16, 10),
        "area_cm2": Fraction(2011, 1000),   # ~2,011 cm²
    },
    "20.0": {
        "diametro_mm": Fraction(20, 1),
        "diametro_cm": Fraction(20, 10),
        "area_cm2": Fraction(3142, 1000),   # ~3,142 cm²
    },
    "25.0": {
        "diametro_mm": Fraction(25, 1),
        "diametro_cm": Fraction(25, 10),
        "area_cm2": Fraction(4909, 1000),   # ~4,909 cm²
    },
}

# Bitolas Comerciais para Estribos Transversais
TABELA_BITOLAS_ESTRIBOS: Dict[str, Dict[str, Any]] = {
    "5.0": {
        "diametro_mm": Fraction(5, 1),
        "diametro_cm": Fraction(5, 10),
        "area_cm2": Fraction(196, 1000),    # ~0,196 cm² (ramo simples)
    },
    "6.3": {
        "diametro_mm": Fraction(63, 10),
        "diametro_cm": Fraction(63, 100),
        "area_cm2": Fraction(312, 1000),    # ~0,312 cm²
    },
    "8.0": {
        "diametro_mm": Fraction(8, 1),
        "diametro_cm": Fraction(8, 10),
        "area_cm2": Fraction(503, 1000),    # ~0,503 cm²
    },
    "10.0": {
        "diametro_mm": Fraction(10, 1),
        "diametro_cm": Fraction(10, 10),
        "area_cm2": Fraction(785, 1000),    # ~0,785 cm²
    },
}
