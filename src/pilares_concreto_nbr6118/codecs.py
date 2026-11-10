"""Serialização e desserialização canônica de projetos e resultados de pilares.

Regras estritas de segurança LOFRANO TECNOLOGIA:
  - Banimento total de ponto flutuante (Zero Float)
  - Rejeição de Byte Order Mark (BOM) UTF-8
  - Rejeição de chaves duplicadas no JSON
  - Limite máximo de profundidade de aninhamento (32 níveis)
  - Saída JSON canônica e determinística com chaves ordenadas e indentação fixa

Norma: ABNT NBR 6118:2023.
"""
from __future__ import annotations

import json
import os
from fractions import Fraction
from typing import Any, Dict, List, Tuple

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

PROFUNDIDADE_MAXIMA_PERMITIDA = 32


def _rejeitar_float(arg: str) -> None:
    raise ValueError(f"Ponto flutuante proibido pelo padrão Zero Float: '{arg}'. Utilize {{'num': N, 'den': D}} ou inteiros.")


def par_chaves_sem_duplicacao(pares: List[Tuple[str, Any]]) -> Dict[str, Any]:
    """Valida se existem chaves duplicadas em um objeto JSON."""
    resultado: Dict[str, Any] = {}
    for chave, valor in pares:
        if chave in resultado:
            raise ValueError(f"Chave duplicada detectada no JSON: '{chave}'.")
        resultado[chave] = valor
    return resultado


def verificar_profundidade(obj: Any, nivel_atual: int = 0) -> None:
    """Verifica se o aninhamento excede a profundidade máxima permitida."""
    if nivel_atual > PROFUNDIDADE_MAXIMA_PERMITIDA:
        raise ValueError(f"Profundidade de aninhamento excessiva ({nivel_atual} > {PROFUNDIDADE_MAXIMA_PERMITIDA}).")
    if isinstance(obj, dict):
        for v in obj.values():
            verificar_profundidade(v, nivel_atual + 1)
    elif isinstance(obj, list):
        for item in obj:
            verificar_profundidade(item, nivel_atual + 1)


def serializar_fracao(f: Fraction) -> Dict[str, int]:
    """Converte Fraction em representação canônica {'num': int, 'den': int}."""
    return {"num": f.numerator, "den": f.denominator}


def deserializar_fracao(d: Any) -> Fraction:
    """Converte representações aceitas em Fraction sem passar por float."""
    if isinstance(d, int):
        return Fraction(d, 1)
    if isinstance(d, Fraction):
        return d
    if isinstance(d, dict) and "num" in d and "den" in d:
        num = d["num"]
        den = d["den"]
        if not isinstance(num, int) or not isinstance(den, int):
            raise ValueError(f"Numerador e denominador devem ser inteiros: {d}")
        if den == 0:
            raise ZeroDivisionError("Denominador não pode ser zero.")
        return Fraction(num, den)
    if isinstance(d, str):
        if "/" in d:
            partes = d.split("/")
            if len(partes) == 2:
                return Fraction(int(partes[0].strip()), int(partes[1].strip()))
        return Fraction(int(d.strip()), 1)
    raise ValueError(f"Formato inválido para fração: {d} (tipo: {type(d).__name__})")


def serializar_projeto(p: ProjetoPilar) -> Dict[str, Any]:
    """Serializa ProjetoPilar para dicionário primitivo sem floats."""
    return {
        "identificacao": p.identificacao,
        "geometria": {
            "largura_b_cm": serializar_fracao(p.geometria.largura_b_cm),
            "comprimento_h_cm": serializar_fracao(p.geometria.comprimento_h_cm),
            "altura_livre_l_cm": serializar_fracao(p.geometria.altura_livre_l_cm),
            "coeficiente_flambagem_alpha": serializar_fracao(p.geometria.coeficiente_flambagem_alpha),
        },
        "esforcos": {
            "forca_normal_nk_kn": serializar_fracao(p.esforcos.forca_normal_nk_kn),
            "momento_topo_mk_topo_knm": serializar_fracao(p.esforcos.momento_topo_mk_topo_knm),
            "momento_base_mk_base_knm": serializar_fracao(p.esforcos.momento_base_mk_base_knm),
            "eixo_flexao": p.esforcos.eixo_flexao,
        },
        "materiais": {
            "classe_concreto_fck": p.materiais.classe_concreto_fck,
            "tipo_aco": p.materiais.tipo_aco,
            "classe_agressividade": p.materiais.classe_agressividade,
            "cobrimento_nominal_cm": serializar_fracao(p.materiais.cobrimento_nominal_cm) if p.materiais.cobrimento_nominal_cm is not None else None,
        },
        "detalhamento": {
            "bitola_longitudinal_sugerida_mm": serializar_fracao(p.detalhamento.bitola_longitudinal_sugerida_mm) if p.detalhamento.bitola_longitudinal_sugerida_mm is not None else None,
            "bitola_estribo_sugerida_mm": serializar_fracao(p.detalhamento.bitola_estribo_sugerida_mm) if p.detalhamento.bitola_estribo_sugerida_mm is not None else None,
            "distribuicao_armadura": p.detalhamento.distribuicao_armadura,
        },
    }


def deserializar_projeto(d: Dict[str, Any]) -> ProjetoPilar:
    """Reconstrói um ProjetoPilar a partir de dicionário decodificado."""
    geo_d = d["geometria"]
    geometria = GeometriaPilar(
        largura_b_cm=deserializar_fracao(geo_d["largura_b_cm"]),
        comprimento_h_cm=deserializar_fracao(geo_d["comprimento_h_cm"]),
        altura_livre_l_cm=deserializar_fracao(geo_d["altura_livre_l_cm"]),
        coeficiente_flambagem_alpha=deserializar_fracao(geo_d.get("coeficiente_flambagem_alpha", 1)),
    )

    esf_d = d["esforcos"]
    esforcos = EsforcosPilar(
        forca_normal_nk_kn=deserializar_fracao(esf_d["forca_normal_nk_kn"]),
        momento_topo_mk_topo_knm=deserializar_fracao(esf_d.get("momento_topo_mk_topo_knm", 0)),
        momento_base_mk_base_knm=deserializar_fracao(esf_d.get("momento_base_mk_base_knm", 0)),
        eixo_flexao=esf_d.get("eixo_flexao", "h"),
    )

    mat_d = d.get("materiais", {})
    cnom_raw = mat_d.get("cobrimento_nominal_cm")
    materiais = PropriedadesMateriais(
        classe_concreto_fck=int(mat_d.get("classe_concreto_fck", 25)),
        tipo_aco=str(mat_d.get("tipo_aco", "CA_50")),
        classe_agressividade=str(mat_d.get("classe_agressividade", "CAA_II")),
        cobrimento_nominal_cm=deserializar_fracao(cnom_raw) if cnom_raw is not None else None,
    )

    det_d = d.get("detalhamento", {})
    bit_l_raw = det_d.get("bitola_longitudinal_sugerida_mm")
    bit_t_raw = det_d.get("bitola_estribo_sugerida_mm")
    detalhamento = PreferenciasDetalhamento(
        bitola_longitudinal_sugerida_mm=deserializar_fracao(bit_l_raw) if bit_l_raw is not None else None,
        bitola_estribo_sugerida_mm=deserializar_fracao(bit_t_raw) if bit_t_raw is not None else None,
        distribuicao_armadura=str(det_d.get("distribuicao_armadura", "SIMETRICA_DUAS_FACES")),
    )

    return ProjetoPilar(
        geometria=geometria,
        esforcos=esforcos,
        materiais=materiais,
        detalhamento=detalhamento,
        identificacao=str(d.get("identificacao", "Pilar Sem Identificação")),
    )


def serializar_resultado(r: ResultadoProjetoPilar) -> Dict[str, Any]:
    """Serializa ResultadoProjetoPilar para dicionário determinístico sem floats."""
    return {
        "identificacao": r.identificacao,
        "atende_geral": r.atende_geral,
        "conformidades": r.conformidades,
        "avisos": r.avisos,
        "esbeltez": {
            "comprimento_efetivo_le_cm": serializar_fracao(r.esbeltez.comprimento_efetivo_le_cm),
            "raio_giracao_i_cm": serializar_fracao(r.esbeltez.raio_giracao_i_cm),
            "indice_esbeltez_lambda": serializar_fracao(r.esbeltez.indice_esbeltez_lambda),
            "coeficiente_majoracao_gamman": serializar_fracao(r.esbeltez.coeficiente_majoracao_gamman),
            "esbeltez_limite_lambda1": serializar_fracao(r.esbeltez.esbeltez_limite_lambda1),
            "dispensa_segunda_ordem": r.esbeltez.dispensa_segunda_ordem,
            "e_esbeltez_admissivel": r.esbeltez.e_esbeltez_admissivel,
            "atende_dimensoes_minimas": r.esbeltez.atende_dimensoes_minimas,
        },
        "excentricidades": {
            "forca_normal_calculo_nsd_kn": serializar_fracao(r.excentricidades.forca_normal_calculo_nsd_kn),
            "excentricidade_primeira_ordem_e1_cm": serializar_fracao(r.excentricidades.excentricidade_primeira_ordem_e1_cm),
            "excentricidade_acidental_ea_cm": serializar_fracao(r.excentricidades.excentricidade_acidental_ea_cm),
            "excentricidade_segunda_ordem_e2_cm": serializar_fracao(r.excentricidades.excentricidade_segunda_ordem_e2_cm),
            "excentricidade_total_etot_cm": serializar_fracao(r.excentricidades.excentricidade_total_etot_cm),
            "momento_calculo_total_msd_knm": serializar_fracao(r.excentricidades.momento_calculo_total_msd_knm),
            "curvatura_aproximada_1_r": serializar_fracao(r.excentricidades.curvatura_aproximada_1_r),
        },
        "flexo_compressao": {
            "area_concreto_ac_cm2": serializar_fracao(r.flexo_compressao.area_concreto_ac_cm2),
            "forca_adimensional_nu": serializar_fracao(r.flexo_compressao.forca_adimensional_nu),
            "momento_adimensional_mu": serializar_fracao(r.flexo_compressao.momento_adimensional_mu),
            "taxa_mecanica_omega": serializar_fracao(r.flexo_compressao.taxa_mecanica_omega),
            "area_aco_calculada_cm2": serializar_fracao(r.flexo_compressao.area_aco_calculada_cm2),
            "area_aco_minima_cm2": serializar_fracao(r.flexo_compressao.area_aco_minima_cm2),
            "area_aco_maxima_cm2": serializar_fracao(r.flexo_compressao.area_aco_maxima_cm2),
            "area_aco_adotada_cm2": serializar_fracao(r.flexo_compressao.area_aco_adotada_cm2),
            "taxa_armadura_geometrica_pct": serializar_fracao(r.flexo_compressao.taxa_armadura_geometrica_pct),
        },
        "detalhamento": {
            "bitola_longitudinal_mm": serializar_fracao(r.detalhamento.bitola_longitudinal_mm),
            "quantidade_barras": r.detalhamento.quantidade_barras,
            "area_aco_efetiva_cm2": serializar_fracao(r.detalhamento.area_aco_efetiva_cm2),
            "espacamento_livre_barras_cm": serializar_fracao(r.detalhamento.espacamento_livre_barras_cm),
            "bitola_estribo_mm": serializar_fracao(r.detalhamento.bitola_estribo_mm),
            "espacamento_estribos_cm": serializar_fracao(r.detalhamento.espacamento_estribos_cm),
            "cobrimento_adotado_cm": serializar_fracao(r.detalhamento.cobrimento_adotado_cm),
            "altura_util_d_cm": serializar_fracao(r.detalhamento.altura_util_d_cm),
        },
    }


def carregar_json_canonico(caminho_ou_conteudo: str) -> Dict[str, Any]:
    """Lê e valida arquivo ou string JSON sob as regras LOFRANO TECNOLOGIA."""
    if "\n" not in caminho_ou_conteudo and (caminho_ou_conteudo.endswith(".json") or len(caminho_ou_conteudo) < 256):
        if os.path.exists(caminho_ou_conteudo):
            with open(caminho_ou_conteudo, "rb") as f:
                bytes_conteudo = f.read()
                if bytes_conteudo.startswith(b"\xef\xbb\xbf"):
                    raise ValueError("Byte Order Mark (BOM) UTF-8 proibido. Utilize UTF-8 puro sem BOM.")
                texto = bytes_conteudo.decode("utf-8")
        else:
            texto = caminho_ou_conteudo
    else:
        texto = caminho_ou_conteudo

    if texto.startswith("\ufeff"):
        raise ValueError("Byte Order Mark (BOM) UTF-8 proibido. Utilize UTF-8 puro sem BOM.")

    dados = json.loads(
        texto,
        parse_float=_rejeitar_float,
        object_pairs_hook=par_chaves_sem_duplicacao,
    )
    verificar_profundidade(dados)
    return dados


def salvar_json_canonico(caminho: str, objeto_serializavel: Any) -> None:
    """Escreve JSON canônico com formatação padronizada e sem BOM."""
    if isinstance(objeto_serializavel, ProjetoPilar):
        dados = serializar_projeto(objeto_serializavel)
    elif isinstance(objeto_serializavel, ResultadoProjetoPilar):
        dados = serializar_resultado(objeto_serializavel)
    elif isinstance(objeto_serializavel, dict):
        dados = objeto_serializavel
    else:
        raise ValueError(f"Tipo não serializável diretamente: {type(objeto_serializavel).__name__}")

    verificar_profundidade(dados)
    texto = json.dumps(dados, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
